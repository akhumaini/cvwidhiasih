from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class ProductUom(models.Model):
    _inherit = 'product.uom'

    cbm_ctn_factor = fields.Float('CBM CTN Factor (from cm)')

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    item_size_l = fields.Float(string="Item Length")
    item_size_w = fields.Float(string="Item Width")
    item_size_h = fields.Float(string="Item Height")


    case_pack_size_l = fields.Float(string="Case Pack Length")
    case_pack_size_w = fields.Float(string="Case Pack Width")
    case_pack_size_h = fields.Float(string="Case Pack Height")

    qty_per_ctn = fields.Float(string="Qty/CTN")


    size_unit_id = fields.Many2one('product.uom', string="Size Unit", default=lambda self:self.env.ref('product.product_uom_cm').id, required=True)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    item_size_l = fields.Float(string="Item Length", related="product_tmpl_id.item_size_l", readonly=True)
    item_size_w = fields.Float(string="Item Width", related="product_tmpl_id.item_size_w", readonly=True)
    item_size_h = fields.Float(string="Item Height", related="product_tmpl_id.item_size_h", readonly=True)


    case_pack_size_l = fields.Float(string="Case Pack Length", related="product_tmpl_id.case_pack_size_l", readonly=True)
    case_pack_size_w = fields.Float(string="Case Pack Width", related="product_tmpl_id.case_pack_size_w", readonly=True)
    case_pack_size_h = fields.Float(string="Case Pack Height", related="product_tmpl_id.case_pack_size_h", readonly=True)


    

    qty_per_ctn = fields.Float(string="Qty/CTN", related="product_tmpl_id.qty_per_ctn", readonly=True)

    size_unit_id = fields.Many2one('product.uom', string="Size Unit", related="product_tmpl_id.size_unit_id", readonly=True)
    

