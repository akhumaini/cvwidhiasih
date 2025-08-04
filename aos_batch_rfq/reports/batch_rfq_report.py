# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools


class BatchRfqReport(models.Model):
    _name = 'batch.rfq.report'
    _description = 'Batch RFQ Analysis'
    _auto = False
    _rec_name = 'batch_rfq_id'

    # Batch RFQ fields
    batch_rfq_id = fields.Many2one('batch.rfq', string='Batch RFQ', readonly=True)
    batch_rfq_name = fields.Char(string='Batch RFQ Number', readonly=True)
    batch_rfq_description = fields.Text(string='Description', readonly=True)
    user_id = fields.Many2one('res.users', string='Responsible', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    category_id = fields.Many2one('purchase.category', string='Category', readonly=True)
    
    # Dates
    date_created = fields.Datetime(string='Creation Date', readonly=True)
    date_deadline = fields.Datetime(string='Deadline', readonly=True)
    date_sent = fields.Datetime(string='Date Sent', readonly=True)
    date_completed = fields.Datetime(string='Date Completed', readonly=True)
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('sent', 'Sent'),
        ('partial', 'Partially Received'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', readonly=True)
    
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Very High')
    ], string='Priority', readonly=True)
    
    # Line fields
    partner_id = fields.Many2one('res.partner', string='Vendor', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    product_categ_id = fields.Many2one('product.category', string='Product Category', readonly=True)
    
    # Quantities and amounts
    product_qty = fields.Float(string='Quantity', readonly=True)
    estimated_price = fields.Float(string='Estimated Price', readonly=True)
    estimated_amount = fields.Monetary(string='Estimated Amount', readonly=True)
    vendor_quoted_price = fields.Float(string='Quoted Price', readonly=True)
    vendor_quoted_amount = fields.Monetary(string='Quoted Amount', readonly=True)
    price_variance = fields.Float(string='Price Variance (%)', readonly=True)
    
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)
    
    # Line status
    line_state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'RFQ Sent'),
        ('received', 'Quotation Received'),
        ('selected', 'Selected'),
        ('cancelled', 'Cancelled')
    ], string='Line Status', readonly=True)
    
    # Purchase Order fields
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order', readonly=True)
    po_state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='PO State', readonly=True)
    
    # Computed fields
    response_time = fields.Float(string='Response Time (Days)', readonly=True)
    is_overdue = fields.Boolean(string='Is Overdue', readonly=True)
    
    # Aggregated fields for reporting
    total_lines = fields.Integer(string='Total Lines', readonly=True)
    sent_lines = fields.Integer(string='Sent Lines', readonly=True)
    received_lines = fields.Integer(string='Received Lines', readonly=True)
    selected_lines = fields.Integer(string='Selected Lines', readonly=True)
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    row_number() OVER () AS id,
                    
                    -- Batch RFQ fields
                    br.id AS batch_rfq_id,
                    br.name AS batch_rfq_name,
                    br.description AS batch_rfq_description,
                    br.user_id,
                    br.company_id,
                    br.category_id,
                    br.date_created,
                    br.date_deadline,
                    br.date_sent,
                    br.date_completed,
                    br.state,
                    br.priority,
                    br.currency_id,
                    
                    -- Line fields
                    brl.partner_id,
                    brl.product_id,
                    pt.categ_id AS product_categ_id,
                    brl.product_qty,
                    brl.estimated_price,
                    brl.estimated_amount,
                    brl.vendor_quoted_price,
                    (brl.vendor_quoted_price * brl.product_qty) AS vendor_quoted_amount,
                    CASE 
                        WHEN brl.estimated_price > 0 THEN 
                            ((brl.vendor_quoted_price - brl.estimated_price) / brl.estimated_price) * 100
                        ELSE 0
                    END AS price_variance,
                    brl.state AS line_state,
                    
                    -- Purchase Order fields
                    brl.purchase_order_id,
                    po.state AS po_state,
                    
                    -- Computed fields
                    CASE 
                        WHEN brl.vendor_response_date IS NOT NULL AND br.date_sent IS NOT NULL THEN
                            EXTRACT(EPOCH FROM (brl.vendor_response_date - br.date_sent)) / 86400
                        ELSE NULL
                    END AS response_time,
                    
                    CASE 
                        WHEN brl.date_deadline < CURRENT_DATE 
                             AND brl.state NOT IN ('received', 'selected', 'cancelled') THEN TRUE
                        ELSE FALSE
                    END AS is_overdue,
                    
                    -- Aggregated fields (these will be the same for all lines of the same batch)
                    (SELECT COUNT(*) FROM batch_rfq_line WHERE batch_rfq_id = br.id) AS total_lines,
                    (SELECT COUNT(*) FROM batch_rfq_line WHERE batch_rfq_id = br.id AND state = 'sent') AS sent_lines,
                    (SELECT COUNT(*) FROM batch_rfq_line WHERE batch_rfq_id = br.id AND state = 'received') AS received_lines,
                    (SELECT COUNT(*) FROM batch_rfq_line WHERE batch_rfq_id = br.id AND state = 'selected') AS selected_lines
                    
                FROM batch_rfq br
                LEFT JOIN batch_rfq_line brl ON brl.batch_rfq_id = br.id
                LEFT JOIN product_product pp ON pp.id = brl.product_id
                LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
                LEFT JOIN purchase_order po ON po.id = brl.purchase_order_id
            )
        """ % self._table)