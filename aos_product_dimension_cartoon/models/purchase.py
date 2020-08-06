from odoo import api, fields, models, _
from odoo.exceptions import UserError

import xlsxwriter
import io

import logging
_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    partner_uom_id = fields.Many2one(related="partner_id.uom_id", string="Unit", store=True, readonly=True)
    errors = fields.Html(compute="_compute_errors")


    def _check_partner_uom_errors(self):
        for rec in self:
            if rec.partner_id.id and not rec.partner_uom_id.id:
                rec.errors = """          
                <div class="alert alert-danger" role="alert">
  <span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span>
  <span class="sr-only">Error:</span>
  Vendor Unit not Defined<br/>Please Set Vendor Unit!
</div>"""

    @api.depends('partner_uom_id')
    def _compute_errors(self):
        self._check_partner_uom_errors()


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
                'item_size_l':0.0,
                'item_size_w':0.0,
                'item_size_h':0.0,
            }
            if rec.order_id.partner_uom_id.id:
                res = {
                    'item_size_l':rec.product_id.size_unit_id._compute_quantity(qty=rec.product_id.item_size_l, to_unit=rec.order_id.partner_uom_id),
                    'item_size_w':rec.product_id.size_unit_id._compute_quantity(qty=rec.product_id.item_size_w, to_unit=rec.order_id.partner_uom_id),
                    'item_size_h':rec.product_id.size_unit_id._compute_quantity(qty=rec.product_id.item_size_h, to_unit=rec.order_id.partner_uom_id),
                }
            rec.update(res)