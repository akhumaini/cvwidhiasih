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

    item_size_l = fields.Float(string="Item Length", related=False, readonly=False, compute="_compute_inventory", inverse=lambda self:self._inverse_inventory(), store=True)
    item_size_w = fields.Float(string="Item Width", related=False, readonly=False, compute="_compute_inventory", inverse=lambda self:self._inverse_inventory(), store=True)
    item_size_h = fields.Float(string="Item Height", related=False, readonly=False, compute="_compute_inventory", inverse=lambda self:self._inverse_inventory(), store=True)


    case_pack_size_l = fields.Float(string="Case Pack Length", related=False, readonly=False, compute="_compute_inventory", inverse=lambda self:self._inverse_inventory(), store=True)
    case_pack_size_w = fields.Float(string="Case Pack Width", related=False, readonly=False, compute="_compute_inventory", inverse=lambda self:self._inverse_inventory(), store=True)
    case_pack_size_h = fields.Float(string="Case Pack Height", related=False, readonly=False, compute="_compute_inventory", inverse=lambda self:self._inverse_inventory(), store=True)

    qty_per_ctn = fields.Float(string="Qty/CTN", related=False, readonly=False, compute="_compute_inventory", inverse=lambda self:self._inverse_inventory(), store=True)

    size_unit_id = fields.Many2one('product.uom', string="Size Unit", related="product_tmpl_id.size_unit_id", readonly=True)
    

    def _compute_inventory(self):
        for rec in self:
            rec.item_size_h = rec.product_tmpl_id.item_size_h
            rec.item_size_w = rec.product_tmpl_id.item_size_w
            rec.item_size_l = rec.product_tmpl_id.item_size_l
            rec.case_pack_size_h = rec.product_tmpl_id.case_pack_size_h
            rec.case_pack_size_w = rec.product_tmpl_id.case_pack_size_w
            rec.case_pack_size_l = rec.product_tmpl_id.case_pack_size_l
            rec.qty_per_ctn = rec.product_tmpl_id.qty_per_ctn

    def _inverse_inventory(self):
        return True