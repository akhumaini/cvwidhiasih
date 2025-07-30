from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class PurchaseOrderBatch(models.Model):
    _name = 'purchase.order.batch'
    _description = 'Purchase Order Batch'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Batch Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    purchase_order_ids = fields.One2many(
        'purchase.order',
        'batch_id',
        string='Purchase Orders',
        domain=[('state', 'in', ['draft', 'sent', 'to approve'])]
    )
    
    purchase_order_count = fields.Integer(
        string='PO Count',
        compute='_compute_purchase_order_count',
        store=True
    )
    
    total_amount = fields.Monetary(
        string='Total Amount',
        compute='_compute_total_amount',
        store=True,
        currency_field='currency_id'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    
    partner_ids = fields.Many2many(
        'res.partner',
        compute='_compute_partners',
        string='Vendors',
        store=True
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='Responsible',
        default=lambda self: self.env.user,
        required=True,
        tracking=True
    )
    
    date_planned = fields.Datetime(
        string='Scheduled Date',
        compute='_compute_date_planned',
        store=True
    )
    
    notes = fields.Text(string='Notes')
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.order.batch') or _('New')
        return super(PurchaseOrderBatch, self).create(vals)
    
    @api.depends('purchase_order_ids')
    def _compute_purchase_order_count(self):
        for batch in self:
            batch.purchase_order_count = len(batch.purchase_order_ids)
    
    @api.depends('purchase_order_ids', 'purchase_order_ids.amount_total')
    def _compute_total_amount(self):
        for batch in self:
            batch.total_amount = sum(batch.purchase_order_ids.mapped('amount_total'))
    
    @api.depends('purchase_order_ids', 'purchase_order_ids.partner_id')
    def _compute_partners(self):
        for batch in self:
            batch.partner_ids = batch.purchase_order_ids.mapped('partner_id')
    
    @api.depends('purchase_order_ids', 'purchase_order_ids.date_planned')
    def _compute_date_planned(self):
        for batch in self:
            if batch.purchase_order_ids:
                dates = batch.purchase_order_ids.mapped('date_planned')
                batch.date_planned = min(dates) if dates else False
            else:
                batch.date_planned = False
    
    def action_confirm(self):
        """Confirm the batch and all associated purchase orders"""
        if not self.purchase_order_ids:
            raise UserError(_('Cannot confirm batch without purchase orders.'))
        
        for po in self.purchase_order_ids:
            if po.state not in ['draft', 'sent', 'to approve']:
                raise UserError(_(
                    'Purchase Order %s is in state %s and cannot be processed in batch.'
                ) % (po.name, po.state))
        
        self.state = 'confirmed'
        self.message_post(body=_('Batch confirmed with %d purchase orders.') % len(self.purchase_order_ids))
    
    def action_process(self):
        """Process all purchase orders in the batch"""
        if self.state != 'confirmed':
            raise UserError(_('Batch must be confirmed before processing.'))
        
        self.state = 'processing'
        
        # Confirm all purchase orders
        failed_pos = []
        for po in self.purchase_order_ids:
            try:
                if po.state == 'draft':
                    po.button_confirm()
                elif po.state == 'sent':
                    po.button_confirm()
                elif po.state == 'to approve':
                    po.button_approve()
            except Exception as e:
                failed_pos.append((po.name, str(e)))
        
        if failed_pos:
            error_msg = _('Failed to process the following POs:\n')
            for po_name, error in failed_pos:
                error_msg += f'- {po_name}: {error}\n'
            raise UserError(error_msg)
        
        self.state = 'done'
        self.message_post(body=_('Batch processing completed successfully.'))
    
    def action_cancel(self):
        """Cancel the batch"""
        if self.state == 'done':
            raise UserError(_('Cannot cancel a completed batch.'))
        
        self.state = 'cancelled'
        self.message_post(body=_('Batch cancelled.'))
    
    def action_reset_to_draft(self):
        """Reset batch to draft state"""
        self.state = 'draft'
        self.message_post(body=_('Batch reset to draft.'))
    
    def action_view_purchase_orders(self):
        """Open purchase orders in the batch"""
        action = self.env['ir.actions.act_window']._for_xml_id('purchase.purchase_rfq')
        
        if len(self.purchase_order_ids) > 1:
            action['domain'] = [('id', 'in', self.purchase_order_ids.ids)]
        elif len(self.purchase_order_ids) == 1:
            action['views'] = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
            action['res_id'] = self.purchase_order_ids.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        
        return action
    
    def unlink(self):
        """Override unlink to check state"""
        for batch in self:
            if batch.state not in ['draft', 'cancelled']:
                raise UserError(_('Cannot delete batch in state %s.') % batch.state)
        return super(PurchaseOrderBatch, self).unlink()
    
    @api.constrains('purchase_order_ids')
    def _check_purchase_orders_state(self):
        """Ensure all POs are in valid state for batching"""
        for batch in self:
            if batch.state in ['confirmed', 'processing']:
                invalid_pos = batch.purchase_order_ids.filtered(
                    lambda po: po.state not in ['draft', 'sent', 'to approve']
                )
                if invalid_pos:
                    raise ValidationError(_(
                        'The following purchase orders cannot be included in batch: %s'
                    ) % ', '.join(invalid_pos.mapped('name')))