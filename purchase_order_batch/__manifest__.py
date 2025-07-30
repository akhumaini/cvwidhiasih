{
    'name': 'Purchase Order Batch',
    'version': '16.0.1.0.0',
    'category': 'Purchase',
    'summary': 'Batch multiple Purchase Orders for efficient processing',
    'description': """
Purchase Order Batch Management
===============================

This module allows you to:
* Group multiple Purchase Orders into batches
* Process multiple POs together
* Track batch status and progress
* Generate batch reports
* Manage batch approvals

Similar to batch transfer functionality but for Purchase Orders.
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': [
        'base',
        'purchase',
        'stock',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/purchase_batch_security.xml',
        'data/purchase_batch_sequence.xml',
        'views/purchase_order_batch_views.xml',
        'views/purchase_order_views.xml',
        'wizards/purchase_batch_wizard_views.xml',
        'views/purchase_order_batch_menu.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}