##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

#from odoo.report import report_sxw
from odoo.tools.translate import _
from odoo import api, models, _
#from common_report_header import common_report_header
from odoo.addons.aos_common_report_header.report.common_report_header import common_report_header
from odoo.api import Environment


class CommonReportAlpha(models.TransientModel, common_report_header):
    _name = 'common.report.alpha'
    
    def get_periods(self, data):
        period_ids = []
        if data['used_context'].get('date_from') and data['used_context'].get('date_to'):
            ds = datetime.strptime(data['used_context'].get('date_from'), '%Y-%m-%d')
            while ds.strftime('%Y-%m-%d')<data['used_context'].get('date_to'):
                de = ds + relativedelta(months=1, days=-1)
                if de.strftime('%Y-%m-%d')>data['used_context'].get('date_to'):
                    de = datetime.strptime(data['used_context'].get('date_to'), '%Y-%m-%d')
                period_ids.append(ds.strftime('%b-%Y'))
                ds = ds + relativedelta(months=1)
        return period_ids
    
    def get_lines(self, data):
        #print "get_lines------------->>",data['date_from']#, self.get_account_lines
        lines = []
        #self.env = Environment(self.cr, self.uid, self.context)
        account_obj = self.env['account.account']
        currency_obj = self.env['res.currency']
        financial_obj = self.env['account.financial.report']
        account_report = financial_obj.browse(data['account_report_id'][0])
        child_reports = account_report._get_children_by_order()
        #print "---child_reports---",child_reports
        #ADD THIS FUNCTION TO MAKE HIRARCY
        childs = []
        childs_report_method = []
        for child in child_reports:
            childs.append(child.id)
            childs_report_method.append(child.report_method)
        child_ids = financial_obj.search([('id', 'in', childs)], order='sequence, code asc')
        #print "=----child_ids----==",child_ids
        #context.update(data.get('used_context'))
        #child_reports = financial_obj.browse(child_ids)
        #print "==child_reports===",child_reports
        res = self._compute_report_balance(child_ids, context=data['used_context'])
        #res = self.with_context(data.get('used_context'))._compute_report_balance(child_reports)
        #print "===res====",res
        #res = self.with_context(data.get('used_context'))._compute_report_balance(child_reports)
        if data['enable_filter'] and not data['multi_period']:
            comparison_res = self._compute_report_balance(child_reports, context=data['comparison_context'])
            for report_id, value in comparison_res.items():
                res[report_id]['comp_bal'] = value['balance']
                report_acc = res[report_id].get('account')
                #print "====res[report_id]====",res[report_id]
                if report_acc:
                    for account_id, val in comparison_res[report_id].get('account').items():
                        #print "===account_id==",account_id,val
                        report_acc[account_id]['comp_bal'] = val['balance']
        multiperiod_res = {}  
        filter_periods = []     
        if data['enable_filter'] and data['multi_period']:
            #print "===multiperiod_res_01==",data['used_context'].get('date_from')
            if data['used_context'].get('date_from') and data['used_context'].get('date_to'):
                date_start = data['used_context'].get('date_from')
                date_end = data['used_context'].get('date_to')
                ds = datetime.strptime(date_start, '%Y-%m-%d')
                while ds.strftime('%Y-%m-%d')<date_end:
                    de = ds + relativedelta(months=1, days=-1)
                    if de.strftime('%Y-%m-%d')>date_end:
                        de = datetime.strptime(date_end, '%Y-%m-%d')
                    filter_periods.append(ds.strftime('%b-%Y'))
                    #create loop monthly here
                    #print "=====----======",childs,childs_report_method,data['multiperiod_context']['strict_range']# = False if result['report_method'] == 'balance' else True
                    if 'balance' in childs_report_method:
                        data['multiperiod_context'].update({'date_from': False, 'date_to': de.strftime('%Y-%m-%d')})
                    else:
                        data['multiperiod_context'].update({'date_from': ds.strftime('%Y-%m-%d'), 'date_to': de.strftime('%Y-%m-%d')})
                    multiperiod_res = self._compute_report_balance(child_reports, context=data['multiperiod_context'])
                    #print "====multiperiod_res====",multiperiod_res
                    for report_id, value in multiperiod_res.items():
                        res[report_id]['comp_bal_%s'%str(ds.strftime('%b-%Y'))] = value['balance']
                        report_acc = res[report_id].get('account')
                        #print "====res===>>>>",res[report_id]
                        if report_acc:
                            for account_id, val in multiperiod_res[report_id].get('account').items():
                                #print "===account_id==",account_id,val
                                report_acc[account_id]['comp_bal_%s'%str(ds.strftime('%b-%Y'))] = val['balance']
                    #========================
                    ds = ds + relativedelta(months=1)
        #print "----filter_periods----",filter_periods
        for report in child_reports:
            if report.parent_id:
                #print "==report==",report.code
                report_balance = res[report.id]['balance']
                vals = {
                    'report':report,
                    'code': report.code,
                    'name': report.name,
                    'balance': report_balance * report.sign,#res[report.id]['balance'] * report.sign,
                    'type': 'report',
                    'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                    'account_type': report.type =='sum' and 'view' or False, #used to underline the financial report balances
                    'account_ids': report.account_ids,
                }
                #print "===report_balance===",report.code,report_balance
                if data['debit_credit']:
                    vals['debit'] = res[report.id]['debit']
                    vals['credit'] = res[report.id]['credit']
                if data['enable_filter'] and not data['multi_period']:
                    vals['balance_cmp'] = res[report.id]['comp_bal'] * report.sign#self.pool.get('account.financial.report').browse(self.cr, self.uid, report.id, context=data['comparison_context']).balance * report.sign or 0.0
                if data['enable_filter'] and data['multi_period']:
                    vals['filter_periods'] = filter_periods
                    for period in filter_periods:
                        vals['balance_%s'%str(period)] = res[report.id]['comp_bal_%s'%str(period)] * report.sign
                lines.append(vals)
                account_ids = []
                #print "==vals=",report.display_detail,vals
                if report.display_detail == 'no_detail':
                    #the rest of the loop is used to display the details of the financial report, so it's not needed here.
                    continue
                #print "---res[report.id].get('account')----",res[report.id]['account'].items()
                if res[report.id].get('account'):
                    for account_id, value in res[report.id]['account'].items():#[(1127, {'credit': 0.0, 'balance': 0.0, 'debit': 0.0}), (1128, {'credit': 0.0, 'balance': 0.0, 'debit': 0.0}), (1129, {'credit': 0.0, 'balance': 0.0, 'debit': 0.0})]:#res[report.id]['account'].items():
                        #if there are accounts to display, we add them to the lines with a level equals to their level in
                        #the COA + 1 (to avoid having them with a too low level that would conflicts with the level of data
                        #financial reports for Assets, liabilities...)
                        #flag = False
                        #print "===data====",data['flag']
                        flag = data['flag']
                        account = self.env['account.account'].browse(account_id)
                        #compute_fiscalyear_dates(date)
                        #days = (account.company_id.compute_fiscalyear_dates(depreciation_date)['date_to'] - depreciation_date).days + 1
                        #days = account.company_id.compute_fiscalyear_dates(data['date_from'])
                        #print "===days===",days
                        #print '===account===',account,account.name,account.code,account.parent_left
                        value_balance = value['balance']
                        vals = {
                            'report':report,
                            'code': account.code,
                            'name': account.name,
                            'balance': value_balance * report.sign or 0.0,#value['balance'] * report.sign or 0.0,
                            'type': 'account',
                            'level': report.account_ids and report.child_level or 5,
                            'account_type': account.internal_type,
                            'account_ids': report.account_ids,
                        }
                        #print "===vals====",vals
                        if data['debit_credit']:
                            vals['debit'] = value['debit']
                            vals['credit'] = value['credit']
                            if not account.company_id.currency_id.is_zero(vals['debit']) or not account.company_id.currency_id.is_zero(vals['credit']):
                                flag = True
                        if not account.company_id.currency_id.is_zero(vals['balance']):
                            flag = True
                        if data['enable_filter'] and not data['multi_period']:
                            vals['balance_cmp'] = value['comp_bal'] * report.sign
                            if not account.company_id.currency_id.is_zero(vals['balance_cmp']):
                                flag = True
                        if data['enable_filter'] and data['multi_period']:
                            vals['filter_periods'] = filter_periods
                            for period in filter_periods:
                                vals['balance_%s'%str(period)] = value['comp_bal_%s'%str(period)] * report.sign
                        if flag:
                            lines.append(vals)
        return lines
    
    def get_accounts(self, data, context=None):
        #print "get_general_ledger",data
        lines = []
        #self.env = Environment(self.cr, self.uid, self.context)
        #self.model = self.context.get('active_model')
        #docs = self.env[self.model].browse(self.context.get('active_id'))
        #print "docs",docs
        init_balance = data.get('initial_balance', True)
        sortby = data.get('sortby', 'sort_date')
        display_account = data['display_account']
        codes = []
        if data.get('journal_ids', False):
            codes = [journal.code for journal in self.env['account.journal'].browse(data['journal_ids'])]
        if not data['account_id']:
            accounts = self.env['account.account'].search([])
        else:
            accounts = self.env['account.account'].search([('id','in',[data['account_id'][0]])])
        #print ('===account_ids===',account_ids)
        #accounts = self.env['account.account'].browse(account_ids)
        #accounts = self.env['account.account'].search([])
        accounts_res = self.with_context(data.get('used_context',{}))._get_account_move_entry(accounts, init_balance, sortby, display_account)
        #accounts_res = self._get_account_move_entry(accounts, init_balance, sortby, display_account, context=context)
        #accounts_res = self._get_account_move_entry(accounts, init_balance, sortby, display_account)
        return accounts_res
    
    
    def get_salesperson(self, data):
        user_ids = []
