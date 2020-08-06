
import time
from odoo import api, fields, models
from odoo.addons.aos_common_report_header.report.report_xls import ReportXls
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

    
class AccountingReport(models.TransientModel):
    _inherit = "accounting.report"
    _description = "Accounting Report"
    
    date_from = fields.Date(string='Date From', default=lambda *a: time.strftime('%Y-01-01'))
    date_to = fields.Date(string='Date to', default=lambda *a: time.strftime('%Y-%m-%d'))
    
    flag = fields.Boolean(string='Include Zero Balance', default=True)
    multi_period = fields.Boolean(string='Multi Period', default=False)
    report_method  = fields.Selection([
        ('profit_loss', 'Profit & Loss'),
        ('balance', 'Balance'),
        ('none', 'None'),
        ], 'Report Method')
    strict_range = fields.Boolean('Strict Range Date')
    
    @api.multi
    @api.onchange('account_report_id')
    def onchange_account_report_id(self):
        values = {
            'report_method': 'none',
        }
        if self.account_report_id.report_method:
            values['report_method'] = self.account_report_id.report_method
        self.update(values)
    
    def _build_contexts(self, data):
        result = super(AccountingReport, self)._build_contexts(data)
        result['report_method'] = data['form']['report_method'] or 'none'
        result['strict_range'] = False if result['report_method'] == 'balance' else True
        #print "====_build_contexts===",result
        return result
    
    def _build_comparison_context(self, data):
        result = super(AccountingReport, self)._build_comparison_context(data)
        result['report_method'] = data['form']['report_method'] or 'none'
        if data['form']['filter_cmp'] == 'filter_date':
            result['date_from'] = data['form']['date_from_cmp']
            result['date_to'] = data['form']['date_to_cmp']
            result['strict_range'] = False if result['report_method'] == 'balance' else True
        #print "====_build_comparison_context===",result
        return result
    
    def _build_multiperiod_context(self, data):
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        result['report_method'] = data['form']['report_method'] or 'none'
        result['strict_range'] = False if result['report_method'] == 'balance' else True
        return result
    
    @api.multi
    def _action_excel(self, report_data, data):
        wb = xlwt.Workbook(encoding="utf-8")
        ws = wb.add_sheet((data['account_report_id'][1]))
        print('------------- xxxxxxxx -------------')
        print(report_data)
        print('------------- xxxxxxxx -------------')
        print(data)
        row_pos = 0
        # Column Title Row
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
        
        c_specs = [('report_name', 3, 0, 'text', report_name.upper())]
        row_data = ReportXls.xls_row_template(c_specs, [x[0] for x in c_specs])        
        row_pos = ReportXls.xls_write_row(ws, row_pos, row_data, row_style=cell_style_center)
        #header title
        title_name = data['account_report_id'][1]
        c_specs = [('title_name', 3, 0, 'text', title_name.upper())]
        row_data = ReportXls.xls_row_template(c_specs, [x[0] for x in c_specs])        
        row_pos = ReportXls.xls_write_row(ws, row_pos, row_data, row_style=cell_style_center)
        #for header date range
        c_specs = [('date_range', 3, 0, 'text', format_date(self.env, data['date_from']) + ' - ' + format_date(self.env, data['date_to'])),]
        row_data = ReportXls.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = ReportXls.xls_write_row(ws, row_pos, row_data, row_style=cell_style_center)
        # write empty row to define column sizes
        c_sizes = column_sizes
        c_specs = [('empty%s' % i, 1, c_sizes[i], 'text', None) for i in range(0, len(c_sizes))]
        row_data = ReportXls.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = ReportXls.xls_write_row(ws, row_pos, row_data, set_column_size=True)
         
        cell_format = _xs['bold']
        c_title_cell_style = xlwt.easyxf(cell_format, num_format_str='#,##0.00;(#,##0.00)')
        #ws.set_horz_split_pos(row_pos)
        row_pos += 1
        Parser = self.env['common.report.alpha']
        periods = Parser.get_periods(data)
        
        if not data['enable_filter'] and not data['debit_credit'] and not data['multi_period']:
            c_specs = [
                    ('cd', 1, 0, 'text', 'Code'),
                    ('nm', 1, 0, 'text', 'Name'),
                    ('bl', 1, 0, 'text', 'Balance'),
                ]
            row_data = ReportXls.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = ReportXls.xls_write_row(ws, row_pos, row_data, c_title_cell_style)
            ws.horz_split_pos = row_pos
            for account in Parser.get_lines(data):
                #print "aaaaa",account['code'],account#['report']
                style_font_xls = account['report']['style_font_xls']#_xs[line.financial_id.style_font_xls]
                color_font_xls = account['report']['color_font_xls']#_xs[line.financial_id.color_font_xls]
                color_fill_xls = account['report']['color_fill_xls']#_xs[line.financial_id.color_fill_xls]
                border_xls = account['report']['border_xls']#_xs[line.financial_id.border_xls]
                
                accounts = []
                for acc in account['account_ids']:
                    accounts.append(acc.code)
                    
                if account['code'] in accounts:
                    line_cell_style = xlwt.easyxf(num_format_str='#,##0.00;(#,##0.00)')
                else:
                    line_cell_style = xlwt.easyxf(_xs[style_font_xls] + _xs[color_font_xls] + _xs[color_fill_xls] + _xs[border_xls], num_format_str='#,##0.00;(#,##0.00)')
                if account['name'] == 'SPACE':
                    c_specs = [
                        ('code', 1, 0, 'text', ''),
                        ('name', 1, 0, 'text', ''),
                        ('balance', 1, 0, 'text', ''),
                    ]
                else:
                    c_specs = [
                        ('code', 1, 0, 'text', account['code'] or ''),
                        ('name', 1, 0, 'text', account['name'] not in ('TOTAL','SPACE') and '  '*account['level'] + account['name'] or ''),
                        ('balance', 1, 0, 'number', account['balance'] or 0.0),
                    ]
                #print "==account['balance']==",account['name'],account['balance']
                row_data = ReportXls.xls_row_template(c_specs, [x[0] for x in c_specs])
                row_pos = ReportXls.xls_write_row(ws, row_pos, row_data, line_cell_style)
        #if with debit & credit
        elif data['debit_credit'] and not data['multi_period']:
            c_specs = [
                    ('cd', 1, 0, 'text', 'Code'),
                    ('nm', 1, 0, 'text', 'Name'),
                    ('db', 1, 0, 'text', 'Debit'),
                    ('cr', 1, 0, 'text', 'Credit'),
                    ('bl', 1, 0, 'text', 'Balance'),
                ]
            row_data = ReportXls.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = ReportXls.xls_write_row(ws, row_pos, row_data, c_title_cell_style)
            ws.horz_split_pos = row_pos
            for account in Parser.get_lines(data):
                style_font_xls = account['report']['style_font_xls']#_xs[line.financial_id.style_font_xls]
                color_font_xls = account['report']['color_font_xls']#_xs[line.financial_id.color_font_xls]
                color_fill_xls = account['report']['color_fill_xls']#_xs[line.financial_id.color_fill_xls]
                border_xls = account['report']['border_xls']#_xs[line.financial_id.border_xls]
                
                accounts = []
                for acc in account['account_ids']:
                    accounts.append(acc.code)
                    
                if account['code'] in accounts:
                    line_cell_style = xlwt.easyxf(num_format_str='#,##0.00;(#,##0.00)')
                else:
                    line_cell_style = xlwt.easyxf(_xs[style_font_xls] + _xs[color_font_xls] + _xs[color_fill_xls] + _xs[border_xls], num_format_str='#,##0.00;(#,##0.00)')
                
                c_specs = [
                    ('code', 1, 0, 'text', account['name'] != 'SPACE' and account['code'] or ''),
                    ('name', 1, 0, 'text', account['name'] not in ('TOTAL','SPACE') and '  '*account['level'] + account['name'] or ''),
                    ('debit', 1, 0, 'number', account['name'] != 'SPACE' and '' or account['debit'] or 0.0),
                    ('credit', 1, 0, 'number', account['name'] != 'SPACE' and '' or account['credit'] or 0.0),
                    ('balance', 1, 0, 'number', account['name'] != 'SPACE' and '' or account['balance'] or 0.0),
                ]
                row_data = ReportXls.xls_row_template(c_specs, [x[0] for x in c_specs])
                row_pos = ReportXls.xls_write_row(ws, row_pos, row_data, line_cell_style)
        #if compare with other
        elif data['enable_filter'] and not data['debit_credit'] and not data['multi_period']:
            c_specs = [
                    ('cd', 1, 0, 'text', 'Code'),
                    ('nm', 1, 0, 'text', 'Name'),
                    ('bl', 1, 0, 'text', 'Balance'),
                    ('blcm', 1, 0, 'text', data['label_filter']),
                ]
            row_data = ReportXls.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = ReportXls.xls_write_row(ws, row_pos, row_data, c_title_cell_style)
            ws.horz_split_pos = row_pos
            for account in Parser.get_lines(data):
                style_font_xls = account['report']['style_font_xls']#_xs[line.financial_id.style_font_xls]
                color_font_xls = account['report']['color_font_xls']#_xs[line.financial_id.color_font_xls]
                color_fill_xls = account['report']['color_fill_xls']#_xs[line.financial_id.color_fill_xls]
                border_xls = account['report']['border_xls']#_xs[line.financial_id.border_xls]
                accounts = []
                for acc in account['account_ids']:
                    accounts.append(acc.code)
                    
                if account['code'] in accounts:
                    line_cell_style = xlwt.easyxf(num_format_str='#,##0.00;(#,##0.00)')
                else:
                    line_cell_style = xlwt.easyxf(_xs[style_font_xls] + _xs[color_font_xls] + _xs[color_fill_xls] + _xs[border_xls], num_format_str='#,##0.00;(#,##0.00)')
                
                c_specs = [
                    ('code', 1, 0, 'text', account['name'] != 'SPACE' and account['code'] or ''),
                    ('name', 1, 0, 'text', account['name'] not in ('TOTAL','SPACE') and '  '*account['level'] + account['name'] or ''),
                    ('balance', 1, 0, 'number', account['name'] != 'SPACE' and '' or account['balance'] or 0.0),
                    ('balance_cmp', 1, 0, 'number', account['name'] != 'SPACE' and '' or account['balance_cmp'] or 0.0),
                ]
                row_data = ReportXls.xls_row_template(c_specs, [x[0] for x in c_specs])
                row_pos = ReportXls.xls_write_row(ws, row_pos, row_data, line_cell_style)
        elif data['multi_period'] and not data['debit_credit']:
            c_specs = [('cd', 1, 0, 'text', 'Code'),
                       ('nm', 1, 0, 'text', 'Name')]
            for pbl in periods:
                c_specs += [('pbl%s'%str(pbl), 1, 0, 'text', '%s'%str(pbl))]
            if data['report_method'] != 'balance':
                c_specs += [('bl', 1, 0, 'text', 'TOTAL')]
            
            row_data = ReportXls.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = ReportXls.xls_write_row(ws, row_pos, row_data, c_title_cell_style)
            ws.horz_split_pos = row_pos
            for account in Parser.get_lines(data):
                style_font_xls = account['report']['style_font_xls']#_xs[line.financial_id.style_font_xls]
                color_font_xls = account['report']['color_font_xls']#_xs[line.financial_id.color_font_xls]
                color_fill_xls = account['report']['color_fill_xls']#_xs[line.financial_id.color_fill_xls]
                border_xls = account['report']['border_xls']#_xs[line.financial_id.border_xls]
                accounts = []
                for acc in account['account_ids']:
                    accounts.append(acc.code)
                    
                if account['code'] in accounts:
                    line_cell_style = xlwt.easyxf(num_format_str='#,##0.00;(#,##0.00)')
                else:
                    line_cell_style = xlwt.easyxf(_xs[style_font_xls] + _xs[color_font_xls] + _xs[color_fill_xls] + _xs[border_xls], num_format_str='#,##0.00;(#,##0.00)')
                
                c_specs = [
                    ('code', 1, 0, 'text', account['name'] != 'SPACE' and account['code'] or ''),
                    ('name', 1, 0, 'text', account['name'] not in ('TOTAL','SPACE') and '  '*account['level'] + account['name'] or ''),      
                ]
                for pbl in periods:
                    c_specs += [('balance_%s'%str(pbl), 1, 0, 'number', account['name'] != 'SPACE' and '' or account['balance_%s'%str(pbl)] or 0.0)]
                if data['report_method'] != 'balance':
                    c_specs += [('balance', 1, 0, 'number', account['name'] != 'SPACE' and '' or account['balance'] or 0.0)]
                row_data = ReportXls.xls_row_template(c_specs, [x[0] for x in c_specs])
                row_pos = ReportXls.xls_write_row(ws, row_pos, row_data, line_cell_style)
        
        file_data = io.BytesIO()
        wb.save(file_data)
        wiz_id = self.env['common.download.report.save'].create({
            'state': 'get',
            'data': base64.encodestring(file_data.getvalue()),
            'name': title_name+".xls"
        })
            
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
        context = self._context
        #print ("======xls_export======",context)
        if context.get('xls_export'):
            # we update form with display account value
            datas = {'ids': context.get('active_ids', [])}
            datas['model'] = 'accounting.report'
            datas['form'] = self.read(['date_from', 'date_to', 'strict_range', 'report_method', 'journal_ids', 
                                         'date_from_cmp', 'debit_credit', 'date_to_cmp', 'filter_cmp', 'account_report_id', 'enable_filter', 'label_filter', 'target_move', 
                                         'flag', 'multi_period',
                                        ])[0]
            used_context = self._build_contexts(datas)
            datas['form']['used_context'] = dict(used_context, lang=context.get('lang', 'en_US'))
            comparison_context = self._build_comparison_context(datas)
            datas['form']['comparison_context'] = comparison_context
            #FILTER DATE MULTI PERIOD
            multiperiod_context = self._build_multiperiod_context(datas)
            datas['form']['multiperiod_context'] = multiperiod_context
            report_data = self._print_report(datas)
            #print "====multiperiod_context===wizard===",multiperiod_context
            return self._action_excel(report_data, datas['form'])
    
    @api.multi
    def check_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'strict_range', 'report_method', 'journal_ids', 
                                         'date_from_cmp', 'debit_credit', 'date_to_cmp', 'filter_cmp', 'account_report_id', 'enable_filter', 'label_filter', 'target_move', 
                                         'flag', 'multi_period'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang', 'en_US'))
        return self._print_report(data)