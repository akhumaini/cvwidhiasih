{
    'name': 'Batch RFQ Management',
    'summary': """
        Batch Request for Quotation Management System
        """,
    'version': '1.0.0',
    'category': 'Purchase',
    'author': 'La Jayuhni Yarsyah',
    'description': """
        Batch RFQ Management System
        ===========================
        
        This module allows you to:
        * Create and manage batch RFQs
        * Process multiple RFQs at once
        * Track batch RFQ status and progress
        * Generate batch reports
        * Automate RFQ workflows
        
        Similar to batch transfer concept but for Request for Quotations.
    """,
    'depends': [
        'base',
        'purchase',
        'stock',
        'sale_management',
        'account',
        'report_xlsx',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        
        'data/sequence.xml',
        'data/mail_template.xml',
        
        'views/batch_rfq_views.xml',
        'views/batch_rfq_line_views.xml',
        'views/purchase_order_views.xml',
        'views/menu_views.xml',
        
        'wizard/batch_rfq_wizard_views.xml',
        'wizard/batch_rfq_send_wizard_views.xml',
        
        'reports/batch_rfq_reports.xml',
        'reports/templates/batch_rfq_template.xml',
    ],
    'demo': [
        'demo/batch_rfq_demo.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}