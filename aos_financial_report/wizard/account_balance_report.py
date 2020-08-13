import time
from odoo import api, fields, models, _
from odoo.addons.aos_common_report_header.report.report_xls import ReportXls
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang, format_date
#from __builtin__ import True
import logging
_logger = logging.getLogger(__name__)
from io import StringIO
import io

try:
    import xlwt
except ImportError:
    _logger.debug('Cannot `import xlwt`.')

try:
    import cStringIO
except ImportError:
    _logger.debug('Cannot `import cStringIO`.')

try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self
        
_column_sizes = [
    ('code', 18),
    ('name', 40), 
    ('jan', 18), 
    ('feb', 18), 
    ('mar', 18), 
    ('apr', 18), 
    ('mei', 18), 
    ('jun', 18), 
    ('jul', 18), 
    ('agt', 18), 
    ('sep', 18),   
    ('okt', 18), 
    ('nov', 18), 
    ('des', 18),   
    ('balance', 18),           
]

column_sizes = [x[1] for x in _column_sizes]
no_ind = 0

    
class AccountBalance(models.TransientModel):
    _inherit = "account.balance.report"
    _description = "Account Balance Report"
    
    
    def _get_accounts(self, accounts, display_account):
        """ compute the balance, debit and credit for the provided accounts
            :Arguments:
                `accounts`: list of accounts record,
                `display_account`: it's used to display either all accounts or those accounts which balance is > 0
            :Returns a list of dictionary of Accounts with following key and value
                `name`: Account name,
                `code`: Account code,
                `credit`: total amount of credit,
                `debit`: total amount of debit,
                `balance`: total amount of balance,
        """
 
        account_result = {}
        # Prepare sql query base on selected parameters from wizard
        tables, where_clause, where_params = self.env['account.move.line']._query_get()
        tables = tables.replace('"','')
        if not tables:
            tables = 'account_move_line'
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        # compute the balance, debit and credit for the provided accounts
        request = ("SELECT account_id AS id, SUM(debit) AS debit, SUM(credit) AS credit, (SUM(debit) - SUM(credit)) AS balance" +\
                   " FROM " + tables + " WHERE account_id IN %s " + filters + " GROUP BY account_id")
        params = (tuple(accounts.ids),) + tuple(where_params)
        self.env.cr.execute(request, params)
        for row in self.env.cr.dictfetchall():
            account_result[row.pop('id')] = row
 
        account_res = []
        for account in accounts:
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res['code'] = account.code
            res['name'] = account.name
            if account.id in account_result:
                res['debit'] = account_result[account.id].get('debit')
                res['credit'] = account_result[account.id].get('credit')
                res['balance'] = account_result[account.id].get('balance')
            if display_account == 'all':
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(res['balance']):
                account_res.append(res)
            if display_account == 'movement' and (not currency.is_zero(res['debit']) or not currency.is_zero(res['credit'])):
                account_res.append(res)
        return account_res
    
    @api.multi
    def _action_excel(self, report_data, data):
#         print("xxxxxxxxxxxxxxxx")
#         print(report_data)
#         print("xxxxxxxxxxxxxxxx11")
#         print(data)
        wb = xlwt.Workbook(encoding="utf-8")
        ws = wb.add_sheet('Trial Balance')
        row_pos = 0
#         # Column Title Row
        ws.panes_frozen = True
        ws.remove_splits = True
        # set print header/footer
        #self.parser_instance = self.parser(self.env.cr, self.env.uid, self.name2, self.env.context)
        _xs = ReportXls.xls_styles
        _p = self.env.user
        #_p = AttrDict(self.parser_instance.localcontext)
        cell_format = _xs['bold']
        cell_style = xlwt.easyxf(_xs['xls_title'])
        cell_style_center = xlwt.easyxf(cell_format + _xs['center'])
        cell_style_left = xlwt.easyxf(cell_format + _xs['left'])
        report_name = _p.company_id.partner_id.name
#         
        c_specs = [('report_name', 5, 0, 'text', report_name.upper())]
        row_data = ReportXls.xls_row_template(c_specs, [x[0] for x in c_specs])        
        row_pos = ReportXls.xls_write_row(ws, row_pos, row_data, row_style=cell_style_center)
        #header title
        title_name = report_data['name']
        c_specs = [('title_name', 5, 0, 'text', title_name.upper())]
        row_data = ReportXls.xls_row_template(c_specs, [x[0] for x in c_specs])        
        row_pos = ReportXls.xls_write_row(ws, row_pos, row_data, row_style=cell_style_center)
        #for header date range
        date_form = report_data['data']['form']['date_from']
        date_to = report_data['data']['form']['date_to']
        c_specs = [('date_range', 5, 0, 'text', format_date(self.env, date_form) + ' - ' + format_date(self.env, date_to)),]
        row_data = ReportXls.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = ReportXls.xls_write_row(ws, row_pos, row_data, row_style=cell_style_center)
        # write empty row to define column sizes
        c_sizes = column_sizes
        c_specs = [('empty%s' % i, 1, c_sizes[i], 'text', None) for i in range(0, len(c_sizes))]
        row_data = ReportXls.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = ReportXls.xls_write_row(ws, row_pos, row_data, set_column_size=True)
        
        cell_format = _xs['bold']
        c_title_cell_style = xlwt.easyxf(cell_format, num_format_str='#,##0.00;(#,##0.00)')
        line_cell_style = xlwt.easyxf(num_format_str='#,##0.00;(#,##0.00)')
        
        c_specs = [
                    ('cd', 1, 0, 'text', 'Code'),
                    ('nm', 1, 0, 'text', 'Account'),
                    ('db', 1, 0, 'text', 'Debit'),
                    ('cr', 1, 0, 'text', 'Credit'),
                    ('bl', 1, 0, 'text', 'Balance'),
                ]
        row_data = ReportXls.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = ReportXls.xls_write_row(ws, row_pos, row_data, c_title_cell_style)
        ws.horz_split_pos = row_pos

        for account in data:
            c_specs = [
                    ('code', 1, 0, 'text', account['code'] or ''),
                    ('name', 1, 0, 'text', account['name'] or ''),
                    ('debit', 1, 0, 'number', account['debit'] or 0.0),
                    ('credit', 1, 0, 'number', account['credit'] or 0.0),
                    ('balance', 1, 0, 'number', account['balance'] or 0.0),
                ]
            row_data = ReportXls.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = ReportXls.xls_write_row(ws, row_pos, row_data, line_cell_style)
            
        file_data = io.BytesIO()
        wb.save(file_data)
        wiz_id = self.env['common.download.report.save'].create({
            'state': 'get',
            'data': base64.encodestring(file_data.getvalue()),
            'name': title_name+".xls"
        })
#             
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
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
        report_data = self.with_context(discard_logo_check=True)._print_report(data)
#         Get data ACCOUNT with Value
        self.model = self.env.context.get('active_model', 'account.balance.report')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        display_account = data['form'].get('display_account')
        accounts = docs if self.model == 'account.account' else self.env['account.account'].search([])
        account_res = self.with_context(data['form'].get('used_context'))._get_accounts(accounts, display_account)
        
        return self._action_excel(report_data, account_res)

    
    



