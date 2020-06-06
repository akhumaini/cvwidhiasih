from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import timedelta
import xlsxwriter
import io

import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_uom_id = fields.Many2one(related="partner_id.uom_id", string="Unit", store=True, readonly=True)
    estimate_delivery_days = fields.Integer(string="Estimate Delivery Days", default=90)
    estimated_delivery_date = fields.Date(string="Estimated Deliveries", compute="_compute_estimation_date")
    port_loading_id = fields.Many2one('port.loading', string="Port Loading")
    bank_account_id = fields.Many2one('account.journal', domain=[('type','=','bank')], string="Bank Name")

    def _compute_estimation_date(self):
        for rec in self:
            if rec.estimate_delivery_days:
                if rec.confirmation_date:
                    res = fields.Datetime.from_string(rec.confirmation_date) + timedelta(days=rec.estimate_delivery_days)
                else:
                    res = fields.Datetime.from_string(rec.date_order) + timedelta(days=rec.estimate_delivery_days)

                rec.estimated_delivery_date = res
                


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

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    buyer_remarks = fields.Text(string="Buyer Remarks")
    item_size_l = fields.Float(string="Item Length", related=False, compute="_compute_itemsize", readonly=True)
    item_size_w = fields.Float(string="Item Width", related=False, compute="_compute_itemsize", readonly=True)
    item_size_h = fields.Float(string="Item Height", related=False, compute="_compute_itemsize", readonly=True)


    case_pack_size_l = fields.Float(string="Case Pack Length", related=False, compute="_compute_itemsize", readonly=True)
    case_pack_size_w = fields.Float(string="Case Pack Width", related=False, compute="_compute_itemsize", readonly=True)
    case_pack_size_h = fields.Float(string="Case Pack Height", related=False, compute="_compute_itemsize", readonly=True)


    

    qty_per_ctn = fields.Float(string="Qty / CTN", related=False, compute="_compute_itemsize", readonly=True)


    cbm_per_ctn = fields.Float(string="CBM / CTN", related=False, compute="_compute_itemsize", readonly=True)

    qty_cartoon = fields.Float(string="Qty Cartoon", related=False, compute="_compute_itemsize", readonly=True)

    total_cbm = fields.Float(string="Total CBM", related=False, compute="_compute_itemsize", readonly=True)


    



    @api.depends('product_id','order_id.partner_id', 'product_uom_qty')
    def _compute_itemsize(self):
        for rec in self:
            case_pack_size_l = rec.product_id.size_unit_id._compute_quantity(qty=rec.product_id.case_pack_size_l, to_unit=rec.order_id.partner_uom_id)
            case_pack_size_w = rec.product_id.size_unit_id._compute_quantity(qty=rec.product_id.case_pack_size_w, to_unit=rec.order_id.partner_uom_id)
            case_pack_size_h = rec.product_id.size_unit_id._compute_quantity(qty=rec.product_id.case_pack_size_h, to_unit=rec.order_id.partner_uom_id)
            cbm_per_ctn = (case_pack_size_l*case_pack_size_w*case_pack_size_h)/rec.order_id.partner_uom_id.cbm_ctn_factor or 1
            qty_cartoon = rec.product_uom_qty/rec.product_id.qty_per_ctn if rec.product_id.qty_per_ctn > 0.0 else 0.0
            res = {
                'item_size_l':rec.product_id.size_unit_id._compute_quantity(qty=rec.product_id.item_size_l, to_unit=rec.order_id.partner_uom_id),
                'item_size_w':rec.product_id.size_unit_id._compute_quantity(qty=rec.product_id.item_size_w, to_unit=rec.order_id.partner_uom_id),
                'item_size_h':rec.product_id.size_unit_id._compute_quantity(qty=rec.product_id.item_size_h, to_unit=rec.order_id.partner_uom_id),
                'case_pack_size_l':case_pack_size_l,
                'case_pack_size_w':case_pack_size_w,
                'case_pack_size_h':case_pack_size_h,
                'qty_per_ctn':rec.product_id.qty_per_ctn,
                'cbm_per_ctn':cbm_per_ctn,
                'qty_cartoon':qty_cartoon,
                'total_cbm':cbm_per_ctn*qty_cartoon,
            }
            rec.update(res)