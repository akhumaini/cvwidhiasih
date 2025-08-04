# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class BatchRfqWizard(models.TransientModel):
    _name = 'batch.rfq.wizard'
    _description = 'Batch RFQ Creation Wizard'

    name = fields.Char(
        string='Batch RFQ Name',
        help='Name for the batch RFQ. Leave empty for auto-generation.'
    )
    
    description = fields.Text(
        string='Description',
        required=True,
        help='Description of the batch RFQ'
    )
    
    date_deadline = fields.Datetime(
        string='Deadline',
        help='Expected deadline for receiving all quotations'
    )
    
    category_id = fields.Many2one(
        'purchase.category',
        string='Purchase Category'
    )
    
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Very High')
    ], string='Priority', default='1')
    
    # Creation method
    creation_method = fields.Selection([
        ('manual', 'Manual Entry'),
        ('from_products', 'From Products'),
        ('from_template', 'From Template'),
        ('from_purchase_request', 'From Purchase Request')
    ], string='Creation Method', default='manual', required=True)
    
    # For manual entry
    line_ids = fields.One2many(
        'batch.rfq.wizard.line',
        'wizard_id',
        string='RFQ Lines'
    )
    
    # For product-based creation
    product_ids = fields.Many2many(
        'product.product',
        string='Products',
        domain=[('purchase_ok', '=', True)]
    )
    
    vendor_ids = fields.Many2many(
        'res.partner',
        string='Vendors',
        domain=[('supplier_rank', '>', 0)]
    )
    
    # For template-based creation
    template_id = fields.Many2one(
        'batch.rfq.template',
        string='RFQ Template'
    )
    
    # Options
    auto_send = fields.Boolean(
        string='Auto Send RFQs',
        help='Automatically send RFQs to vendors after creation'
    )
    
    email_template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        domain=[('model', '=', 'purchase.order')]
    )
    
    def action_create_batch_rfq(self):
        """Create the batch RFQ based on wizard configuration"""
        self.ensure_one()
        
        # Create batch RFQ header
        batch_vals = self._prepare_batch_rfq_values()
        batch_rfq = self.env['batch.rfq'].create(batch_vals)
        
        # Create lines based on creation method
        if self.creation_method == 'manual':
            self._create_lines_from_manual(batch_rfq)
        elif self.creation_method == 'from_products':
            self._create_lines_from_products(batch_rfq)
        elif self.creation_method == 'from_template':
            self._create_lines_from_template(batch_rfq)
        elif self.creation_method == 'from_purchase_request':
            self._create_lines_from_purchase_request(batch_rfq)
        
        # Auto-confirm and send if requested
        if batch_rfq.batch_rfq_line_ids:
            batch_rfq.action_confirm()
            
            if self.auto_send:
                batch_rfq.action_generate_rfqs()
                batch_rfq.action_send_rfqs()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Batch RFQ'),
            'res_model': 'batch.rfq',
            'res_id': batch_rfq.id,
            'view_mode': 'form',
            'target': 'current'
        }
    
    def _prepare_batch_rfq_values(self):
        """Prepare values for batch RFQ creation"""
        return {
            'name': self.name or False,  # Will be auto-generated if empty
            'description': self.description,
            'date_deadline': self.date_deadline,
            'category_id': self.category_id.id if self.category_id else False,
            'priority': self.priority,
            'email_template_id': self.email_template_id.id if self.email_template_id else False,
        }
    
    def _create_lines_from_manual(self, batch_rfq):
        """Create batch RFQ lines from manual entry"""
        for line in self.line_ids:
            line_vals = line._prepare_batch_rfq_line_values(batch_rfq.id)
            self.env['batch.rfq.line'].create(line_vals)
    
    def _create_lines_from_products(self, batch_rfq):
        """Create batch RFQ lines from products and vendors"""
        if not self.product_ids or not self.vendor_ids:
            raise UserError(_('Please select both products and vendors.'))
        
        for product in self.product_ids:
            for vendor in self.vendor_ids:
                # Check if vendor supplies this product
                supplierinfo = self.env['product.supplierinfo'].search([
                    ('product_tmpl_id', '=', product.product_tmpl_id.id),
                    ('name', '=', vendor.id)
                ], limit=1)
                
                line_vals = {
                    'batch_rfq_id': batch_rfq.id,
                    'name': product.name,
                    'partner_id': vendor.id,
                    'product_id': product.id,
                    'product_qty': 1.0,
                    'product_uom_id': product.uom_po_id.id,
                    'estimated_price': supplierinfo.price if supplierinfo else 0.0,
                    'date_required': self.date_deadline.date() if self.date_deadline else False,
                }
                self.env['batch.rfq.line'].create(line_vals)
    
    def _create_lines_from_template(self, batch_rfq):
        """Create batch RFQ lines from template"""
        if not self.template_id:
            raise UserError(_('Please select a template.'))
        
        for template_line in self.template_id.line_ids:
            line_vals = template_line._prepare_batch_rfq_line_values(batch_rfq.id)
            self.env['batch.rfq.line'].create(line_vals)
    
    def _create_lines_from_purchase_request(self, batch_rfq):
        """Create batch RFQ lines from purchase requests"""
        # This would integrate with a purchase request module if available
        # For now, we'll skip this implementation
        pass
    
    @api.onchange('creation_method')
    def _onchange_creation_method(self):
        """Clear fields when creation method changes"""
        if self.creation_method != 'manual':
            self.line_ids = [(5, 0, 0)]
        if self.creation_method != 'from_products':
            self.product_ids = [(5, 0, 0)]
            self.vendor_ids = [(5, 0, 0)]
        if self.creation_method != 'from_template':
            self.template_id = False


