from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    partner_uom_id = fields.Many2one(related="partner_id.uom_id", string="Unit", store=True, readonly=True)

    port_loading_id = fields.Many2one('port.loading', string="Port Loading")
    bank_account_id = fields.Many2one('account.journal', domain=[('type','=','bank')], string="Bank Name")

    estimate_delivery_days = fields.Integer(string="Estimate Delivery Days")
    estimated_delivery_date = fields.Date(string="Estimated Deliveries")

    @api.model
    def create(self,vals):
        active_id = self.env.context.get('active_id')
        active_model = self.env.context.get('active_model')
        self.env.context.get('active_id')
        if active_id and active_model=='sale.order':
            # sale
            sale = self.env['sale.order'].browse(active_id)
            if len(sale):
                vals.update({
                    'port_loading_id':sale.port_loading_id.id, 
                    'bank_account_id':sale.bank_account_id.id,
                    'estimate_delivery_days':sale.estimate_delivery_days,
                    'estimated_delivery_date':sale.estimated_delivery_date,
                    })
            
        return super(AccountInvoice, self).create(vals)

class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'


    item_size_l = fields.Float(string="Item Length", related=False, compute="_compute_itemsize", readonly=True)
    item_size_w = fields.Float(string="Item Width", related=False, compute="_compute_itemsize", readonly=True)
    item_size_h = fields.Float(string="Item Height", related=False, compute="_compute_itemsize", readonly=True)


    case_pack_size_l = fields.Float(string="Case Pack Length", related=False, compute="_compute_itemsize", readonly=True)
    case_pack_size_w = fields.Float(string="Case Pack Width", related=False, compute="_compute_itemsize", readonly=True)
    case_pack_size_h = fields.Float(string="Case Pack Height", related=False, compute="_compute_itemsize", readonly=True)


    

    qty_per_ctn = fields.Float(string="Qty/CTN", related=False, compute="_compute_itemsize", readonly=True)


    cbm_per_ctn = fields.Float(string="CBM/CTN", related=False, compute="_compute_itemsize", readonly=True)

    qty_cartoon = fields.Float(string="Qty Cartoon", related=False, compute="_compute_itemsize", readonly=True)

    total_cbm = fields.Float(string="Total CBM", related=False, compute="_compute_itemsize", readonly=True)

    buyer_remarks = fields.Text(string="Buyer Remarks")

    def _fetch_buyer_remarks_from_sale_line(self):
        self.ensure_one()
        if len(self.sale_line_ids)==1:
            self.buyer_remarks = self.sale_line_ids.buyer_remarks

    @api.model
    def create(self,vals):
        active_id = self.env.context.get('active_id')
        active_model = self.env.context.get('active_model')

        sup = super(AccountInvoiceLine, self).create(vals)

        sup._fetch_buyer_remarks_from_sale_line()
        return sup


    @api.depends('product_id','invoice_id.partner_id', 'quantity')
    def _compute_itemsize(self):
        for rec in self:
            case_pack_size_l = rec.product_id.size_unit_id._compute_quantity(qty=rec.product_id.case_pack_size_l, to_unit=rec.invoice_id.partner_uom_id)
            case_pack_size_w = rec.product_id.size_unit_id._compute_quantity(qty=rec.product_id.case_pack_size_w, to_unit=rec.invoice_id.partner_uom_id)
            case_pack_size_h = rec.product_id.size_unit_id._compute_quantity(qty=rec.product_id.case_pack_size_h, to_unit=rec.invoice_id.partner_uom_id)
            cbm_per_ctn = (case_pack_size_l*case_pack_size_w*case_pack_size_h)/rec.invoice_id.partner_uom_id.cbm_ctn_factor or 1
            qty_cartoon = rec.quantity/rec.product_id.qty_per_ctn if rec.product_id.qty_per_ctn > 0.0 else 0.0
            res = {
                'item_size_l':rec.product_id.size_unit_id._compute_quantity(qty=rec.product_id.item_size_l, to_unit=rec.invoice_id.partner_uom_id),
                'item_size_w':rec.product_id.size_unit_id._compute_quantity(qty=rec.product_id.item_size_w, to_unit=rec.invoice_id.partner_uom_id),
                'item_size_h':rec.product_id.size_unit_id._compute_quantity(qty=rec.product_id.item_size_h, to_unit=rec.invoice_id.partner_uom_id),
                'case_pack_size_l':case_pack_size_l,
                'case_pack_size_w':case_pack_size_w,
                'case_pack_size_h':case_pack_size_h,
                
                'qty_per_ctn':rec.product_id.qty_per_ctn,
                'cbm_per_ctn':cbm_per_ctn,
                'qty_cartoon':qty_cartoon,
                'total_cbm':cbm_per_ctn*qty_cartoon,
            }
            rec.update(res)