#         self.env = Environment(self.cr, self.uid, self.context)
#         target_move = data.get('target_move', 'all')
        date_from = data.get('date_from', time.strftime('%Y-%m-%d'))
# 
        if data['result_selection'] == 'customer':
            account_type = ['receivable']
        elif data['result_selection'] == 'supplier':
            account_type = ['payable']
        else:
            account_type = ['payable','receivable']
            
        user_ids = self._get_salesperson(account_type, date_from)
        return self.env['res.users'].browse(user_ids)
    
    def get_partner(self, data):
        partner_ids = []
#         self.env = Environment(self.cr, self.uid, self.context)
        target_move = data.get('target_move', 'all')
        date_from = data.get('date_from', time.strftime('%Y-%m-%d'))

        if data['result_selection'] == 'customer':
            account_type = ['receivable']
        elif data['result_selection'] == 'supplier':
            account_type = ['payable']
        else:
            account_type = ['payable','receivable']
            
        partner_ids = self._get_partner(data, account_type, date_from, target_move)
        return self.env['res.partner'].browse(partner_ids)
    
    def get_data(self, partner, user_id, data):
        #print "===get_data===",partner
#         self.env = Environment(self.cr, self.uid, self.context)
        self.total_account = []
        #self.model = self.context.get('active_model')
        #docs = self.env[self.model].browse(self.context.get('active_id'))
        
        target_move = data.get('target_move', 'all')
        date_from = data.get('date_from', time.strftime('%Y-%m-%d'))

        if data['result_selection'] == 'customer':
            account_type = ['receivable']
        elif data['result_selection'] == 'supplier':
            account_type = ['payable']
        else:
            account_type = ['payable','receivable']

        without_partner_movelines = self._get_move_lines_with_out_partner(partner, user_id, data, account_type, date_from, target_move)
        tot_list = self.total_account
        partner_movelines = self._get_partner_move_lines(partner, user_id, data, account_type, date_from, target_move)
        #print "====partner_movelines====",partner_movelines
