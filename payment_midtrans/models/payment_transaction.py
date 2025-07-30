import hashlib
import hmac
import json
import logging
from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    midtrans_order_id = fields.Char(string='Midtrans Order ID')
    midtrans_transaction_id = fields.Char(string='Midtrans Transaction ID')
    midtrans_snap_token = fields.Char(string='Snap Token')
    midtrans_snap_redirect_url = fields.Char(string='Snap Redirect URL')

    def _get_specific_rendering_values(self, processing_values):
        """ Override method to add Midtrans-specific rendering values """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'midtrans':
            return res

        # Create Snap transaction
        snap_data = self._midtrans_create_snap_transaction()
        
        rendering_values = {
            'snap_token': snap_data.get('token'),
            'snap_redirect_url': snap_data.get('redirect_url'),
            'client_key': self.provider_id.midtrans_client_key,
            'api_url': self._get_midtrans_snap_js_url(),
        }
        
        # Store snap token for later use
        self.midtrans_snap_token = snap_data.get('token')
        self.midtrans_snap_redirect_url = snap_data.get('redirect_url')
        
        return rendering_values

    def _midtrans_create_snap_transaction(self):
        """ Create Snap transaction with Midtrans """
        order_id = f"{self.reference}_{self.id}"
        self.midtrans_order_id = order_id
        
        # Prepare transaction details
        transaction_details = {
            'order_id': order_id,
            'gross_amount': int(self.amount)
        }
        
        # Prepare customer details
        customer_details = {}
        if self.partner_id:
            customer_details = {
                'first_name': self.partner_id.name or '',
                'email': self.partner_id.email or '',
                'phone': self.partner_id.phone or self.partner_id.mobile or '',
            }
            
            # Add billing address if available
            if self.partner_id.street:
                customer_details['billing_address'] = {
                    'first_name': self.partner_id.name or '',
                    'address': self.partner_id.street or '',
                    'city': self.partner_id.city or '',
                    'postal_code': self.partner_id.zip or '',
                    'country_code': self.partner_id.country_id.code or 'ID',
                }

        # Prepare item details
        item_details = []
        if hasattr(self, 'sale_order_ids') and self.sale_order_ids:
            for order in self.sale_order_ids:
                for line in order.order_line:
                    item_details.append({
                        'id': str(line.product_id.id),
                        'price': int(line.price_unit),
                        'quantity': int(line.product_uom_qty),
                        'name': line.product_id.name[:50],  # Midtrans limit
                    })
        else:
            # Fallback item
            item_details.append({
                'id': '1',
                'price': int(self.amount),
                'quantity': 1,
                'name': f'Payment {self.reference}',
            })

        # Prepare callback URLs
        base_url = self.provider_id.get_base_url()
        callbacks = {
            'finish': f"{base_url}/payment/midtrans/return",
            'error': f"{base_url}/payment/midtrans/return",
            'unfinish': f"{base_url}/payment/midtrans/return",
        }

        # Complete payload
        payload = {
            'transaction_details': transaction_details,
            'customer_details': customer_details,
            'item_details': item_details,
            'callbacks': callbacks,
            'expiry': {
                'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S +0700'),
                'unit': 'minutes',
                'duration': 60
            }
        }

        # Make API call to create Snap transaction
        try:
            response = self.provider_id._midtrans_make_request('transactions', payload)
            return response
        except Exception as e:
            _logger.error("Failed to create Midtrans Snap transaction: %s", str(e))
            raise ValidationError(_("Failed to create payment transaction. Please try again."))

    def _get_midtrans_snap_js_url(self):
        """ Get Snap.js URL based on environment """
        if self.provider_id.state == 'enabled':
            return 'https://app.midtrans.com/snap/snap.js'
        else:
            return 'https://app.sandbox.midtrans.com/snap/snap.js'

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """ Override method to find transaction from notification data """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'midtrans' or len(tx) == 1:
            return tx

        # Find transaction by Midtrans order ID
        order_id = notification_data.get('order_id')
        if order_id:
            tx = self.search([('midtrans_order_id', '=', order_id)])

        if not tx:
            raise ValidationError(_("Midtrans: No transaction found matching order ID: %s", order_id))

        return tx

    def _process_notification_data(self, notification_data):
        """ Override method to process Midtrans notification data """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'midtrans':
            return

        # Verify signature
        if not self._midtrans_verify_signature(notification_data):
            _logger.warning("Midtrans: Invalid signature for transaction %s", self.reference)
            return

        # Update transaction data
        self.midtrans_transaction_id = notification_data.get('transaction_id')
        
        # Update transaction status
        transaction_status = notification_data.get('transaction_status')
        fraud_status = notification_data.get('fraud_status', 'accept')
        
        if transaction_status == 'capture':
            if fraud_status == 'accept':
                self._set_done()
            elif fraud_status == 'challenge':
                self._set_pending()
        elif transaction_status == 'settlement':
            self._set_done()
        elif transaction_status in ['cancel', 'deny', 'expire']:
            self._set_canceled()
        elif transaction_status == 'pending':
            self._set_pending()
        else:
            _logger.warning("Midtrans: Unknown transaction status %s for transaction %s", 
                          transaction_status, self.reference)

    def _midtrans_verify_signature(self, notification_data):
        """ Verify Midtrans signature """
        order_id = notification_data.get('order_id', '')
        status_code = notification_data.get('status_code', '')
        gross_amount = notification_data.get('gross_amount', '')
        server_key = self.provider_id.midtrans_server_key
        
        # Create signature string
        signature_string = f"{order_id}{status_code}{gross_amount}{server_key}"
        
        # Calculate signature hash
        signature_hash = hashlib.sha512(signature_string.encode()).hexdigest()
        
        # Compare with received signature
        received_signature = notification_data.get('signature_key', '')
        
        return signature_hash == received_signature