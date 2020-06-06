from odoo import api, fields, models, _
from odoo.exceptions import UserError

import xlsxwriter
import io

import logging
_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    partner_uom_id = fields.Many2one(related="partner_id.uom_id", string="Unit", store=True, readonly=True)


    def print_xls_report(self):
        self.ensure_one()

        # workbook = xlsxwriter.Workbook('%s.xlsx' % self.display_name.replace('/','_'))
        # worksheet = workbook.add_worksheet()
        # output = io.BytesIO()

        # workbook.close()
        # output.seek(0)
        # response.stream.write(output.read())
        # output.close()

        data = self.read()[0]
        _logger.critical(data)
        return {'type': 'ir.actions.report.xlsx',
                'report_name': 'aos_product_dimension_cartoon.sale_report_xlsx',
                'datas': data
                }

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    item_size_l = fields.Float(string="Item Length", related=False, compute="_compute_itemsize", readonly=True)
    item_size_w = fields.Float(string="Item Width", related=False, compute="_compute_itemsize", readonly=True)
    item_size_h = fields.Float(string="Item Height", related=False, compute="_compute_itemsize", readonly=True)
    

    @api.depends('product_id','order_id.partner_id', 'product_qty')
    def _compute_itemsize(self):
        for rec in self:
            res = {
                'item_size_l':rec.product_id.size_unit_id._compute_quantity(qty=rec.product_id.item_size_l, to_unit=rec.order_id.partner_uom_id),
                'item_size_w':rec.product_id.size_unit_id._compute_quantity(qty=rec.product_id.item_size_w, to_unit=rec.order_id.partner_uom_id),
                'item_size_h':rec.product_id.size_unit_id._compute_quantity(qty=rec.product_id.item_size_h, to_unit=rec.order_id.partner_uom_id),
            }
            rec.update(res)