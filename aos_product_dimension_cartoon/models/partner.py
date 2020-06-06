from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    allowed_category_ids = fields.Many2many('product.uom.categ', compute="_compute_allowed_category_id")
    uom_id = fields.Many2one('product.uom', string="Unit")

    def _compute_allowed_category_id(self):
        categories = self.env.ref('product.uom_categ_length')
        for rec in self:
            rec.allowed_category_ids = categories.ids