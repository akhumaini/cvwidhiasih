# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Common Report Header',
    'version' : '11.0.0.1.0',
    'license': 'AGPL-3',
    'summary': 'Common Report Header for All Reports',
    'sequence': 1,
    "author": "Alphasoft",
    'description': """Common Report Header""",
    'category' : 'Accounting',
    'website': 'https://www.alphasoft.co.id/',
    'images':  ['images/main_screenshot.png'],
    'depends' : ['account'],
    'data': [
        #'wizard/account_financial_report_view.xml',
        'wizard/common_download_report_view.xml',
        'views/account_view.xml',
    ],
    'demo': [
        
    ],
    'qweb': [
        
    ],
    'price': 55.00,
    'currency': 'EUR',
    'installable': True,
    'application': False,
    'auto_install': False,
}
