import json
import logging
import pprint

from odoo import http, _
from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class MidtransController(http.Controller):

    _notify_url = '/payment/midtrans/notify'
    _return_url = '/payment/midtrans/return'

    @http.route(_notify_url, type='http', auth='public', methods=['POST'], csrf=False)
    def midtrans_notify(self, **data):
        """ Process Midtrans notification/webhook """
        _logger.info("Midtrans notification received with data:\n%s", pprint.pformat(data))
        
        try:
            # Get notification data from request
            if request.httprequest.content_type == 'application/json':
                notification_data = json.loads(request.httprequest.data.decode('utf-8'))
            else:
                notification_data = data

            # Find the transaction
            tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
                'midtrans', notification_data
            )

            # Process the notification
            tx_sudo._process_notification_data(notification_data)
            
            # Return success response
            return "OK"
            
        except ValidationError as e:
            _logger.warning("Midtrans notification validation error: %s", str(e))
            return "FAIL"
        except Exception as e:
            _logger.error("Midtrans notification processing error: %s", str(e))
            return "FAIL"

    @http.route(_return_url, type='http', auth='public', methods=['GET', 'POST'])
    def midtrans_return(self, **data):
        """ Handle return from Midtrans payment page """
        _logger.info("Midtrans return received with data:\n%s", pprint.pformat(data))
        
        try:
            # Get order_id from data
            order_id = data.get('order_id')
            if not order_id:
                raise ValidationError(_("Missing order_id in return data"))

            # Find transaction by order_id
            tx_sudo = request.env['payment.transaction'].sudo().search([
                ('midtrans_order_id', '=', order_id)
            ], limit=1)
            
            if not tx_sudo:
                raise ValidationError(_("No transaction found for order_id: %s") % order_id)

            # Check transaction status via API
            self._check_transaction_status(tx_sudo)
            
            # Redirect to appropriate page based on transaction status
            if tx_sudo.state == 'done':
                return request.redirect('/payment/status')
            elif tx_sudo.state == 'pending':
                return request.redirect('/payment/status')
            else:
                return request.redirect('/payment/status?error=1')
                
        except Exception as e:
            _logger.error("Midtrans return processing error: %s", str(e))
            return request.redirect('/payment/status?error=1')

    def _check_transaction_status(self, tx_sudo):
        """ Check transaction status via Midtrans API """
        try:
            # Make API call to check status
            response = tx_sudo.provider_id._midtrans_make_request(
                f'transactions/{tx_sudo.midtrans_order_id}/status',
                method='GET'
            )
            
            # Process the response as notification data
            tx_sudo._process_notification_data(response)
            
        except Exception as e:
            _logger.warning("Failed to check Midtrans transaction status: %s", str(e))

    @http.route('/payment/midtrans/test', type='http', auth='public')
    def midtrans_test(self):
        """ Test endpoint for Midtrans integration """
        return "Midtrans integration is working!"