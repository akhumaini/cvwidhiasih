import hashlib
import hmac
import json
import logging
import requests
from werkzeug import urls

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('midtrans', 'Midtrans')],
        ondelete={'midtrans': 'set default'}
    )
    
    midtrans_server_key = fields.Char(
        string='Server Key',
        help='Server Key from Midtrans Dashboard',
        groups='base.group_system'
    )
    
    midtrans_client_key = fields.Char(
        string='Client Key',
        help='Client Key from Midtrans Dashboard'
    )
    
    midtrans_merchant_id = fields.Char(
        string='Merchant ID',
        help='Merchant ID from Midtrans Dashboard'
    )

    def _get_supported_currencies(self):
        """ Override method to specify supported currencies """
        supported_currencies = super()._get_supported_currencies()
        if self.code == 'midtrans':
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in ['IDR', 'USD', 'SGD', 'MYR']
            )
        return supported_currencies

    def _get_default_payment_method_codes(self):
        """ Override method to specify default payment method codes """
        default_codes = super()._get_default_payment_method_codes()
        if self.code == 'midtrans':
            return const.DEFAULT_PAYMENT_METHODS_CODES
        return default_codes

    @api.model
    def _get_compatible_providers(self, *args, currency_id=None, **kwargs):
        """ Override method to filter compatible providers """
        providers = super()._get_compatible_providers(*args, currency_id=currency_id, **kwargs)
        
        currency = self.env['res.currency'].browse(currency_id) if currency_id else None
        if currency and currency.name not in ['IDR', 'USD', 'SGD', 'MYR']:
            providers = providers.filtered(lambda p: p.code != 'midtrans')
            
        return providers

    def _midtrans_get_api_url(self):
        """ Return the API URL according to the provider state """
        if self.state == 'enabled':
            return 'https://app.midtrans.com/snap/v1'
        else:
            return 'https://app.sandbox.midtrans.com/snap/v1'

    def _midtrans_make_request(self, endpoint, payload=None, method='POST'):
        """ Make request to Midtrans API """
        url = f"{self._midtrans_get_api_url()}/{endpoint}"
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Basic {self._midtrans_get_basic_auth()}'
        }
        
        try:
            if method == 'POST':
                response = requests.post(url, headers=headers, json=payload, timeout=60)
            else:
                response = requests.get(url, headers=headers, timeout=60)
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            _logger.error("Midtrans API request failed: %s", str(e))
            raise ValidationError(_("Payment communication error. Please try again."))

    def _midtrans_get_basic_auth(self):
        """ Get basic auth string for Midtrans API """
        import base64
        auth_string = f"{self.midtrans_server_key}:"
        return base64.b64encode(auth_string.encode()).decode()

    @api.constrains('state', 'midtrans_server_key', 'midtrans_client_key', 'midtrans_merchant_id')
    def _check_midtrans_configuration(self):
        """ Check Midtrans configuration when enabling the provider """
        for provider in self:
            if provider.code == 'midtrans' and provider.state == 'enabled':
                if not provider.midtrans_server_key:
                    raise ValidationError(_("Server Key is required for Midtrans"))
                if not provider.midtrans_client_key:
                    raise ValidationError(_("Client Key is required for Midtrans"))
                if not provider.midtrans_merchant_id:
                    raise ValidationError(_("Merchant ID is required for Midtrans"))


# Constants for payment methods
class PaymentProviderConstants:
    DEFAULT_PAYMENT_METHODS_CODES = [
        'credit_card',
        'bank_transfer',
        'e_wallet',
        'over_the_counter',
        'cardless_credit'
    ]

const = PaymentProviderConstants()