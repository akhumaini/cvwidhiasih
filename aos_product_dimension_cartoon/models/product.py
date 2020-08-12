from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class ProductUom(models.Model):
    _inherit = 'product.uom'

    cbm_ctn_factor = fields.Float('CBM CTN Factor (from cm)')

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    item_size_l = fields.Float(string="Item Length", inverse=lambda self:self._inverse_size())
    item_size_w = fields.Float(string="Item Width", inverse=lambda self:self._inverse_size())
    item_size_h = fields.Float(string="Item Height", inverse=lambda self:self._inverse_size())


    case_pack_size_l = fields.Float(string="Case Pack Length", inverse=lambda self:self._inverse_size())
    case_pack_size_w = fields.Float(string="Case Pack Width", inverse=lambda self:self._inverse_size())
    case_pack_size_h = fields.Float(string="Case Pack Height", inverse=lambda self:self._inverse_size())

    qty_per_ctn = fields.Float(string="Qty/CTN", inverse=lambda self:self._inverse_size())


    size_unit_id = fields.Many2one('product.uom', string="Size Unit", default=lambda self:self.env.ref('product.product_uom_cm').id, required=True)


    def _inverse_size(self):
        for rec in self:
            for var in rec.product_variant_ids:
                var.update({
                    'item_size_l':rec.item_size_l,
                    'item_size_h':rec.item_size_h,
                    'item_size_w':rec.item_size_w,

                    'case_pack_size_l':rec.case_pack_size_l,
                    'case_pack_size_h':rec.case_pack_size_h,
                    'case_pack_size_w':rec.case_pack_size_w,

                    'qty_per_ctn':rec.qty_per_ctn,

                })


class ProductProduct(models.Model):
    _inherit = 'product.product'

    item_size_l = fields.Float(string="Item Length", store=True)
    item_size_w = fields.Float(string="Item Width", store=True)
    item_size_h = fields.Float(string="Item Height", store=True)


    case_pack_size_l = fields.Float(string="Case Pack Length", store=True)
    case_pack_size_w = fields.Float(string="Case Pack Width", store=True)
    case_pack_size_h = fields.Float(string="Case Pack Height", store=True)

    qty_per_ctn = fields.Float(string="Qty/CTN", store=True)

    size_unit_id = fields.Many2one('product.uom', string="Size Unit", related="product_tmpl_id.size_unit_id", readonly=True)
    
    # @api.depends('product_tmpl_id.item_size_h','product_tmpl_id.item_size_w','product_tmpl_id.item_size_l','product_tmpl_id.case_pack_size_h','product_tmpl_id.case_pack_size_w','product_tmpl_id.case_pack_size_l','product_tmpl_id.qty_per_ctn')
    # def _compute_inventory(self):
    #     for rec in self:
    #         rec.item_size_h = rec.product_tmpl_id.item_size_h
    #         rec.item_size_w = rec.product_tmpl_id.item_size_w
    #         rec.item_size_l = rec.product_tmpl_id.item_size_l
    #         rec.case_pack_size_h = rec.product_tmpl_id.case_pack_size_h
    #         rec.case_pack_size_w = rec.product_tmpl_id.case_pack_size_w
    #         rec.case_pack_size_l = rec.product_tmpl_id.case_pack_size_l
    #         rec.qty_per_ctn = rec.product_tmpl_id.qty_per_ctn

    def _inverse_inventory(self):
        return True