class BatchRfqWizardLine(models.TransientModel):
    _name = 'batch.rfq.wizard.line'
    _description = 'Batch RFQ Wizard Line'

    wizard_id = fields.Many2one(
        'batch.rfq.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )
    
    sequence = fields.Integer(string='Sequence', default=10)
    
    name = fields.Char(
        string='Description',
        required=True
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Vendor',
        required=True,
        domain=[('supplier_rank', '>', 0)]
    )
    
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
    
    estimated_price = fields.Float(
        string='Estimated Unit Price'
    )
    
    date_required = fields.Date(
        string='Required Date'
    )
    
    date_deadline = fields.Date(
        string='RFQ Deadline'
    )
    
    notes = fields.Text(string='Notes')
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_po_id
            self.name = self.product_id.name
            
            # Get last purchase price as estimated price
            if self.partner_id:
                last_po_line = self.env['purchase.order.line'].search([
                    ('product_id', '=', self.product_id.id),
                    ('partner_id', '=', self.partner_id.id),
                    ('state', 'in', ['purchase', 'done'])
                ], order='create_date desc', limit=1)
                
                if last_po_line:
                    self.estimated_price = last_po_line.price_unit
    
    def _prepare_batch_rfq_line_values(self, batch_rfq_id):
        """Prepare values for batch RFQ line creation"""
        return {
            'batch_rfq_id': batch_rfq_id,
            'sequence': self.sequence,
            'name': self.name,
            'partner_id': self.partner_id.id,
            'product_id': self.product_id.id if self.product_id else False,
            'product_qty': self.product_qty,
            'product_uom_id': self.product_uom_id.id,
            'estimated_price': self.estimated_price,
            'date_required': self.date_required,
            'date_deadline': self.date_deadline,
            'notes': self.notes,
        }


class BatchRfqTemplate(models.Model):
    _name = 'batch.rfq.template'
    _description = 'Batch RFQ Template'

    name = fields.Char(string='Template Name', required=True)
    description = fields.Text(string='Description')
    category_id = fields.Many2one('purchase.category', string='Category')
    active = fields.Boolean(string='Active', default=True)
    
    line_ids = fields.One2many(
        'batch.rfq.template.line',
        'template_id',
        string='Template Lines'
    )


class BatchRfqTemplateLine(models.Model):
    _name = 'batch.rfq.template.line'
    _description = 'Batch RFQ Template Line'

    template_id = fields.Many2one(
        'batch.rfq.template',
        string='Template',
        required=True,
        ondelete='cascade'
    )
    
    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(string='Description', required=True)
    product_id = fields.Many2one('product.product', string='Product')
    product_qty = fields.Float(string='Quantity', default=1.0)
    product_uom_id = fields.Many2one('uom.uom', string='UoM')
    estimated_price = fields.Float(string='Estimated Price')
    
    def _prepare_batch_rfq_line_values(self, batch_rfq_id):
        """Prepare values for batch RFQ line creation from template"""
        return {
            'batch_rfq_id': batch_rfq_id,
            'sequence': self.sequence,
            'name': self.name,
            'product_id': self.product_id.id if self.product_id else False,
            'product_qty': self.product_qty,
            'product_uom_id': self.product_uom_id.id if self.product_uom_id else False,
            'estimated_price': self.estimated_price,
        }