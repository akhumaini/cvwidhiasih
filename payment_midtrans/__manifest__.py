{
    'name': 'Payment Acquirer: Midtrans',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Payment Acquirers',
    'summary': 'Payment Acquirer: Midtrans Implementation',
    'description': """
    Midtrans Payment Acquirer
    =========================
    
    This module allows you to accept online payments using Midtrans payment gateway.
    
    Features:
    - Support for Snap payment method
    - Automatic payment confirmation
    - Multi-currency support
    - Sandbox and production environment
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['payment'],
    'data': [
        'security/ir.model.access.csv',
        'views/payment_midtrans_templates.xml',
        'views/payment_provider_views.xml',
        'data/payment_provider_data.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_midtrans/static/src/js/payment_form.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}