#         for i in range(7):
#             self.total_account[i] += tot_list[i]
        movelines = partner_movelines + without_partner_movelines
        docargs = {
            'get_partner_lines': movelines,
            'get_direction': self.total_account,
        }
        return docargs
    
    #===========================================================================
    # CASH & BANK
    #===========================================================================
    def get_bank_accounts(self, data):
        accounts = self.env['account.journal'].search([('default_debit_account_id','=',data['journal_id'])])
        accounts_res = self._get_account_move_init_balance(data, accounts, True, 'sort_date', 'all', 'bankbook_account')
        return accounts_res
    
    def get_liquidity_accounts(self, data):
        #self.env = Environment(self.cr, self.uid, self.context)
        lines = []
        init_balance = True
        sortby = 'sort_date'
        display_account = 'all'
        daily_ids = data['daily_cashbank_ids']
        account_ids = self._get_account_daily_report(daily_ids, 'cashbank')
        accounts = self.env['account.account'].browse(account_ids)
        accounts_res = []
        accounts_res = self._get_account_move_init_balance(data, accounts, init_balance, sortby, display_account, 'cashbank_account')
        #print "=accounts_res==",accounts_res
        return accounts_res
    
    def get_liquidity_lines(self, data, account_init, account_sum):
        accounts_lines = self._get_account_move_counter_part(data, account_init, account_sum)
        return accounts_lines
    
    def get_cashflow_lines(self, data, lines):
        #self.env = Environment(self.cr, self.uid, self.context)
        accounts_lines = self._get_account_cashflow_report_line(data, lines)
        return accounts_lines
    
    def get_cashflow_accounts(self, data, account_ids):
        #self.env = Environment(self.cr, self.uid, self.context)
        init_balance = True
        sortby = 'sort_date'
        display_account = 'all'
        accounts_res = []
        if account_ids:
            accounts = self.env['account.account'].browse(account_ids)
            accounts_res = self._get_account_move_init_balance(data, accounts, init_balance, sortby, display_account, 'cashflow_account')
        return accounts_res
    
    def get_cashflow_details(self, data, account_init, account_sum):
        accounts_lines = self._get_account_move_counter_part(data, account_init, account_sum)
        return accounts_lines
    
    def get_cashflow_totals(self, data, account_init, account_sum):
        accounts_lines = self._get_account_move_counter_part(data, account_init, account_sum)
        return accounts_lines
    
    def get_cashflow_balance(self, report, context={}):
        #self.env = Environment(self.cr, self.uid, self.context)
        financial_obj = self.env['account.financial.report']
        account_report = financial_obj.browse(report)
        child_reports = account_report._get_children_by_order()
        res = self._compute_report_balance(child_reports, context=context)
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
