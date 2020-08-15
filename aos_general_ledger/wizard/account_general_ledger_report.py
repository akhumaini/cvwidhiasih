# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi, Guewen Baconnier
#    Copyright Camptocamp SA 2011
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang, format_date

import logging
_logger = logging.getLogger(__name__)

try:
    import xlsxwriter
except ImportError:
    _logger.debug('Can not import xlsxwriter`.')

from io import StringIO
import io

try:
    import cStringIO
except ImportError:
    _logger.debug('Cannot `import cStringIO`.')

try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')


class AccountReportGeneralLedger(models.TransientModel):
    _inherit = "account.report.general.ledger"
    _description = "General Ledger Report"
    
    initial_balance = fields.Boolean(string='Include Initial Balances', default=True,
                                    help='If you selected date, this field allow you to add a row to display the amount of debit/credit/balance that precedes the filter you\'ve set.')
    amount_currency = fields.Boolean(string='With Currency', default=False, help="It adds the currency column")
    display_type = fields.Selection([('all','All'), ('split','Split into Sheet')], 
                                        string='Display Type', required=False, default='all') 
    account_id = fields.Many2one('account.account', string='Filter on Accounts', help="""Only selected accounts will be printed. Leave empty to print all accounts.""")
    analytic_account_ids = fields.Many2many('account.analytic.account', 'account_report_general_ledger_analytic_rel', 'account_id', 'analytic_account_id', string='Analytic Account', required=False)
    
    def _print_report1(self, data):
        data = self.pre_print_report(data)
        data.update(self.read(['sortby', 'initial_balance', 'amount_currency', 'account_id', 'display_type', 'analytic_account_ids'])[0])
        records = self.env[data['model']].browse(data.get('ids', []))
        return self.env.ref('account.action_report_general_ledger').with_context(landscape=True).report_action(records, data=data)

    def _build_contexts(self, data):
        result = super(AccountReportGeneralLedger, self)._build_contexts(data)
        result['analytic_account_ids'] = 'analytic_account_ids' in data and data['analytic_account_ids'] or False
        return result
    
    @api.multi
    def _action_excel(self, report_data, data):
        file_data = io.BytesIO()
        wb = xlsxwriter.Workbook(file_data)
        _p = self.env.user
        Parser = self.env['common.report.alpha']
        if data['display_type'] == 'split':
            title_style = wb.add_format({'bold': True, 'color': 'FF000000', 'size': 12})
            header_style = wb.add_format({'bold': True, 'color': 'FF000000', 'size': 10})
            account_style = wb.add_format({'bold': True, 'num_format':'#,##0.00;(#,##0.00)', 'size': 10})
            line_style = wb.add_format({'bold': False, 'num_format':'#,##0.00;(#,##0.00)', 'size': 10})
            for account in Parser.get_accounts(data, data['used_context']):
                ws = wb.add_worksheet(account['code'])  
                ws.write(0,3,account['name'].upper(), title_style)  
                ws.write(1,3,'GENERAL LEDGER', title_style)  
                #ws.write(1,3, account['parent_id'] and account['parent_id']['code'], title_style)
                #ws.write(2,3, account['parent_id'] and account['parent_id']['name'], title_style)                
                ws.write(2,2,'UNTUK PERIODE : BULAN '+ format_date(self.env, data['date_from']) +' - '+ format_date(self.env, data['date_to']), title_style)
                #ws.write(4,5,'TAHUN '+ self._display_fiscalyear(parser, data), title_style)
                   
                #Tanggal    No Voucher    Keterangan    Debet    Kredit    Saldo
                ws.write(4,0,'Nama Akun',header_style)
                ws.write(4,1,account['name'],header_style)
                ws.write(5,0,'Induk Akun',header_style)
                #ws.write(5,1,account['parent_id'] and account['parent_id']['name'],header_style)
                ws.write(6,0,'No Akun',header_style)
                ws.write(6,1,account['code'],header_style)
                ws.freeze_panes(8,0)
                
                ws.write(8,0,'Tanggal',header_style)
                ws.write(8,1,'No Voucher',header_style)
                ws.write(8,2,'Keterangan',header_style)
                ws.write(8,3,'Debet',header_style)
                ws.write(8,4,'Kredit',header_style)
                ws.write(8,5,'Saldo',header_style)
                row_count = 9
                for line in account['move_lines']:
                    ws.write(row_count,0,format_date(self.env, line['ldate']),line_style)
                    ws.write(row_count,1,line['move_name'],line_style)
                    ws.write(row_count,2,line['lname'],line_style)
                    ws.write(row_count,3,line['debit'],line_style)
                    ws.write(row_count,4,line['credit'],line_style)
                    ws.write(row_count,5,line['balance'],line_style)
                    row_count += 1
        #this is on one sheet                            
        elif data['display_type'] == 'all':
            ws = wb.add_worksheet('General Ledger')
            ws.freeze_panes(6,0)
            ws.fit_width_to_pages = 1
            row_count = 6
            ws.horz_split_pos = row_count
    
            title_style = wb.add_format({'bold': True, 'color': 'FF000000', 'size': 12})
            header_style = wb.add_format({'bold': True, 'color': 'FF000000', 'size': 10})
            account_style = wb.add_format({'bold': True, 'num_format':'#,##0.00;(#,##0.00)', 'size': 10})
            line_style = wb.add_format({'bold': False, 'num_format':'#,##0.00;(#,##0.00)', 'size': 10})
            
            #ws.write(basis(angka), kolom(abjad))
            ws.write(0,0,'GENERAL LEDGER', title_style)
            ws.write(2,0,'%s - %s' % (format_date(self.env, data['date_from']),format_date(self.env, data['date_to'])), title_style)       
            ws.write(4,0,'Account Code',header_style)
            ws.write(4,1,'Account Name',header_style)
            ws.write(4,6,'Debit',header_style)
            ws.write(4,7,'Credit',header_style)
            ws.write(4,8,'Balance',header_style)
              
            ws.write(5,0,'Date',header_style)
            ws.write(5,1,'Journal',header_style)
            ws.write(5,2,'Partner Name',header_style)
            ws.write(5,3,'Ref.',header_style)
            ws.write(5,4,'Move',header_style)
            ws.write(5,5,'Entry Label',header_style)
            ws.write(5,6,'Debit',header_style)
            ws.write(5,7,'Credit',header_style)                
            ws.write(5,8,'Balance',header_style)
            if data['amount_currency']:
                ws.write(5,9,'Currency', header_style)
                ws.write(5,10,'Symbol', header_style)
     
            for account in Parser.get_accounts(data, data['used_context']):
                ws.write(row_count,0,'%s' % account['code'], account_style)
                ws.write(row_count,1,'%s' % account['name'], account_style)
                ws.write(row_count,6,account['debit'], account_style)
                ws.write(row_count,7,account['credit'], account_style)
                ws.write(row_count,8,account['balance'], account_style)
                row_count += 1
                for line in account['move_lines']:
                    ws.write(row_count,0,format_date(self.env, line['ldate']),line_style)
                    ws.write(row_count,1,line['lcode'],line_style)
                    ws.write(row_count,2,line['partner_name'],line_style)
                    ws.write(row_count,3,line['lref'],line_style)
                    ws.write(row_count,4,line['move_name'],line_style)
                    ws.write(row_count,5,line['lname'],line_style)
                    ws.write(row_count,6,line['debit'],line_style)
                    ws.write(row_count,7,line['credit'],line_style)
                    ws.write(row_count,8,line['balance'],line_style)
                    if data['amount_currency'] and (line['amount_currency'] is not None and line['amount_currency'] > 0.0):
                        ws.write(row_count,9,line['amount_currency'],line_style)
                        ws.write(row_count,10,line['currency_code'],line_style)
                    row_count += 1
                row_count += 1
        wb.close()
        file_data.seek(0)
        wiz_id = self.env['common.download.report.save'].create({
            'state': 'get',
            'data': base64.encodestring(file_data.read()),
            'name': 'General Ledger.xls'
        })
        #print ('--wiz_id--',wiz_id)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Download Report',
            'res_model': 'common.download.report.save',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': wiz_id.id,
            'target': 'new'
        }
    
    @api.multi
    def xls_export(self):
        #print "======xls_export======",ids
        context = self._context
        if context.get('xls_export'):
            # we update form with display account value
            datas = {'ids': context.get('active_ids', [])}
            datas['model'] = 'account.report.general.ledger'
            datas['form'] = self.read()[0]
            used_context = self._build_contexts(datas)
            datas['form']['used_context'] = dict(used_context, lang=context.get('lang', 'en_US'))
            report_data = self._print_report1(datas)
            #print "====multiperiod_context===wizard===",multiperiod_context
            return self._action_excel(report_data, datas['form'])