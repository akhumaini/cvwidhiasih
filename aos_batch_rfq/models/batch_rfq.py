# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class BatchRfq(models.Model):
    _name = 'batch.rfq'
    _description = 'Batch Request for Quotation'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Batch RFQ Number',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _('New')
    )
    
    description = fields.Text(
        string='Description',
        help='Description of the batch RFQ'
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('sent', 'Sent'),
        ('partial', 'Partially Received'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    user_id = fields.Many2one(
        'res.users',
        string='Responsible',
        default=lambda self: self.env.user,
        tracking=True
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )
    
    date_created = fields.Datetime(
        string='Creation Date',
        default=fields.Datetime.now,
        readonly=True
    )
    
    date_deadline = fields.Datetime(
        string='Deadline',
        help='Expected deadline for receiving all quotations'
    )
    
    date_sent = fields.Datetime(
        string='Date Sent',
        readonly=True,
        help='Date when batch RFQ was sent to vendors'
    )
    
    date_completed = fields.Datetime(
        string='Date Completed',
        readonly=True,
        help='Date when all RFQs in batch were completed'
    )
    
    # Relations
    batch_rfq_line_ids = fields.One2many(
        'batch.rfq.line',
        'batch_rfq_id',
        string='RFQ Lines',
        copy=True
    )
    
    purchase_order_ids = fields.One2many(
        'purchase.order',
        'batch_rfq_id',
        string='Purchase Orders',
        readonly=True
    )
    
    # Computed fields
    total_rfq_count = fields.Integer(
        string='Total RFQs',
        compute='_compute_rfq_statistics',
        store=True
    )
    
    sent_rfq_count = fields.Integer(
        string='Sent RFQs',
        compute='_compute_rfq_statistics',
        store=True
    )
    
    received_rfq_count = fields.Integer(
        string='Received RFQs',
        compute='_compute_rfq_statistics',
        store=True
    )
    
    progress_percentage = fields.Float(
        string='Progress (%)',
        compute='_compute_rfq_statistics',
        store=True
    )
    
    total_estimated_amount = fields.Monetary(
        string='Total Estimated Amount',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id'
    )
    
    total_received_amount = fields.Monetary(
        string='Total Received Amount',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True
    )
    
    # Priority and categorization
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Very High')
    ], string='Priority', default='1')
    
    category_id = fields.Many2one(
        'purchase.category',
        string='Purchase Category'
    )
    
    # Email and communication
    email_template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        domain=[('model', '=', 'purchase.order')]
    )
    
    notes = fields.Html(string='Internal Notes')
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('batch.rfq') or _('New')
        return super(BatchRfq, self).create(vals)
    
    @api.depends('batch_rfq_line_ids', 'batch_rfq_line_ids.purchase_order_id', 
                 'batch_rfq_line_ids.purchase_order_id.state')
    def _compute_rfq_statistics(self):
        for record in self:
            lines = record.batch_rfq_line_ids
            total_count = len(lines)
            sent_count = len(lines.filtered(lambda l: l.purchase_order_id and l.purchase_order_id.state in ['sent', 'to approve', 'purchase', 'done']))
            received_count = len(lines.filtered(lambda l: l.purchase_order_id and l.purchase_order_id.state in ['to approve', 'purchase', 'done']))
            
            record.total_rfq_count = total_count
            record.sent_rfq_count = sent_count
            record.received_rfq_count = received_count
            record.progress_percentage = (received_count / total_count * 100) if total_count > 0 else 0
    
    @api.depends('batch_rfq_line_ids', 'batch_rfq_line_ids.estimated_amount',
                 'batch_rfq_line_ids.purchase_order_id', 'batch_rfq_line_ids.purchase_order_id.amount_total')
    def _compute_amounts(self):
        for record in self:
            estimated_amount = sum(record.batch_rfq_line_ids.mapped('estimated_amount'))
            received_amount = sum(line.purchase_order_id.amount_total 
                                for line in record.batch_rfq_line_ids 
                                if line.purchase_order_id and line.purchase_order_id.state in ['to approve', 'purchase', 'done'])
            
            record.total_estimated_amount = estimated_amount
            record.total_received_amount = received_amount
    
    def action_confirm(self):
        """Confirm the batch RFQ"""
        if not self.batch_rfq_line_ids:
            raise UserError(_('Cannot confirm batch RFQ without any lines.'))
        
        self.state = 'confirmed'
        self.message_post(body=_('Batch RFQ has been confirmed.'))
    
    def action_generate_rfqs(self):
        """Generate individual RFQs from batch lines"""
        if self.state != 'confirmed':
            raise UserError(_('Batch RFQ must be confirmed before generating RFQs.'))
        
        generated_orders = []
        
        for line in self.batch_rfq_line_ids:
            if not line.purchase_order_id:
                # Create purchase order
                po_vals = line._prepare_purchase_order_values()
                purchase_order = self.env['purchase.order'].create(po_vals)
                line.purchase_order_id = purchase_order.id
                generated_orders.append(purchase_order)
        
        if generated_orders:
            self.message_post(
                body=_('%d Purchase Orders have been generated from this batch RFQ.') % len(generated_orders)
            )
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Generated RFQs'),
            'res_model': 'purchase.order',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', [po.id for po in generated_orders])],
            'context': {'default_batch_rfq_id': self.id}
        }
    
    def action_send_rfqs(self):
        """Send all RFQs to vendors"""
        if not self.purchase_order_ids:
            raise UserError(_('No RFQs to send. Please generate RFQs first.'))
        
        sent_count = 0
        for po in self.purchase_order_ids.filtered(lambda p: p.state == 'draft'):
            try:
                po.button_confirm()
                if self.email_template_id:
                    po.with_context(force_send=True).message_post_with_template(
                        self.email_template_id.id
                    )
                sent_count += 1
            except Exception as e:
                _logger.error(f"Failed to send RFQ {po.name}: {str(e)}")
        
        if sent_count > 0:
            self.state = 'sent'
            self.date_sent = fields.Datetime.now()
            self.message_post(
                body=_('%d RFQs have been sent to vendors.') % sent_count
            )
    
    def action_cancel(self):
        """Cancel the batch RFQ"""
        self.state = 'cancelled'
        # Cancel all related purchase orders
        self.purchase_order_ids.filtered(lambda po: po.state in ['draft', 'sent']).button_cancel()
        self.message_post(body=_('Batch RFQ has been cancelled.'))
    
    def action_set_to_draft(self):
        """Reset to draft state"""
        self.state = 'draft'
        self.message_post(body=_('Batch RFQ has been reset to draft.'))
    
    def action_view_purchase_orders(self):
        """View related purchase orders"""
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        action['domain'] = [('batch_rfq_id', '=', self.id)]
        action['context'] = {'default_batch_rfq_id': self.id}
        return action
    
    @api.model
    def _update_batch_status(self):
        """Cron method to update batch status based on RFQ progress"""
        batches = self.search([('state', 'in', ['sent', 'partial'])])
        
        for batch in batches:
            if batch.progress_percentage == 100:
                batch.state = 'done'
                batch.date_completed = fields.Datetime.now()
            elif batch.progress_percentage > 0:
                batch.state = 'partial'
    
    @api.constrains('date_deadline')
    def _check_deadline(self):
        for record in self:
            if record.date_deadline and record.date_deadline < fields.Datetime.now():
                raise ValidationError(_('Deadline cannot be in the past.'))


class PurchaseCategory(models.Model):
    _name = 'purchase.category'
    _description = 'Purchase Category'
    
    name = fields.Char(string='Category Name', required=True)
    code = fields.Char(string='Category Code')
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)