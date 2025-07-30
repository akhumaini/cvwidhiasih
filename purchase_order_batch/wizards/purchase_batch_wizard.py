from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PurchaseBatchWizard(models.TransientModel):
    _name = 'purchase.batch.wizard'
    _description = 'Purchase Order Batch Wizard'

    name = fields.Char(
        string='Batch Name',
        help='Leave empty to auto-generate'
    )
    
    purchase_order_ids = fields.Many2many(
        'purchase.order',
        string='Purchase Orders',
        domain=[('state', 'in', ['draft', 'sent', 'to approve']), ('batch_id', '=', False)],
        required=True
    )
    
    partner_filter_id = fields.Many2one(
        'res.partner',
        string='Filter by Vendor',
        help='Filter purchase orders by vendor'
    )
    
    date_from = fields.Date(
        string='Date From',
        help='Filter purchase orders from this date'
    )
    
    date_to = fields.Date(
        string='Date To',
        help='Filter purchase orders until this date'
    )
    
    notes = fields.Text(string='Notes')
    
    @api.onchange('partner_filter_id', 'date_from', 'date_to')
    def _onchange_filters(self):
        """Update domain based on filters"""
        domain = [
            ('state', 'in', ['draft', 'sent', 'to approve']),
            ('batch_id', '=', False)
        ]
        
        if self.partner_filter_id:
            domain.append(('partner_id', '=', self.partner_filter_id.id))
        
        if self.date_from:
            domain.append(('date_order', '>=', self.date_from))
        
        if self.date_to:
            domain.append(('date_order', '<=', self.date_to))
        
        return {'domain': {'purchase_order_ids': domain}}
    
    def action_create_batch(self):
        """Create batch with selected purchase orders"""
        if not self.purchase_order_ids:
            raise UserError(_('Please select at least one purchase order.'))
        
        # Check if any selected PO is already in a batch
        batched_pos = self.purchase_order_ids.filtered('batch_id')
        if batched_pos:
            raise UserError(_(
                'The following purchase orders are already in a batch: %s'
            ) % ', '.join(batched_pos.mapped('name')))
        
        # Create the batch
        batch_vals = {
            'purchase_order_ids': [(6, 0, self.purchase_order_ids.ids)],
            'notes': self.notes or _('Batch created from wizard with %d purchase orders') % len(self.purchase_order_ids)
        }
        
        if self.name:
            batch_vals['name'] = self.name
        
        batch = self.env['purchase.order.batch'].create(batch_vals)
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Purchase Order Batch'),
            'res_model': 'purchase.order.batch',
            'res_id': batch.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    @api.model
    def default_get(self, fields_list):
        """Set default values including selected POs from context"""
        res = super(PurchaseBatchWizard, self).default_get(fields_list)
        
        # If called from purchase order list view with selected records
        active_ids = self.env.context.get('active_ids', [])
        if active_ids and self.env.context.get('active_model') == 'purchase.order':
            purchase_orders = self.env['purchase.order'].browse(active_ids)
            
            # Filter valid purchase orders
            valid_pos = purchase_orders.filtered(
                lambda po: po.state in ['draft', 'sent', 'to approve'] and not po.batch_id
            )
            
            if valid_pos:
                res['purchase_order_ids'] = [(6, 0, valid_pos.ids)]
        
        return res


class PurchaseBatchAddWizard(models.TransientModel):
    _name = 'purchase.batch.add.wizard'
    _description = 'Add Purchase Orders to Batch Wizard'

    batch_id = fields.Many2one(
        'purchase.order.batch',
        string='Batch',
        required=True,
        domain=[('state', '=', 'draft')]
    )
    
    purchase_order_ids = fields.Many2many(
        'purchase.order',
        string='Purchase Orders to Add',
        domain=[('state', 'in', ['draft', 'sent', 'to approve']), ('batch_id', '=', False)],
        required=True
    )
    
    def action_add_to_batch(self):
        """Add selected purchase orders to the batch"""
        if not self.purchase_order_ids:
            raise UserError(_('Please select at least one purchase order.'))
        
        if self.batch_id.state != 'draft':
            raise UserError(_('Can only add purchase orders to draft batches.'))
        
        # Check if any selected PO is already in a batch
        batched_pos = self.purchase_order_ids.filtered('batch_id')
        if batched_pos:
            raise UserError(_(
                'The following purchase orders are already in a batch: %s'
            ) % ', '.join(batched_pos.mapped('name')))
        
        # Add POs to batch
        self.purchase_order_ids.write({'batch_id': self.batch_id.id})
        
        self.batch_id.message_post(
            body=_('Added %d purchase orders to batch: %s') % (
                len(self.purchase_order_ids),
                ', '.join(self.purchase_order_ids.mapped('name'))
            )
        )
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Purchase Order Batch'),
            'res_model': 'purchase.order.batch',
            'res_id': self.batch_id.id,
            'view_mode': 'form',
            'target': 'current',
        }