{
    'name': 'Product Dimension Cartoon',
    'summary': """
        Product Dimension Cartoon
        """,
    'version': '0.0.1',
    'category': 'inventory',
    'author': 'La Jayuhni Yarsyah',
    'description': """
        Add scale on product
    """,
    'depends': [
        'stock','purchase','sale_management','sales_team','account','report_xlsx',
    ],
    'data': [
        'data/paper_format_landscape.xml',
        'views/port.xml',
        'views/journal.xml',
        'views/product.xml',
        'views/partner.xml',
        'views/sale.xml',
        'views/invoice.xml',
        'views/purchase.xml',

        'reports/reports.xml',

        'security/ir.model.access.csv',
        

        'reports/template/sale_order.xml',
        'reports/template/account_invoice.xml',
        'reports/template/purchase_order.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True
}