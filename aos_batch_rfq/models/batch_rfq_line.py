# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class BatchRfqLine(models.Model):
    _name = 'batch.rfq.line'
    _description = 'Batch RFQ Line'
    _order = 'sequence, id'

    # Basic fields
    sequence = fields.Integer(string='Sequence', default=10)
    
    batch_rfq_id = fields.Many2one(
        'batch.rfq',
        string='Batch RFQ',
        required=True,
        ondelete='cascade'
    )
    
    name = fields.Char(
        string='Description',
        required=True,
        help='Description of the RFQ line'
    )
    
    # Vendor information
    partner_id = fields.Many2one(
        'res.partner',
        string='Vendor',
        required=True,
        domain=[('supplier_rank', '>', 0)]
    )
    
    # Product information
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        domain=[('purchase_ok', '=', True)]
    )
    
    product_qty = fields.Float(
        string='Quantity',
        default=1.0,
        required=True
    )
    
    product_uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        required=True
    )
    
    # Pricing
    estimated_price = fields.Float(
        string='Estimated Unit Price',
        help='Estimated price per unit'
    )
    
    estimated_amount = fields.Monetary(
        string='Estimated Total Amount',
        compute='_compute_estimated_amount',
        store=True,
        currency_field='currency_id'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='batch_rfq_id.currency_id',
        store=True
    )
    
    # Dates
    date_required = fields.Date(
        string='Required Date',
        help='Date when the product is required'
    )
    
    date_deadline = fields.Date(
        string='RFQ Deadline',
        help='Deadline for receiving quotation from vendor'
    )
    
    # Status and tracking
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'RFQ Sent'),
        ('received', 'Quotation Received'),
        ('selected', 'Selected'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    # Relations
    purchase_order_id = fields.Many2one(
        'purchase.order',
        string='Purchase Order',
        readonly=True,
        help='Generated purchase order for this line'
    )
    
    purchase_order_line_ids = fields.One2many(
        'purchase.order.line',
        'batch_rfq_line_id',
        string='Purchase Order Lines'
    )
    
    # Additional information
    notes = fields.Text(string='Notes')
    
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Very High')
    ], string='Priority', default='1')
    
    # Vendor response tracking
    vendor_response_date = fields.Datetime(
        string='Vendor Response Date',
        readonly=True
    )
    
    vendor_quoted_price = fields.Float(
        string='Vendor Quoted Price',
        readonly=True
    )
    
    vendor_delivery_date = fields.Date(
        string='Vendor Delivery Date',
        readonly=True
    )
    
    vendor_notes = fields.Text(
        string='Vendor Notes',
        readonly=True
    )
    
    # Computed fields
    price_variance = fields.Float(
        string='Price Variance (%)',
        compute='_compute_price_variance',
        help='Variance between estimated and quoted price'
    )
    
    is_overdue = fields.Boolean(
        string='Is Overdue',
        compute='_compute_overdue_status'
    )
    
    @api.depends('product_qty', 'estimated_price')
    def _compute_estimated_amount(self):
        for line in self:
            line.estimated_amount = line.product_qty * line.estimated_price
    
    @api.depends('estimated_price', 'vendor_quoted_price')
    def _compute_price_variance(self):
        for line in self:
            if line.estimated_price and line.vendor_quoted_price:
                variance = ((line.vendor_quoted_price - line.estimated_price) / line.estimated_price) * 100
                line.price_variance = variance
            else:
                line.price_variance = 0.0
    
    @api.depends('date_deadline', 'state')
    def _compute_overdue_status(self):
        today = fields.Date.today()
        for line in self:
            line.is_overdue = (
                line.date_deadline and 
                line.date_deadline < today and 
                line.state not in ['received', 'selected', 'cancelled']
            )
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_po_id
            self.name = self.product_id.name
            
            # Get last purchase price as estimated price
            last_po_line = self.env['purchase.order.line'].search([
                ('product_id', '=', self.product_id.id),
                ('partner_id', '=', self.partner_id.id),
                ('state', 'in', ['purchase', 'done'])
            ], order='create_date desc', limit=1)
            
            if last_po_line:
                self.estimated_price = last_po_line.price_unit
    
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id and self.product_id:
            # Update estimated price based on vendor
            self._onchange_product_id()
    
    def _prepare_purchase_order_values(self):
        """Prepare values for creating purchase order"""
        self.ensure_one()
        
        # Check if there's already a PO for this vendor in the batch
        existing_po = self.batch_rfq_id.purchase_order_ids.filtered(
            lambda po: po.partner_id.id == self.partner_id.id
        )
        
        if existing_po:
            # Add line to existing PO
            return self._prepare_purchase_order_line_values(existing_po[0])
        else:
            # Create new PO
            po_vals = {
                'partner_id': self.partner_id.id,
                'batch_rfq_id': self.batch_rfq_id.id,
                'origin': self.batch_rfq_id.name,
                'company_id': self.batch_rfq_id.company_id.id,
                'currency_id': self.currency_id.id,
                'date_order': fields.Datetime.now(),
                'order_line': [(0, 0, self._prepare_purchase_order_line_values())]
            }
            return po_vals
    
    def _prepare_purchase_order_line_values(self, purchase_order=None):
        """Prepare values for purchase order line"""
        self.ensure_one()
        
        line_vals = {
            'name': self.name,
            'product_id': self.product_id.id if self.product_id else False,
            'product_qty': self.product_qty,
            'product_uom': self.product_uom_id.id,
            'price_unit': self.estimated_price,
            'date_planned': self.date_required or fields.Date.today(),
            'batch_rfq_line_id': self.id,
        }
        
        if purchase_order:
            line_vals['order_id'] = purchase_order.id
            
        return line_vals
    
    def action_create_rfq(self):
        """Create individual RFQ for this line"""
        self.ensure_one()
        
        if self.purchase_order_id:
            raise UserError(_('RFQ already exists for this line.'))
        
        po_vals = self._prepare_purchase_order_values()
        purchase_order = self.env['purchase.order'].create(po_vals)
        self.purchase_order_id = purchase_order.id
        self.state = 'sent'
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Purchase Order'),
            'res_model': 'purchase.order',
            'res_id': purchase_order.id,
            'view_mode': 'form',
            'target': 'current'
        }
    
    def action_view_rfq(self):
        """View the related RFQ/Purchase Order"""
        self.ensure_one()
        
        if not self.purchase_order_id:
            raise UserError(_('No RFQ exists for this line.'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Purchase Order'),
            'res_model': 'purchase.order',
            'res_id': self.purchase_order_id.id,
            'view_mode': 'form',
            'target': 'current'
        }
    
    def action_mark_received(self):
        """Mark quotation as received"""
        self.ensure_one()
        self.state = 'received'
        self.vendor_response_date = fields.Datetime.now()
        
        # Update vendor quoted price from PO if available
        if self.purchase_order_id and self.purchase_order_id.order_line:
            po_line = self.purchase_order_id.order_line.filtered(
                lambda l: l.batch_rfq_line_id.id == self.id
            )
            if po_line:
                self.vendor_quoted_price = po_line[0].price_unit
    
    def action_select_quotation(self):
        """Select this quotation"""
        self.ensure_one()
        self.state = 'selected'
        
        # Optionally, you can confirm the related PO
        if self.purchase_order_id and self.purchase_order_id.state == 'draft':
            self.purchase_order_id.button_confirm()
    
    def action_cancel(self):
        """Cancel this RFQ line"""
        self.ensure_one()
        self.state = 'cancelled'
        
        if self.purchase_order_id and self.purchase_order_id.state in ['draft', 'sent']:
            self.purchase_order_id.button_cancel()
    
    @api.constrains('product_qty')
    def _check_product_qty(self):
        for line in self:
            if line.product_qty <= 0:
                raise ValidationError(_('Product quantity must be positive.'))
    
    @api.constrains('date_deadline', 'date_required')
    def _check_dates(self):
        for line in self:
            if line.date_deadline and line.date_required:
                if line.date_deadline > line.date_required:
                    raise ValidationError(_('RFQ deadline cannot be after required date.'))