# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class BatchRfqSendWizard(models.TransientModel):
    _name = 'batch.rfq.send.wizard'
    _description = 'Batch RFQ Send Wizard'

    batch_rfq_id = fields.Many2one(
        'batch.rfq',
        string='Batch RFQ',
        required=True,
        readonly=True
    )
    
    email_template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        domain=[('model', '=', 'purchase.order')],
        required=True
    )
    
    subject = fields.Char(
        string='Subject',
        related='email_template_id.subject',
        readonly=True
    )
    
    body_html = fields.Html(
        string='Email Body',
        related='email_template_id.body_html',
        readonly=True
    )
    
    # Send options
    send_method = fields.Selection([
        ('email', 'Send by Email'),
        ('print', 'Print Only'),
        ('both', 'Email and Print')
    ], string='Send Method', default='email', required=True)
    
    # RFQ selection
    rfq_selection = fields.Selection([
        ('all', 'All RFQs'),
        ('selected', 'Selected RFQs'),
        ('by_vendor', 'By Vendor'),
        ('by_status', 'By Status')
    ], string='RFQ Selection', default='all', required=True)
    
    # For selected RFQs
    purchase_order_ids = fields.Many2many(
        'purchase.order',
        string='Purchase Orders',
        domain="[('batch_rfq_id', '=', batch_rfq_id)]"
    )
    
    # For vendor selection
    vendor_ids = fields.Many2many(
        'res.partner',
        string='Vendors',
        domain="[('supplier_rank', '>', 0)]"
    )
    
    # For status selection
    po_states = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='PO Status')
    
    # Additional options
    force_send = fields.Boolean(
        string='Force Send',
        help='Force send even if already sent'
    )
    
    add_attachment = fields.Boolean(
        string='Add PDF Attachment',
        default=True
    )
    
    custom_message = fields.Text(
        string='Custom Message',
        help='Additional message to include in email'
    )
    
    # Summary fields
    total_rfqs = fields.Integer(
        string='Total RFQs',
        compute='_compute_rfq_counts'
    )
    
    selected_rfqs = fields.Integer(
        string='Selected RFQs',
        compute='_compute_rfq_counts'
    )
    
    @api.depends('batch_rfq_id', 'rfq_selection', 'purchase_order_ids', 
                 'vendor_ids', 'po_states')
    def _compute_rfq_counts(self):
        for wizard in self:
            if not wizard.batch_rfq_id:
                wizard.total_rfqs = 0
                wizard.selected_rfqs = 0
                continue
            
            all_pos = wizard.batch_rfq_id.purchase_order_ids
            wizard.total_rfqs = len(all_pos)
            
            selected_pos = wizard._get_selected_purchase_orders()
            wizard.selected_rfqs = len(selected_pos)
    
    def _get_selected_purchase_orders(self):
        """Get purchase orders based on selection criteria"""
        if not self.batch_rfq_id:
            return self.env['purchase.order']
        
        all_pos = self.batch_rfq_id.purchase_order_ids
        
        if self.rfq_selection == 'all':
            return all_pos
        elif self.rfq_selection == 'selected':
            return self.purchase_order_ids
        elif self.rfq_selection == 'by_vendor':
            return all_pos.filtered(lambda po: po.partner_id in self.vendor_ids)
        elif self.rfq_selection == 'by_status':
            return all_pos.filtered(lambda po: po.state == self.po_states)
        
        return self.env['purchase.order']
    
    @api.onchange('rfq_selection')
    def _onchange_rfq_selection(self):
        """Clear selection fields when method changes"""
        if self.rfq_selection != 'selected':
            self.purchase_order_ids = [(5, 0, 0)]
        if self.rfq_selection != 'by_vendor':
            self.vendor_ids = [(5, 0, 0)]
        if self.rfq_selection != 'by_status':
            self.po_states = False
    
    @api.onchange('batch_rfq_id')
    def _onchange_batch_rfq_id(self):
        """Set default email template from batch RFQ"""
        if self.batch_rfq_id and self.batch_rfq_id.email_template_id:
            self.email_template_id = self.batch_rfq_id.email_template_id
    
    def action_send_rfqs(self):
        """Send RFQs based on wizard configuration"""
        self.ensure_one()
        
        selected_pos = self._get_selected_purchase_orders()
        
        if not selected_pos:
            raise UserError(_('No RFQs selected for sending.'))
        
        # Filter POs that can be sent
        sendable_pos = selected_pos
        if not self.force_send:
            sendable_pos = selected_pos.filtered(lambda po: po.state == 'draft')
        
        if not sendable_pos:
            raise UserError(_('No RFQs available for sending. Use "Force Send" to send already sent RFQs.'))
        
        sent_count = 0
        error_count = 0
        errors = []
        
        for po in sendable_pos:
            try:
                # Confirm PO if in draft state
                if po.state == 'draft':
                    po.button_confirm()
                
                # Send based on method
                if self.send_method in ['email', 'both']:
                    self._send_email(po)
                
                if self.send_method in ['print', 'both']:
                    self._print_rfq(po)
                
                sent_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append(f"RFQ {po.name}: {str(e)}")
                _logger.error(f"Failed to send RFQ {po.name}: {str(e)}")
        
        # Update batch RFQ status
        if sent_count > 0:
            self.batch_rfq_id.state = 'sent'
            self.batch_rfq_id.date_sent = fields.Datetime.now()
        
        # Show result message
        message = f"Successfully sent {sent_count} RFQ(s)."
        if error_count > 0:
            message += f"\n{error_count} RFQ(s) failed to send:\n" + "\n".join(errors)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('RFQ Send Result'),
                'message': message,
                'type': 'success' if error_count == 0 else 'warning',
                'sticky': True,
            }
        }
    
    def _send_email(self, purchase_order):
        """Send email for a purchase order"""
        template = self.email_template_id
        
        # Prepare email context
        email_ctx = {
            'default_model': 'purchase.order',
            'default_res_id': purchase_order.id,
            'default_use_template': bool(template),
            'default_template_id': template.id if template else False,
            'default_composition_mode': 'comment',
            'force_send': True,
        }
        
        # Add custom message if provided
        if self.custom_message:
            email_ctx['custom_message'] = self.custom_message
        
        # Send email
        purchase_order.with_context(**email_ctx).message_post_with_template(
            template.id,
            composition_mode='comment',
            email_layout_xmlid="mail.mail_notification_paynow",
        )
    
    def _print_rfq(self, purchase_order):
        """Print RFQ for a purchase order"""
        # This would trigger the print action
        # For now, we'll just log it
        _logger.info(f"Print RFQ requested for {purchase_order.name}")
    
    def action_preview_email(self):
        """Preview email template"""
        self.ensure_one()
        
        if not self.email_template_id:
            raise UserError(_('Please select an email template first.'))
        
        selected_pos = self._get_selected_purchase_orders()
        if not selected_pos:
            raise UserError(_('No RFQs selected for preview.'))
        
        # Use first PO for preview
        po = selected_pos[0]
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Email Preview'),
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_model': 'purchase.order',
                'default_res_id': po.id,
                'default_use_template': True,
                'default_template_id': self.email_template_id.id,
                'default_composition_mode': 'comment',
            }
        }
    
    def action_test_send(self):
        """Send test email to current user"""
        self.ensure_one()
        
        if not self.email_template_id:
            raise UserError(_('Please select an email template first.'))
        
        selected_pos = self._get_selected_purchase_orders()
        if not selected_pos:
            raise UserError(_('No RFQs selected for test.'))
        
        # Use first PO for test
        po = selected_pos[0]
        
        # Send test email to current user
        template = self.email_template_id.with_context(
            lang=self.env.user.lang
        )
        
        template.send_mail(
            po.id,
            force_send=True,
            email_values={
                'email_to': self.env.user.email,
                'subject': f'[TEST] {template.subject}',
            }
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Test Email Sent'),
                'message': _('Test email sent to %s') % self.env.user.email,
                'type': 'success',
            }
        }