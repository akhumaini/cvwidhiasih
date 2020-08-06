# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Financial Report XLS',
    'version' : '11.0.0.1.0',
    'license': 'AGPL-3',
    'summary': 'Financial Report for Balance Sheet and Profit and Loss',
    'sequence': 1,
    "author": "Alphasoft",
    'description': """
This module is aim to add balance sheet & profit loss xls
    """,
    'category' : 'Accounting',
    'website': 'https://www.alphasoft.co.id/',
    'images':  ['images/main_screenshot.png'],
    'depends' : ['account', 'aos_common_report_header'],
    'data': [
        'wizard/account_balance_report_view.xml',
        'wizard/account_financial_report_view.xml',
        'views/report_financial.xml',
    ],
    'demo': [
        
    ],
    'qweb': [
        
    ],
    'price': 25.00,
    'currency': 'EUR',
    'installable': True,
    'application': False,
    'auto_install': False,
}
