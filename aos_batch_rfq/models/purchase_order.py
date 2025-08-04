# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    batch_rfq_id = fields.Many2one(
        'batch.rfq',
        string='Batch RFQ',
        readonly=True,
        help='Batch RFQ that generated this purchase order'
    )
    
    is_batch_rfq = fields.Boolean(
        string='Is Batch RFQ',
        compute='_compute_is_batch_rfq',
        store=True
    )
    
    @api.depends('batch_rfq_id')
    def _compute_is_batch_rfq(self):
        for order in self:
            order.is_batch_rfq = bool(order.batch_rfq_id)
    
    def action_view_batch_rfq(self):
        """View the related batch RFQ"""
        self.ensure_one()
        
        if not self.batch_rfq_id:
            return
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Batch RFQ'),
            'res_model': 'batch.rfq',
            'res_id': self.batch_rfq_id.id,
            'view_mode': 'form',
            'target': 'current'
        }
    
    def write(self, vals):
        """Override to update batch RFQ line status when PO state changes"""
        result = super(PurchaseOrder, self).write(vals)
        
        if 'state' in vals:
            # Update related batch RFQ line states
            for order in self:
                if order.batch_rfq_id:
                    batch_lines = order.batch_rfq_id.batch_rfq_line_ids.filtered(
                        lambda l: l.purchase_order_id.id == order.id
                    )
                    
                    if vals['state'] == 'sent':
                        batch_lines.write({'state': 'sent'})
                    elif vals['state'] in ['to approve', 'purchase', 'done']:
                        batch_lines.write({'state': 'received'})
                    elif vals['state'] == 'cancel':
                        batch_lines.write({'state': 'cancelled'})
        
        return result


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    batch_rfq_line_id = fields.Many2one(
        'batch.rfq.line',
        string='Batch RFQ Line',
        readonly=True,
        help='Batch RFQ line that generated this purchase order line'
    )
    
    is_batch_rfq_line = fields.Boolean(
        string='Is Batch RFQ Line',
        compute='_compute_is_batch_rfq_line',
        store=True
    )
    
    @api.depends('batch_rfq_line_id')
    def _compute_is_batch_rfq_line(self):
        for line in self:
            line.is_batch_rfq_line = bool(line.batch_rfq_line_id)
    
    def write(self, vals):
        """Override to update batch RFQ line when PO line changes"""
        result = super(PurchaseOrderLine, self).write(vals)
        
        # Update related batch RFQ line with vendor response
        if any(field in vals for field in ['price_unit', 'date_planned']):
            for line in self:
                if line.batch_rfq_line_id:
                    update_vals = {}
                    if 'price_unit' in vals:
                        update_vals['vendor_quoted_price'] = vals['price_unit']
                    if 'date_planned' in vals:
                        update_vals['vendor_delivery_date'] = vals['date_planned']
                    
                    if update_vals:
                        line.batch_rfq_line_id.write(update_vals)
        
        return result