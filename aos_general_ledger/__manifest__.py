# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'General Ledger Report XLSX',
    'version' : '10.0.0.1.0',
    'license': 'AGPL-3',
    'summary': 'General Ledger Report',
    'sequence': 1,
    "author": "Alphasoft",
    'description': """
This module is aim to add General Ledger report xlsx
    """,
    'category' : 'Accounting',
    'website': 'https://www.alphasoft.co.id/',
    'images' : ['static/description/main_screenshot.png'],
    'depends' : ['account',
                 'report_xlsx', 
                 'aos_common_report_header'
                ],
    'data': [
        'wizard/account_general_ledger_report_view.xml'
    ],
    'demo': [
        
    ],
    'qweb': [
        
    ],
    'price': 25.00,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
}
