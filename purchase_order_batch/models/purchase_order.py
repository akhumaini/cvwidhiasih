from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    batch_id = fields.Many2one(
        'purchase.order.batch',
        string='Batch',
        ondelete='set null',
        help='Batch this purchase order belongs to'
    )
    
    batch_state = fields.Selection(
        related='batch_id.state',
        string='Batch Status',
        store=True,
        readonly=True
    )
    
    def action_create_batch(self):
        """Create a new batch with selected purchase orders"""
        if not self:
            return
        
        # Check if any PO is already in a batch
        batched_pos = self.filtered('batch_id')
        if batched_pos:
            raise UserError(_(
                'The following purchase orders are already in a batch: %s'
            ) % ', '.join(batched_pos.mapped('name')))
        
        # Check states
        invalid_pos = self.filtered(lambda po: po.state not in ['draft', 'sent', 'to approve'])
        if invalid_pos:
            raise UserError(_(
                'The following purchase orders cannot be batched due to their state: %s'
            ) % ', '.join(invalid_pos.mapped('name')))
        
        # Create batch
        batch = self.env['purchase.order.batch'].create({
            'purchase_order_ids': [(6, 0, self.ids)],
            'notes': _('Batch created from %d purchase orders') % len(self)
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Purchase Order Batch'),
            'res_model': 'purchase.order.batch',
            'res_id': batch.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_remove_from_batch(self):
        """Remove purchase order from its batch"""
        for po in self:
            if po.batch_id and po.batch_id.state not in ['draft']:
                raise UserError(_(
                    'Cannot remove %s from batch %s because the batch is %s'
                ) % (po.name, po.batch_id.name, po.batch_id.state))
            po.batch_id = False
    
    def write(self, vals):
        """Override write to handle batch constraints"""
        # If trying to change state and PO is in a confirmed/processing batch
        if 'state' in vals:
            for po in self:
                if po.batch_id and po.batch_id.state in ['confirmed', 'processing']:
                    if vals['state'] not in ['purchase', 'done', 'cancel']:
                        raise UserError(_(
                            'Cannot change state of %s because it is in batch %s which is %s'
                        ) % (po.name, po.batch_id.name, po.batch_id.state))
        
        return super(PurchaseOrder, self).write(vals)