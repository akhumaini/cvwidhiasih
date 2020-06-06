from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class PortLoading(models.Model):
    _name = 'port.loading'
    _description = 'Port Loading'

    name = fields.Char('Name', required=True)
    active = fields.Boolean(default=True, string="Active")