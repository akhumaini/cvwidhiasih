# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools.translate import _
from odoo import api, models

from odoo.tools import float_is_zero
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import pprint

_mapping_periods = {
        '0': _('Opening'),
        '1': _(datetime(1900, int(1), 1).strftime('%B')),
        '2': _(datetime(1900, int(2), 1).strftime('%B')),
        '3': _(datetime(1900, int(3), 1).strftime('%B')),
        '4': _(datetime(1900, int(4), 1).strftime('%B')),
        '5': _(datetime(1900, int(5), 1).strftime('%B')),
        '6': _(datetime(1900, int(6), 1).strftime('%B')),
        '7': _(datetime(1900, int(7), 1).strftime('%B')),
        '8': _(datetime(1900, int(8), 1).strftime('%B')),
        '9': _(datetime(1900, int(9), 1).strftime('%B')),
        '10': _(datetime(1900, int(10), 1).strftime('%B')),
        '11': _(datetime(1900, int(11), 1).strftime('%B')),
        '12': _(datetime(1900, int(12), 1).strftime('%B')),
    }
# Mixin to use with rml_parse, so self.pool will be defined.
class common_report_header(object):
    #LAST DAY OF MONTH
    def _last_day_of_month(self, any_day):
        next_month = any_day.replace(day=28) + timedelta(days=4)  # this will never fail
        return next_month - timedelta(days=next_month.day)
    #FOR FU AR
    def get_outstanding(self, data, objects):
        cr = self.env.cr
        uid = self.env.uid
        qq=''
        start_date = data['start_date']
        end_date = data['end_date']
        if data['account_ids']:
            qq ="and aa in "+str(tuple(data['account_ids']))
            qq ="and aa in "+str(tuple(data['account_ids']))
        query="""select dummy3.name,dummy3.number1,dummy3.balance1,dummy4.number2,dummy4.balance2
            from
            (select dummy.name,count(dummy.partner_id) as number1,sum(coalesce(balance,0.00)) as balance1
            from (
            select 
            rpu.name,aml.partner_id,sum(coalesce(aml.debit,0.00)-coalesce(partial.credit,0.00)) as balance
            from account_move_line aml
            left join account_account aa on aml.account_id=aa.id
            left join res_partner rp on aml.partner_id=rp.id
            left join res_users ru on rp.payment_responsible_id=ru.id
            left join res_partner rpu on ru.partner_id=rpu.id
            left join (
                select aml2.reconcile_partial_id,sum(aml2.credit) as credit 
                from account_move_line aml2 
                where aml2.date<='%s' and aml2.reconcile_partial_id is not NULL
                group by aml2.reconcile_partial_id) partial on aml.reconcile_partial_id=partial.reconcile_partial_id
            where 
            aml.date<='%s'
            and aa.reconcile=True
            and aa.type='receivable'
            and aml.reconcile_id is NULL
            group by rpu.name,aml.partner_id
            order by rpu.name
            ) dummy
            group by dummy.name
            ) dummy3
            left join 
            (
            select dummy2.name,count(dummy2.partner_id) as number2,sum(coalesce(balance,0.00)) as balance2
            from (
            select 
            rpu.name,aml.partner_id,sum(coalesce(aml.debit,0.00)-coalesce(partial.credit,0.00)) as balance
            from account_move_line aml
            left join account_account aa on aml.account_id=aa.id
            left join res_partner rp on aml.partner_id=rp.id
            left join res_users ru on rp.payment_responsible_id=ru.id
            left join res_partner rpu on ru.partner_id=rpu.id
            left join (
                select aml2.reconcile_partial_id,sum(aml2.credit) as credit 
                from account_move_line aml2 
                where aml2.date<='%s'::timestamp -INTERVAL '30 days' and aml2.reconcile_partial_id is not NULL
                group by aml2.reconcile_partial_id) partial on aml.reconcile_partial_id=partial.reconcile_partial_id
            where 
            aml.date_maturity<='%s'::timestamp -INTERVAL '30 days'
            and aa.reconcile=True
            and aa.type='receivable'
            and aml.reconcile_id is NULL
            group by rpu.name,aml.partner_id
            order by rpu.name
            ) dummy2
            group by dummy2.name
            ) dummy4 on dummy3.name=dummy4.name
            """%(end_date,end_date,end_date,end_date)
        
        cr.execute(query)
        result = cr.dictfetchall()
        return result
    
    #FOR DAILY REPORT
    def lines(self, data):
        aml_obj = self.env['account.move.line']
        move_state = ['posted']

        domain = [
                '&', ('reconciled', '=', False), 
                '&', ('account_id.user_type_id.type', '=', 'receivable'), 
                ('move_id.state', 'in', tuple(move_state))
            ]
        if data['date_from']:
            domain += [('date','>=', data['date_from'])]
        if data['date']:
            domain += [('date', '<=', data['date'])]
        #if self.account_ids:
        #    domain += [('account_id', 'in', tuple(self.account_ids))]

        receivables = []
        lines = aml_obj.search(domain, order="partner_id ASC, date ASC, account_id ASC")
        for line in lines:
            date_line = datetime.strptime(str(line.date), '%Y-%m-%d').date() 
            lyear, lmonth, lday = date_line.year, date_line.month, date_line.day
            #print "===",lyear, lmonth, lday
            receivables.append({
                'date': line.date,
                'move_name': line.move_id.name,
                'date_maturity': line.date_maturity,
                'fiscal': lyear,
                'period_name': str(lmonth),
                'account_name': '%s - %s' % (line.account_id.code, line.account_id.name),
                'payment_responsible_name': line.partner_id and line.partner_id.name or False,
                'partner_name': line.partner_id and line.partner_id.name or False,
                'level': 1,
                'balance': line.balance,
                'balance_red': (line.date_maturity and line.date_maturity < (datetime.now() + relativedelta(months=-1)).strftime('%Y-%m-%d')) and line.balance or 0.0,
            })
        #if self.report_type == 'daily_receivable':
        receivables = sorted(receivables, key=lambda k: (k['fiscal'], k['period_name'], k['partner_name'], k['account_name']))
        #if self.display_detail and self.group_by == 'group_partner':
        receivables = sorted(receivables, key=lambda k: (k['partner_name'], k['fiscal'], k['period_name'], k['account_name']))
#         if self.report_type == 'outstanding_followup':
#             receivables = sorted(receivables, key=lambda k: (k['payment_responsible_name'], k['partner_name'], k['fiscal'], k['period_name'], k['account_name']))
#             if self.display_detail and self.group_by == 'group_fiscal':
#                 receivables = sorted(receivables, key=lambda k: (k['payment_responsible_name'], k['fiscal'], k['period_name'], k['partner_name'], k['account_name']))
        return receivables
    
    def get_result_with_partner(self, receivables):
        res = [res for res in receivables if res.get('partner_name')]
        fiscal_periods = {}
        fiscal = set([r['fiscal'] for r in res])
        for f in sorted(fiscal):
            fiscal_periods.setdefault(f, {})
            for p in ['0','1','2','3','4','5','6','7','8','9','10','11','12']:
                fiscal_periods[f][p] = 0.0
        for r in res:
            fiscal_periods[r['fiscal']][r['period_name']] += r['balance']
        return (fiscal_periods, fiscal)

    def get_result_without_partner(self, receivables):
        res = [res for res in receivables if not res.get('partner_name')]
        return sum(r['balance'] for r in res)
    
    def get_result_followup(self, receivables):
        res_dict = {}
        i = 0
        for line in receivables:
            key = line['payment_responsible_name'] and line['payment_responsible_name'] or 'Unassigned'
            if res_dict.get(key):
                res_dict[key]['balance'] += line['balance']
                res_dict[key]['balance_red'] += line['balance_red']
                res_dict[key]['partner_count'] += (line['balance'] and receivables[i]['partner_name'] != receivables[i-1]['partner_name']) and 1 or 0
                res_dict[key]['partner_count_red'] += (line['balance_red'] and receivables[i]['partner_name'] != receivables[i-1]['partner_name']) and 1 or 0
            else:
                res_dict[key] = {
                        'payment_responsible_name': line['payment_responsible_name'] and line['payment_responsible_name'] or 'Unassigned',
                        'balance': line['balance'],
                        'balance_red': line['balance_red'],                    
                        'partner_count': 1,                    
                        'partner_count_red': line['balance_red'] and 1 or 0,                    
                    }
            i += 1   
        return [v for k, v in res_dict.items()]
    
    def get_receivable_group_followup_fiscal(self, receivables):
        res_dict = {}
        i = 0
        for line in receivables:
            group_payment = line['payment_responsible_name'] and line['payment_responsible_name'] or 'Unassigned'
            group_fiscal = str(line['fiscal'])
            group_period = str(line['period_name'].split('/')[0])
            group_partner = line['partner_name'] and line['partner_name'] or 'Unknown Partner'
            group_account = line['account_name'].split('-')[0].strip()
            key_level_account = group_fiscal + '-' + group_period + '-' + group_partner + '-' + group_account
            key_level_partner = group_fiscal + '-' + group_period + '-' + group_partner
            key_level_period = group_fiscal + '-' + group_period
            key_level_fiscal = group_fiscal
            key_level_payment = group_payment
            res_dict[key_level_account + '-' + line['date'] + '-' + line['move_name']] = {
                    'date': line['date'],
                    'move_name': line['move_name'],
                    'date_maturity': line['date_maturity'],
                    'level': 5,
                    'balance': line['balance'],
                    'balance_red': line['balance_red'],
                }
            if res_dict.get(key_level_account):
                res_dict[key_level_account]['balance'] += line['balance']
                res_dict[key_level_account]['balance_red'] += line['balance_red']
            else:
                res_dict[key_level_account] = {
                        'name': line['account_name'],
                        'level': 4,
                        'balance': line['balance'],
                        'balance_red': line['balance_red'],
                    }
            if res_dict.get(key_level_partner):
                res_dict[key_level_partner]['balance'] += line['balance']
                res_dict[key_level_partner]['balance_red'] += line['balance_red']
            else:
                res_dict[key_level_partner] = {
                        'name': group_partner,
                        'level': 3,
                        'balance': line['balance'],
                        'balance_red': line['balance_red'],
                    }
            if res_dict.get(key_level_period):
                res_dict[key_level_period]['balance'] += line['balance']
                res_dict[key_level_period]['balance_red'] += line['balance_red']
            else:
                res_dict[key_level_period] = {
                        'name': _mapping_periods[group_period],
                        'level': 2,
                        'balance': line['balance'],
                        'balance_red': line['balance_red'],
                    }
            if res_dict.get(key_level_fiscal):
                res_dict[key_level_fiscal]['balance'] += line['balance']
                res_dict[key_level_fiscal]['balance_red'] += line['balance_red']
            else:
                res_dict[key_level_fiscal] = {
                        'name': str(line['fiscal']),
                        'level': 1,
                        'balance': line['balance'],
                        'balance_red': line['balance_red'],
                    }
#             if res_dict.get(key_level_payment):
#                 res_dict[key_level_payment]['balance'] += line['balance']
#                 res_dict[key_level_payment]['balance_red'] += line['balance_red']
#             else:
#                 res_dict[key_level_payment] = {
#                         'name': group_payment,
#                         'level': 0,
#                         'balance': line['balance'],
#                         'balance_red': line['balance_red'],
#                     }
            i += 1   
        return [v for k, v in sorted(res_dict.items())]
    #FOR FINANCIAL REPORT
    def _compute_account_balance(self, accounts, context=None):
        """ compute the balance, debit and credit for the provided accounts
        """
        mapping = {
            'balance': "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as balance",
            'debit': "COALESCE(SUM(debit), 0) as debit",
            'credit': "COALESCE(SUM(credit), 0) as credit",
        }

        res = {}
        for account in accounts:
            res[account.id] = dict((fn, 0.0) for fn in mapping.keys())    
        if accounts:
            tables, where_clause, where_params = self.env['account.move.line'].with_context(context)._query_get()
            #print "tables===",tables
            #print "where_clause===",where_clause
            #print "where_params===",where_params
            tables = tables.replace('"', '') if tables else "account_move_line"
            wheres = [""]
            if where_clause.strip():
                wheres.append(where_clause.strip())
            filters = " AND ".join(wheres)
            request = "SELECT account_id as id, " + ', '.join(mapping.values()) + \
                       " FROM " + tables + \
                       " WHERE account_id IN %s " \
                            + filters + \
                       " GROUP BY account_id"
            params = (tuple(accounts._ids),) + tuple(where_params)
            self.env.cr.execute(request, params)
            for row in self.env.cr.dictfetchall():
                res[row['id']] = row
        return res

    def _compute_report_balance(self, reports, context=None):
        '''returns a dictionary with key=the ID of a record and value=the credit, debit and balance amount
           computed for this record. If the record is of type :
               'accounts' : it's the sum of the linked accounts
               'account_type' : it's the sum of leaf accoutns with such an account_type
               'account_report' : it's the amount of the related report
               'sum' : it's the sum of the children of this record (aka a 'view' record)'''
        res = {}
        fields = ['balance', 'debit', 'credit']
        #print "==_compute_report_balance====",reports
        for report in reports:
            #print "==report.type===",report.type,report.name
            context_retain_earning = context.copy()
            if report.special_date_changer == 'from_beginning':
                context_retain_earning.update({'date_from': False})
            if report.special_date_changer == 'to_beginning_of_period' and context.get('date_from'):
                date_to_re = datetime.strptime(str(context.get('date_from')), '%Y-%m-%d').date() 
                date_to = date(date_to_re.year, date_to_re.month, date_to_re.day) - timedelta(days=1)
                context_retain_earning.update({'date_from': False, 'date_to': date_to})
            if report.id in res:
                continue
            res[report.id] = dict((fn, 0.0) for fn in fields)
            if report.type == 'accounts':
                # it's the sum of the linked accounts
                res[report.id]['account'] = self._compute_account_balance(report.account_ids, context=context_retain_earning)
                #print "====res[report.id]['account']====",res[report.id]['account']
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_type':
                # it's the sum the leaf accounts with such an account type
                accounts_ids = self.env['account.account'].search([('user_type_id', 'in', report.account_type_ids.ids)])
                #accounts = self.env['account.account'].browse(accounts_ids)
                res[report.id]['account'] = self._compute_account_balance(accounts_ids, context=context_retain_earning)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
                res4 = self._compute_report_balance(report.account_report_ids, context=context_retain_earning)
                for key, value in res4.items():
                    for field in fields:
                        res[report.id][field] += value[field]
            elif report.type in ('account_report','account_report_monthly') and report.account_report_id:
                # it's the amount of the linked report
                context_current_earning = context.copy()
                res2 = self._compute_report_balance(report.account_report_id, context=context_current_earning)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
            elif report.type == 'account_reports' and report.account_report_ids:
                # it's the amount of the linked report
                res3 = self._compute_report_balance(report.account_report_ids, context=context_retain_earning)
                for key, value in res3.items():
                    for field in fields:
                        res[report.id][field] += value[field]
            elif report.type == 'sum':
                # it's the sum of the children of this account.report
                res2 = self._compute_report_balance(report.children_ids, context=context)
                #print "====res2====",res2
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
        return res
    #FOR REPORT GENERATE
    def _get_account_generate_report_line(self, data, lines):
        cr = self.env.cr
        uid = self.env.uid
        line_ids = []
        report_line_obj = self.env['account.generate.report.line']
        for line in report_line_obj.browse(lines):
            line_ids.append(line)
        return line_ids
    #FOR CASHFLOW
    def _get_account_cashflow_report_line(self, data, lines):
        cr = self.env.cr
        uid = self.env.uid
        line_ids = []
        report_line_obj = self.env['daily.report.cashflow.detail']
        for line in report_line_obj.browse(lines):
            line_ids.append(line)
        return line_ids
    
    #FOR DAILY REPORT
    def _get_account_daily_report(self, account_daily, daily_type):
        cr = self.env.cr
        uid = self.env.uid
        daily_ids = []
        #daily_cash_obj = self.env['daily.report.cash']
        #daily_bank_obj = self.env['daily.report.bank']
        daily_cashbank_obj = self.env['daily.report.cashbank']
#         if daily_type == 'cash':
#             for daily_cash in daily_cash_obj.browse(account_daily):
#                 res_cash = {}
#                 res_cash['account_id'] = daily_cash.account_id.id
#                 res_cash['amount'] = daily_cash.amount
#                 res_cash['notes'] = daily_cash.notes
#                 daily_ids.append(daily_cash.account_id.id)
#         if daily_type == 'bank':
#             for daily_bank in daily_bank_obj.browse(account_daily):
#                 #print "==daily_bank===",daily_bank#,daily_bank.account_id
#                 res_bank = {}
#                 res_bank['account_id'] = daily_bank.account_id.id
#                 res_bank['amount'] = daily_bank.amount
#                 res_bank['notes'] = daily_bank.notes
#                 daily_ids.append(daily_bank.account_id.id)
        if daily_type == 'cashbank':
            for daily_cashbank in daily_cashbank_obj.browse(account_daily):
                #print "==daily_bank===",daily_bank#,daily_bank.account_id
                res_cashbank = {}
                res_cashbank['account_id'] = daily_cashbank.account_id.id
                res_cashbank['amount'] = daily_cashbank.amount
                res_cashbank['notes'] = daily_cashbank.notes
                daily_ids.append(daily_cashbank.account_id.id)
        return daily_ids
    #FOR STOCK MOVEMENT
    def _get_account_stock_movement_balance(self, init_balance, accounts, data, product):
        product_obj = self.env['product.product']
        product_id = product_obj.browse(product)
        #move_state = ['posted','']
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        #move_lines = dict(map(lambda x: (x, []), accounts.ids))
        res = {}
        # Prepare initial sql query and Get the initial move lines
        if init_balance:
            init_tables, init_where_clause, init_where_params = MoveLine.with_context(date_from=data['date_from'], date_to=data['date_to'])._query_get_daily()
            init_wheres = [""]
            init_where_less = [data['date_from']]
            if init_where_clause.strip():
                init_wheres.append(init_where_clause.strip())
            init_filters = " AND ".join(init_wheres)
            #print "===init_where_params==",product, init_where_clause, init_where_params
            filters = init_filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
            #print "===filters==",filters,tuple(accounts.ids)
            sql = ("SELECT 0 AS lid, '' AS ldate, '' AS lcode, NULL AS amount_currency, '' AS lref, 'Saldo Awal' AS lname, \
                    COALESCE(SUM(l.debit),0.0) AS debit, COALESCE(SUM(l.credit),0.0) AS credit, \
                    (SELECT COALESCE(sum(ll.quantity),0) FROM account_move_line ll WHERE ll.debit >= 0 and ll.credit = 0 AND ll.account_id IN %s AND ll.move_id IN (SELECT id FROM account_move WHERE date < %s) AND ll.product_id = %s) AS lqty_in, \
                    (SELECT COALESCE(sum(ll.debit),0) FROM account_move_line ll WHERE ll.debit >= 0 and ll.credit = 0 AND ll.account_id IN %s AND ll.move_id IN (SELECT id FROM account_move WHERE date < %s) AND ll.product_id = %s) AS lqty_debit, \
                    (SELECT COALESCE(sum(ll.quantity),0) FROM account_move_line ll WHERE  ll.credit >= 0 and ll.debit = 0 AND ll.account_id IN %s AND ll.move_id IN (SELECT id FROM account_move WHERE date < %s) AND ll.product_id = %s) AS lqty_out, \
                    (SELECT COALESCE(sum(ll.credit),0) FROM account_move_line ll WHERE ll.credit >= 0 and ll.debit = 0 AND ll.account_id IN %s AND ll.move_id IN (SELECT id FROM account_move WHERE date < %s) AND ll.product_id = %s) AS lqty_credit, \
                    (SELECT COALESCE(sum(ll.quantity),0) FROM account_move_line ll WHERE ll.debit >= 0 AND ll.account_id IN %s AND ll.move_id IN (SELECT id FROM account_move WHERE date < %s) AND ll.product_id = %s) AS lqty_in1, \
                    (SELECT COALESCE(sum(ll.debit),0) FROM account_move_line ll WHERE ll.debit >= 0 AND ll.account_id IN %s AND ll.move_id IN (SELECT id FROM account_move WHERE date < %s) AND ll.product_id = %s) AS lqty_debit1, \
                    (SELECT COALESCE(sum(ll.quantity),0) FROM account_move_line ll WHERE  ll.credit >= 0 AND ll.account_id IN %s AND ll.move_id IN (SELECT id FROM account_move WHERE date < %s) AND ll.product_id = %s) AS lqty_out1, \
                    (SELECT COALESCE(sum(ll.credit),0) FROM account_move_line ll WHERE ll.credit >= 0 AND ll.account_id IN %s AND ll.move_id IN (SELECT id FROM account_move WHERE date < %s) AND ll.product_id = %s) AS lqty_credit1, \
                    (SELECT COALESCE(sum(ll.quantity),0) FROM account_move_line ll WHERE ll.debit > 0 AND ll.account_id IN %s AND ll.move_id IN (SELECT id FROM account_move WHERE date between %s and %s) AND ll.product_id = %s) AS lqty_in_in, \
                    (SELECT COALESCE(sum(ll.quantity),0) FROM account_move_line ll WHERE ll.credit > 0 AND ll.account_id IN %s AND ll.move_id IN (SELECT id FROM account_move WHERE date between %s and %s) AND ll.product_id = %s) AS lqty_out_out, \
                    (SELECT COALESCE(sum(ll.debit),0) FROM account_move_line ll WHERE ll.debit > 0 AND ll.account_id IN %s AND ll.move_id IN (SELECT id FROM account_move WHERE date between %s and %s) AND ll.product_id = %s) AS debit_in, \
                    (SELECT COALESCE(sum(ll.credit),0) FROM account_move_line ll WHERE ll.credit > 0 AND ll.account_id IN %s AND ll.move_id IN (SELECT id FROM account_move WHERE date between %s and %s) AND ll.product_id = %s) AS credit_out, \
                    '' AS lpartner_id,\
                    '' AS move_name, '' AS mmove_id, '' AS currency_code,\
                    NULL AS currency_id,\
                    '' AS invoice_id, '' AS invoice_type, '' AS invoice_number,\
                    '' AS partner_name\
                    FROM account_move_line l\
                    LEFT JOIN account_move m ON (l.move_id=m.id)\
                    LEFT JOIN res_currency c ON (l.currency_id=c.id)\
                    LEFT JOIN res_partner p ON (l.partner_id=p.id)\
                    LEFT JOIN account_invoice i ON (m.id =i.move_id)\
                    JOIN account_journal j ON (l.journal_id=j.id)\
                WHERE l.account_id IN %s AND l.product_id = %s " + filters + " ") 
            #DATE LESS THAN DATE TO
            params_lqty_in = (tuple(accounts.ids),) + tuple(init_where_less) + tuple([product])
            params_lqty_debit = (tuple(accounts.ids),) + tuple(init_where_less) + tuple([product])
            params_lqty_out = (tuple(accounts.ids),) + tuple(init_where_less) + tuple([product])
            params_lqty_credit = (tuple(accounts.ids),) + tuple(init_where_less) + tuple([product])
            params_lqty_in1 = (tuple(accounts.ids),) + tuple(init_where_less) + tuple([product])
            params_lqty_debit1 = (tuple(accounts.ids),) + tuple(init_where_less) + tuple([product])
            params_lqty_out1 = (tuple(accounts.ids),) + tuple(init_where_less) + tuple([product])
            params_lqty_credit1 = (tuple(accounts.ids),) + tuple(init_where_less) + tuple([product])
            #DATE BETWEEN FROM AND TO
            params_lqty_in_in = (tuple(accounts.ids),) + tuple(init_where_params) + tuple([product])
            params_lqty_out_out = (tuple(accounts.ids),) + tuple(init_where_params) + tuple([product])
            params_debit_in = (tuple(accounts.ids),) + tuple(init_where_params) + tuple([product])
            params_credit_in = (tuple(accounts.ids),) + tuple(init_where_params) + tuple([product])
            params_end = (tuple(accounts.ids),) + tuple([product]) + tuple(init_where_params)
            params = params_lqty_in + params_lqty_debit + params_lqty_out + params_lqty_credit + params_lqty_in1 + params_lqty_debit1 + params_lqty_out1 + params_lqty_credit1 + \
                     params_lqty_in_in + params_lqty_out_out + params_debit_in + params_credit_in + \
                     params_end
            #print "sql--",params
            #params = tuple(init_where_params)
            cr.execute(sql, params)
            res = self.env.cr.dictfetchall()
            # Calculate the debit, credit and balance for Accounts
            # account_res = []
            for l in res:
                l['iproduct'] = product_id.default_code
                l['pproduct'] = product_id.name
                l['product_awal'] = (l['lqty_debit'] - l['lqty_credit']) > 0.0 and l['lqty_in'] or -l['lqty_out'] or l['lqty_in1']-l['lqty_out1']
                l['product_masuk'] = ''
                l['product_keluar'] = ''
                l['product_akhir'] = ''
                l['saldo_awal'] = (l['lqty_debit'] - l['lqty_credit']) or (l['lqty_debit1'] - l['lqty_credit1'])
                l['saldo_masuk'] = ''
                l['saldo_keluar'] = ''
                l['saldo_akhir'] = ''
        return res
    
    def _get_account_movelines_movement_balance(self, data, product, init_account, accounts, context=None):
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        StockPicking = self.env['stock.picking']
        StockMove = self.env['stock.move']
        ProductProduct = self.env['product.product']
        #move_lines = dict(map(lambda x: (x, []), accounts.ids))
        sql_sort = 'l.date, l.move_id'
        tables, where_clause, where_params = MoveLine.with_context(date_from=data['date_from'], date_to=data['date_to'])._query_get_daily()
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        filters = filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')

        # Get move lines base on sql query and Calculate the total balance of move lines
        sql = ('SELECT l.id AS lid, l.account_id AS account_id, l.date AS ldate, j.code AS lcode, l.currency_id, l.amount_currency, l.ref AS lref, l.name AS lname, \
            COALESCE(l.debit,0) AS debit, COALESCE(l.credit,0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS balance, \
            COALESCE(l.quantity,0) AS lqty_in, COALESCE(l.quantity,0) AS lqty_out, \
            m.name AS move_name, c.symbol AS currency_code, p.name AS partner_name, \
            prdt.name AS pproduct, prd.id AS prodid \
            FROM account_move_line l\
            JOIN account_move m ON (l.move_id=m.id)\
            LEFT JOIN product_product prd on (l.product_id=prd.id)\
            LEFT JOIN product_template prdt on (prd.product_tmpl_id=prdt.id)\
            LEFT JOIN res_currency c ON (l.currency_id=c.id)\
            LEFT JOIN res_partner p ON (l.partner_id=p.id)\
            JOIN account_journal j ON (l.journal_id=j.id)\
            JOIN account_account acc ON (l.account_id = acc.id) \
            WHERE l.account_id IN %s AND l.product_id = %s ' + filters + ' GROUP BY l.id, l.account_id, l.date, j.code, l.currency_id, l.amount_currency, l.ref, l.name, m.name, c.symbol, p.name, prdt.name, prd.id ORDER BY ' + sql_sort)
        params = (tuple(accounts.ids),) + tuple([product]) + tuple(where_params)
        #print "sql_line",sql,params
        cr.execute(sql, params)
        res = self.env.cr.dictfetchall()
        account_sum = saldo_sum = 0.0
        for l in res:
            l['lorigin'] = ''
            l['llocation'] = ''
            picking_ids = StockPicking.search([('name','=',l['lref'])])
            move_ids = StockMove.search([('name','=',l['lname'])])
            if picking_ids:
                for pick in picking_ids:#StockPicking.browse(picking_ids):
                    if pick.move_lines:
                        for move in pick.move_lines:
                            l['llocation'] = move.location_id and move.location_id.name
                    l['lorigin'] = pick.sale_id and pick.sale_id.name
            elif move_ids:
                for stock in move_ids:#StockMove.browse(move_ids):
                    #print "=====",stock
                    l['llocation'] = stock.location_id and stock.location_id.name or ''
                    l['lref'] = l['lname']
            l['product_awal'] =  ''
            l['product_masuk'] = (l['debit'] > 0 and l['lqty_in']) or (l['debit']-l['credit']) == 0 and 'IN/' in l['lref'] and l['lqty_in']
            l['product_keluar'] = (l['credit'] > 0 and l['lqty_out']) or (l['debit']-l['credit']) == 0 and 'OUT/' in l['lref'] and l['lqty_out']
            account_sum+=(l['product_masuk'] - l['product_keluar'])
            product = ProductProduct.browse(l['prodid'])
            #print "=================",product.standard_price,account_sum+account['product_awal']
            l['product_akhir'] = (init_account['product_awal'])+account_sum#\\l['lqty_in'] - l['product_masuk'] - l['product_keluar']
            
            l['saldo_awal'] = ''
            l['saldo_masuk'] = l['debit'] > 0 and l['debit']
            l['saldo_keluar'] = l['credit'] > 0 and l['credit']
            saldo_sum+=(l['saldo_masuk'] - l['saldo_keluar'])
            l['saldo_akhir'] = (init_account['saldo_awal'])+saldo_sum
        return res
    
    #FOR GENERAL LEDGER
    def _get_account_move_balance(self, data, accounts, init_balance, sortby, display_account):
        """ """
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        move_lines = dict(map(lambda x: (x, []), accounts.ids))
        date_from = False
        date_to = time.strftime('%Y-%m-%d', time.strptime(data['date'],'%Y-%m-%d'))
        # Prepare initial sql query and Get the initial move lines
        if init_balance:
            init_tables, init_where_clause, init_where_params = MoveLine.with_context(date_from=date_from, date_to=date_to)._query_get()#MoveLine.with_context(date_to=self.context.get('date_from'), date_from=False)._query_get()
            init_wheres = [""]
            if init_where_clause.strip():
                init_wheres.append(init_where_clause.strip())
            init_filters = " AND ".join(init_wheres)
            filters = init_filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
            sql = ("SELECT 0 AS lid, l.account_id AS account_id, '' AS ldate, '' AS lcode, NULL AS amount_currency, '' AS lref, 'Initial Balance' AS lname, COALESCE(SUM(l.debit),0.0) AS debit, COALESCE(SUM(l.credit),0.0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance, '' AS lpartner_id,\
                '' AS move_name, '' AS mmove_id, '' AS currency_code,\
                NULL AS currency_id,\
                '' AS invoice_id, '' AS invoice_type, '' AS invoice_number,\
                '' AS partner_name\
                FROM account_move_line l\
                LEFT JOIN account_move m ON (l.move_id=m.id)\
                LEFT JOIN res_currency c ON (l.currency_id=c.id)\
                LEFT JOIN res_partner p ON (l.partner_id=p.id)\
                LEFT JOIN account_invoice i ON (m.id =i.move_id)\
                JOIN account_journal j ON (l.journal_id=j.id)\
                WHERE l.account_id IN %s" + filters + ' GROUP BY l.account_id')
            params = (tuple(accounts.ids),) + tuple(init_where_params)
            cr.execute(sql, params)
            for row in cr.dictfetchall():
                move_lines[row.pop('account_id')].append(row)

        sql_sort = 'l.date, l.move_id'
        if sortby == 'sort_journal_partner':
            sql_sort = 'j.code, p.name, l.move_id'

        # Calculate the debit, credit and balance for Accounts
        account_res = []
        for account in accounts:
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            res['id'] = account.id
            res['code'] = account.code
            res['name'] = account.name
            res['move_lines'] = move_lines[account.id]
            for line in res.get('move_lines'):
                res['debit'] += line['debit']
                res['credit'] += line['credit']
                res['balance'] = line['balance']
            #print "===display_account===",res
            if display_account == 'all':
                account_res.append(res)
            if display_account == 'movement' and res.get('move_lines'):
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(res['balance']):
                account_res.append(res)
        return account_res
    
    def _get_account_move_init_balance(self, data, accounts, init_balance, sortby, display_account, account_type):
        #print """ _get_account_move_init_balance """,data['date'],account_type
        cr = self.env.cr
        uid = self.env.uid
        if account_type in ('cash_account','bank_account', 'cashbank_account', 'cashflow_account', 'bankbook_account'):
            date_from = False#time.strftime('%Y-%m-01', time.strptime(data['date'],'%Y-%m-%d'))
            date_first_to = time.strftime('%Y-%m-01', time.strptime(data['date'],'%Y-%m-%d'))
            date_to = datetime.strptime(date_first_to, DEFAULT_SERVER_DATE_FORMAT).date() - timedelta(days=1)
            #next_month = any_day.replace(day=28) + timedelta(days=4)  # this will never fail
            #print "====", date_first_to - timedelta(days=1)
        else:
            #account_type as YYYY-MM-DD
            if sortby == 'daily':
                date_from = time.strftime('%Y-%m-%d', time.strptime(account_type,'%Y-%m-%d'))
                date_to = time.strftime('%Y-%m-%d', time.strptime(account_type,'%Y-%m-%d')) 
            else:
                date_monthly = datetime.strptime(account_type, DEFAULT_SERVER_DATE_FORMAT).date()
                date_from = time.strftime('%Y-%m-01', time.strptime(account_type,'%Y-%m-%d'))
                date_to = self._last_day_of_month(date(date_monthly.year, date_monthly.month, date_monthly.day))
                #print "==date_monthly==",date_from,date_to
                #date_to = time.strftime('%Y-%m-%d', time.strptime(data['date'],'%Y-%m-%d'))         
        MoveLine = self.env['account.move.line']
        move_lines = dict(map(lambda x: (x, []), accounts.ids))
        #print "===init_balance==",date_from,date_to
        # Prepare initial sql query and Get the initial move lines
        if init_balance:
            init_tables, init_where_clause, init_where_params = MoveLine.with_context(date_from=date_from, date_to=date_to)._query_get_daily()#MoveLine.with_context(date_to=self.context.get('date_from'), date_from=False)._query_get()
            init_wheres = [""]
            if init_where_clause.strip():
                init_wheres.append(init_where_clause.strip())
            init_filters = " AND ".join(init_wheres)
            filters = init_filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
            sql = ("SELECT 0 AS lid, l.account_id AS account_id, '' AS ldate, '' AS lcode, NULL AS amount_currency, '' AS lref, 'Initial Balance' AS lname, COALESCE(SUM(l.debit),0.0) AS debit, COALESCE(SUM(l.credit),0.0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance, '' AS lpartner_id,\
                '' AS move_name, '' AS mmove_id, '' AS currency_code,\
                NULL AS currency_id,\
                '' AS invoice_id, '' AS invoice_type, '' AS invoice_number,\
                '' AS partner_name\
                FROM account_move_line l\
                LEFT JOIN account_move m ON (l.move_id=m.id)\
                LEFT JOIN res_currency c ON (l.currency_id=c.id)\
                LEFT JOIN res_partner p ON (l.partner_id=p.id)\
                LEFT JOIN account_invoice i ON (m.id =i.move_id)\
                JOIN account_journal j ON (l.journal_id=j.id)\
                WHERE l.account_id IN %s" + filters + ' GROUP BY l.account_id')
            #print "==sql==",accounts.ids,init_where_params
            params = (tuple(accounts.ids),) + tuple(init_where_params)
            cr.execute(sql, params)
            for row in cr.dictfetchall():
                move_lines[row.pop('account_id')].append(row)
                #print "====row====",row
        #print "===move_lines===",move_lines
        sql_sort = 'l.date, l.move_id'
        if sortby == 'sort_journal_partner':
            sql_sort = 'j.code, p.name, l.move_id'
        #dailyc_ids = []
        #daily_ids = dict(map(lambda x: (x, []), accounts.ids))
        daily_ids = dict(map(lambda x: (x, []), accounts.ids))
        #print ('dail')
        if account_type == 'cashbank_account':
            for dailyc in self.env['daily.report.cashbank'].browse(data['daily_cashbank_ids']):
                daily_ids[dailyc.account_id.id].append(dailyc)
#         if account_type == 'cash_account':
#             for dailyc in self.env['daily.report.cash'].browse(data['daily_report_cash']):
#                 daily_ids[dailyc.account_id.id].append(dailyc)
#         elif account_type == 'bank_account':
#             for dailyb in self.env['daily.report.bank'].browse(data['daily_report_bank']):
#                 daily_ids[dailyb.account_id.id].append(dailyb)
        # Calculate the debit, credit and balance for Accounts
        account_res = []
        #print "===accounts===",accounts
        for account in accounts:
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            res['id'] = account.id
            res['code'] = account.code
            res['name'] = account.name
            if account_type in ('cash_account', 'bank_account','cashbank_account'):
                res['sfr'] = daily_ids[res['id']][0].amount
                res['as'] = daily_ids[res['id']][0].notes
            res['sr'] = 0.0
            res['move_lines'] = move_lines[account.id]
            for line in res.get('move_lines'):
                #print "====line====",line['debit'],line['credit']
                res['debit'] += line['debit']
                res['credit'] += line['credit']
                res['balance'] = line['balance']
            if display_account == 'all':
                account_res.append(res)
            if display_account == 'movement' and res.get('move_lines'):
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(res['balance']):
                account_res.append(res)
        #print "====account_res====",account_res
        return account_res
    
    def _get_account_move_counter_part(self, data, account, account_sum):
        #print "===_get_account_move_counter_part===",account,account_sum
        lines = []
        if account:
            cr = self.env.cr
            MoveLine = self.env['account.move.line']
            date_from = time.strftime('%Y-%m-01', time.strptime(data['date'],'%Y-%m-%d'))
            date_to = time.strftime('%Y-%m-%d', time.strptime(data['date'],'%Y-%m-%d'))
            #move_lines = dict(map(lambda x: (x, []), accounts.ids))
            #move_line_ids = MoveLine.search([('move_id','=',l['mmove_id']),('account_id','!=',account.id)])
            sql_sort = 'l.date, l.move_id'
            #print "====get_lines===",date_from,date_to
    #         if sortby == 'sort_journal_partner':
    #             sql_sort = 'j.code, p.name, l.move_id'
            # Prepare sql query base on selected parameters from wizard
            tables, where_clause, where_params = MoveLine.with_context(date_to=date_to, date_from=date_from)._query_get_daily()
            #print '===tables, where_clause, where_params==',where_params
            wheres = [""]
            if where_clause.strip():
                wheres.append(where_clause.strip())
            filters = " AND ".join(wheres)
            filters = filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
    
            # Get move lines base on sql query and Calculate the total balance of move lines
            sql = ('SELECT l.id AS lid, l.account_id AS account_id, l.date AS ldate, j.code AS lcode, l.currency_id, l.amount_currency, l.ref AS lref, l.name AS lname, COALESCE(l.debit,0) AS debit, COALESCE(l.credit,0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS balance,\
                m.name AS move_name, m.id AS mmove_id, c.symbol AS currency_code, p.name AS partner_name\
                FROM account_move_line l\
                JOIN account_move m ON (l.move_id=m.id)\
                LEFT JOIN res_currency c ON (l.currency_id=c.id)\
                LEFT JOIN res_partner p ON (l.partner_id=p.id)\
                JOIN account_journal j ON (l.journal_id=j.id)\
                JOIN account_account acc ON (l.account_id = acc.id) \
                WHERE l.account_id in %s ' + filters + ' GROUP BY l.id, l.account_id, l.date, j.code, l.currency_id, l.amount_currency, l.ref, l.name, m.name, m.id, c.symbol, p.name ORDER BY ' + sql_sort)
            params = (tuple(account),) + tuple(where_params)
            #print "===params====",params
            #params = tuple(where_params)
            cr.execute(sql, params)
            for line_row in cr.dictfetchall():
                move_line_ids = MoveLine.search([('move_id','=',line_row['mmove_id']),('account_id','not in',tuple(account))])
                #print "===move_line_ids==",move_line_ids
                line_row['laccid'] = ''
                line_row['lacc'] = ''
                line_row['lidd'] = ''
                for line_move in move_line_ids:
                    line_row['mmove_id'] = line_move.move_id
                    line_row['lacc'] = line_move.account_id.name
                    line_row['lidd'] = line_move.id
                    line_row['laccid'] = line_move.account_id.id
                    lines.append(line_move.id)
        #print "====lines==",lines
        res = {}
        if lines != []:
            if len(lines) == 1:
                if data['display_type'] == 'summary':# or data['display_type_bank'] == 'summary':
                    sql_counter = ('SELECT 0 AS lid, l.account_id AS account_id, acc.name AS lref, acc.code AS lname, COALESCE(SUM(l.debit),0.0) AS credit, COALESCE(SUM(l.credit),0.0) AS debit \
                        FROM account_move_line l\
                        JOIN account_move m ON (l.move_id=m.id)\
                        LEFT JOIN res_currency c ON (l.currency_id=c.id)\
                        LEFT JOIN res_partner p ON (l.partner_id=p.id)\
                        JOIN account_journal j ON (l.journal_id=j.id)\
                        JOIN account_account acc ON (l.account_id = acc.id) \
                        WHERE l.id = '+ str(lines[0]) +' ' + filters + ' GROUP BY l.account_id,acc.name,acc.code')
#                 if data['display_type_bank'] == 'summary':# or data['display_type_bank'] == 'summary':
#                     sql_counter = ('SELECT 0 AS lid, l.account_id AS account_id, acc.name AS lref, acc.code AS lname, COALESCE(SUM(l.debit),0.0) AS credit, COALESCE(SUM(l.credit),0.0) AS debit \
#                         FROM account_move_line l\
#                         JOIN account_move m ON (l.move_id=m.id)\
#                         LEFT JOIN res_currency c ON (l.currency_id=c.id)\
#                         LEFT JOIN res_partner p ON (l.partner_id=p.id)\
#                         JOIN account_journal j ON (l.journal_id=j.id)\
#                         JOIN account_account acc ON (l.account_id = acc.id) \
#                         WHERE l.id = '+ str(lines[0]) +' ' + filters + ' GROUP BY l.account_id,acc.name,acc.code')
                    #print "====line1====summary",sql_counter,lines
                if data['display_type'] == 'detail':
                    sql_counter = ('SELECT 0 AS lid, l.move_id AS move_id, l.account_id AS account_id, acc.name AS lref, l.name AS lname, l.date AS ldate, COALESCE(SUM(l.debit),0.0) AS credit, COALESCE(SUM(l.credit),0.0) AS debit \
                        FROM account_move_line l\
                        JOIN account_move m ON (l.move_id=m.id)\
                        LEFT JOIN res_currency c ON (l.currency_id=c.id)\
                        LEFT JOIN res_partner p ON (l.partner_id=p.id)\
                        JOIN account_journal j ON (l.journal_id=j.id)\
                        JOIN account_account acc ON (l.account_id = acc.id) \
                        WHERE l.id = '+ str(lines[0]) +' ' + filters + ' GROUP BY l.id,acc.name,l.name ORDER BY l.date')
#                 if data['display_type_bank'] == 'detail':
#                     sql_counter = ('SELECT 0 AS lid, l.account_id AS account_id, acc.name AS lref, l.name AS lname, l.date AS ldate, COALESCE(SUM(l.debit),0.0) AS credit, COALESCE(SUM(l.credit),0.0) AS debit \
#                         FROM account_move_line l\
#                         JOIN account_move m ON (l.move_id=m.id)\
#                         LEFT JOIN res_currency c ON (l.currency_id=c.id)\
#                         LEFT JOIN res_partner p ON (l.partner_id=p.id)\
#                         JOIN account_journal j ON (l.journal_id=j.id)\
#                         JOIN account_account acc ON (l.account_id = acc.id) \
#                         WHERE l.id = '+ str(lines[0]) +' ' + filters + ' GROUP BY l.id,acc.name,l.name ORDER BY l.date')
                    #print "====line1====detail",sql_counter,lines
                cr.execute(sql_counter, tuple(where_params))
            else:
                if data['display_type'] == 'summary':
                    sql_counter = ('SELECT 0 AS lid, l.account_id AS account_id, acc.name AS lref, acc.code AS lname, COALESCE(SUM(l.debit),0.0) AS credit, COALESCE(SUM(l.credit),0.0) AS debit \
                        FROM account_move_line l\
                        JOIN account_move m ON (l.move_id=m.id)\
                        LEFT JOIN res_currency c ON (l.currency_id=c.id)\
                        LEFT JOIN res_partner p ON (l.partner_id=p.id)\
                        JOIN account_journal j ON (l.journal_id=j.id)\
                        JOIN account_account acc ON (l.account_id = acc.id) \
                        WHERE l.id IN %s ' + filters + ' GROUP BY l.account_id,acc.name,acc.code')
#                 if data['display_type_bank'] == 'summary':
#                     sql_counter = ('SELECT 0 AS lid, l.account_id AS account_id, acc.name AS lref, acc.code AS lname, COALESCE(SUM(l.debit),0.0) AS credit, COALESCE(SUM(l.credit),0.0) AS debit \
#                         FROM account_move_line l\
#                         JOIN account_move m ON (l.move_id=m.id)\
#                         LEFT JOIN res_currency c ON (l.currency_id=c.id)\
#                         LEFT JOIN res_partner p ON (l.partner_id=p.id)\
#                         JOIN account_journal j ON (l.journal_id=j.id)\
#                         JOIN account_account acc ON (l.account_id = acc.id) \
#                         WHERE l.id IN %s ' + filters + ' GROUP BY l.account_id,acc.name,acc.code')
                    #print "====line>1====summary",sql_counter,data['display_type_cash']              
                if data['display_type'] == 'detail':
                    sql_counter = ('SELECT 0 AS lid, l.move_id AS move_id, l.account_id AS account_id, acc.name AS lref, l.name AS lname, l.date AS ldate, COALESCE(SUM(l.debit),0.0) AS credit, COALESCE(SUM(l.credit),0.0) AS debit \
                        FROM account_move_line l\
                        JOIN account_move m ON (l.move_id=m.id)\
                        LEFT JOIN res_currency c ON (l.currency_id=c.id)\
                        LEFT JOIN res_partner p ON (l.partner_id=p.id)\
                        JOIN account_journal j ON (l.journal_id=j.id)\
                        JOIN account_account acc ON (l.account_id = acc.id) \
                        WHERE l.id IN %s ' + filters + ' GROUP BY l.id,acc.name,l.name ORDER BY l.date')
#                 if data['display_type_bank'] == 'detail':
#                     sql_counter = ('SELECT 0 AS lid, l.account_id AS account_id, acc.name AS lref, l.name AS lname, l.date AS ldate, COALESCE(SUM(l.debit),0.0) AS credit, COALESCE(SUM(l.credit),0.0) AS debit \
#                         FROM account_move_line l\
#                         JOIN account_move m ON (l.move_id=m.id)\
#                         LEFT JOIN res_currency c ON (l.currency_id=c.id)\
#                         LEFT JOIN res_partner p ON (l.partner_id=p.id)\
#                         JOIN account_journal j ON (l.journal_id=j.id)\
#                         JOIN account_account acc ON (l.account_id = acc.id) \
#                         WHERE l.id IN %s ' + filters + ' GROUP BY l.id,acc.name,l.name ORDER BY l.date')
                    #print "====line>1====detail",sql_counter,lines
                cr.execute(sql_counter, (tuple(lines),) + tuple(where_params))
            #account_sum = 0.0
            #print "===sql_counter===",sql_counter,lines
            res_counter = cr.dictfetchall()
            res = res_counter
            for line_cou in res:
                line_cou['lacc'] = ''
                #print "==ddd==",line_cou['debit'], line_cou['credit']
                account_sum += line_cou['debit'] - line_cou['credit']
                line_cou['balance'] = line_cou['debit'] - line_cou['credit']
                #line_cou['date'] = line_cou['date']
                line_cou['lname'] = line_cou['lname']
                if data['display_type'] == 'detail':
                    line_cou['move_id'] = line_cou['move_id']
                    line_cou['ldate'] = line_cou['ldate']
                    #line_cou['move_name'] = line_cou['lname']
#                 if data['display_type_bank'] == 'detail':
#                     line_cou['ldate'] = line_cou['ldate']
                line_cou['progress'] = account_sum
        return res
    
    def _get_account_move_entry(self, accounts, init_balance, sortby, display_account, context=None):
        """
        :param:
                accounts: the recordset of accounts
                init_balance: boolean value of initial_balance
                sortby: sorting by date or partner and journal
                display_account: type of account(receivable, payable and both)

        Returns a dictionary of accounts with following key and value {
                'code': account code,
                'name': account name,
                'debit': sum of total debit amount,
                'credit': sum of total credit amount,
                'balance': total balance,
                'amount_currency': sum of amount_currency,
                'move_lines': list of move line
        }
        """
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        acc_ids = []
        for acc in accounts.ids:
            acc_ids.append(acc.id)
        move_lines = dict(map(lambda x: (x, []), acc_ids))
        
        # Prepare initial sql query and Get the initial move lines
        if init_balance:
            init_tables, init_where_clause, init_where_params = MoveLine.with_context(date_to=context.get('date_from'), date_from=False)._query_get()#MoveLine.with_context(date_to=self.context.get('date_from'), date_from=False)._query_get()
            #print "gl===xls==date_from",accounts.ids
            init_wheres = [""]
            if init_where_clause.strip():
                init_wheres.append(init_where_clause.strip())
            init_filters = " AND ".join(init_wheres)
            filters = init_filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
            sql = ("SELECT 0 AS lid, l.account_id AS account_id, '' AS ldate, '' AS lcode, NULL AS amount_currency, '' AS lref, 'Initial Balance' AS lname, COALESCE(SUM(l.debit),0.0) AS debit, COALESCE(SUM(l.credit),0.0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance, '' AS lpartner_id,\
                '' AS move_name, '' AS mmove_id, '' AS currency_code,\
                NULL AS currency_id,\
                '' AS invoice_id, '' AS invoice_type, '' AS invoice_number,\
                '' AS partner_name\
                FROM account_move_line l\
                LEFT JOIN account_move m ON (l.move_id=m.id)\
                LEFT JOIN res_currency c ON (l.currency_id=c.id)\
                LEFT JOIN res_partner p ON (l.partner_id=p.id)\
                LEFT JOIN account_invoice i ON (m.id =i.move_id)\
                JOIN account_journal j ON (l.journal_id=j.id)\
                WHERE l.account_id IN %s" + filters + ' GROUP BY l.account_id')
            params = (tuple(acc_ids),) + tuple(init_where_params)
            cr.execute(sql, params)
            for row in cr.dictfetchall():
                move_lines[row.pop('account_id')].append(row)

        sql_sort = 'l.date, l.move_id'
        if sortby == 'sort_journal_partner':
            sql_sort = 'j.code, p.name, l.move_id'

        # Prepare sql query base on selected parameters from wizard
        tables, where_clause, where_params = MoveLine.with_context(context)._query_get()
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        filters = filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')

        # Get move lines base on sql query and Calculate the total balance of move lines
        sql = ('SELECT l.id AS lid, l.account_id AS account_id, l.date AS ldate, j.code AS lcode, l.currency_id, l.amount_currency, l.ref AS lref, l.name AS lname, COALESCE(l.debit,0) AS debit, COALESCE(l.credit,0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS balance,\
            m.name AS move_name, c.symbol AS currency_code, p.name AS partner_name\
            FROM account_move_line l\
            JOIN account_move m ON (l.move_id=m.id)\
            LEFT JOIN res_currency c ON (l.currency_id=c.id)\
            LEFT JOIN res_partner p ON (l.partner_id=p.id)\
            JOIN account_journal j ON (l.journal_id=j.id)\
            JOIN account_account acc ON (l.account_id = acc.id) \
            WHERE l.account_id IN %s ' + filters + ' GROUP BY l.id, l.account_id, l.date, j.code, l.currency_id, l.amount_currency, l.ref, l.name, m.name, c.symbol, p.name ORDER BY ' + sql_sort)
        params = (tuple(acc_ids),) + tuple(where_params)
        cr.execute(sql, params)

        for row in cr.dictfetchall():
            balance = 0
            for line in move_lines.get(row['account_id']):
                balance += line['debit'] - line['credit']
            row['balance'] += balance
            move_lines[row.pop('account_id')].append(row)

        # Calculate the debit, credit and balance for Accounts
        account_res = []
        for account in accounts.ids:
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            res['code'] = account.code
            res['name'] = account.name
            res['move_lines'] = move_lines[account.id]
            for line in res.get('move_lines'):
                res['debit'] += line['debit']
                res['credit'] += line['credit']
                res['balance'] = line['balance']
            if display_account == 'all':
                account_res.append(res)
            if display_account == 'movement' and res.get('move_lines'):
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(res['balance']):
                account_res.append(res)
        return account_res
    
    #===========================================================================
    # START OF AGED PARTNER BALANCE
    #===========================================================================
    def _get_salesperson(self, account_type, date_from):
        cr = self.env.cr
        arg_list = (tuple(account_type), date_from)
        query = '''
            SELECT DISTINCT (res_users.id) AS id 
            FROM res_partner, res_users, account_invoice AS l, account_account 
            WHERE (l.account_id=account_account.id) 
                AND (account_account.internal_type IN %s) 
                AND (l.residual > 0.0) 
                AND (l.partner_id=res_partner.id) 
                AND (l.user_id=res_users.id) 
                AND (res_users.active = True)
                AND (l.date_invoice <= %s)'''
        cr.execute(query, arg_list)

        users = cr.dictfetchall()
        # Build a string like (1,2,3) for easy use in SQL query
        user_ids = [user['id'] for user in users]
        #print "===user_ids====",user_ids
        return user_ids
    
    def _get_partner(self, form, account_type, date_from, target_move):
        cr = self.env.cr
        uid = self.env.uid
        user = self.env['res.users'].browse(uid)
        user_company = user.company_id.id
        move_state = ['draft', 'posted']
        if target_move == 'posted':
            move_state = ['posted']
        arg_list = (tuple(move_state), tuple(account_type))
        #build the reconciliation clause to see what partner needs to be printed
        reconciliation_clause = '(l.reconciled IS FALSE)'
        cr.execute('SELECT debit_move_id, credit_move_id FROM account_partial_reconcile where create_date > %s', (date_from,))
        reconciled_after_date = []
        for row in cr.fetchall():
            reconciled_after_date += [row[0], row[1]]
        if reconciled_after_date:
            reconciliation_clause = '(l.reconciled IS FALSE OR l.id IN %s)'
            arg_list += (tuple(reconciled_after_date),)
        arg_list += (date_from, user_company)
        query = '''
            SELECT DISTINCT res_partner.id AS id, res_partner.name AS name, UPPER(res_partner.name) AS uppername
            FROM res_partner,account_move_line AS l, account_account, account_move am
            WHERE (l.account_id = account_account.id)
                AND (l.move_id = am.id)
                AND (am.state IN %s)
                AND (account_account.internal_type IN %s)
                AND ''' + reconciliation_clause + '''
                AND (l.partner_id = res_partner.id)
                AND (l.date <= %s)
                AND l.company_id = %s
            ORDER BY UPPER(res_partner.name)'''
        cr.execute(query, arg_list)

        partners = cr.dictfetchall()
        # Build a string like (1,2,3) for easy use in SQL query
        partner_ids = [partner['id'] for partner in partners]
        return partner_ids
        
    def _get_partner_move_lines(self, partner, user_id, form, account_type, date_from, target_move):
        #print "==_get_partner_move_lines==",form#.get('result_selection', False)
        res = []
        self.total_account = []
        #'result_selection' in form
        if form['display_type'] == 'summary':
            #=====99272
            fill = 'l.partner_id IN %s'
            part_rel = ''
            part_tot = ''
            res_partner = ''
            #=====
            user = ''
            user_rel = ''
            user_tot = ''
            res_users = ''
        elif form['display_type'] in ('detail', 'salesperson', 'partner'):
            #=====
            fill = 'l.id IN %s'
            part_rel = """AND (l.partner_id=res_partner.id) """
            part_tot = """AND (res_partner.id = """+str(partner.id)+""") """
            res_partner = """ res_partner, """
            #=====
            if form['display_type'] in ('detail', 'partner'):
                user_ids = ''
                user_rel = ''
                user_tot = ''
                res_users = ''
            else:
                user_ids = """AND (res_users.id = """+str(user_id.id)+""") """
                user_rel = """AND (am.user_id=res_users.id) """
                user_tot = """AND (res_users.id = """+str(user_id.id)+""") """
                res_users = """ res_users, """
            #=====
        cr = self.env.cr
        uid = self.env.uid
        user = self.env['res.users'].browse(uid)
        user_company = user.company_id.id
        move_state = ['draft', 'posted']
        if target_move == 'posted':
            move_state = ['posted']
        arg_list = (tuple(move_state), tuple(account_type))
#         if form['result_selection'] == 'customer':
#             filter_result = 'AND l.debit > 0.0'
#         elif form['result_selection'] == 'supplier':
#             filter_result = 'AND l.credit > 0.0'
#         else:
        filter_result = ''
        #build the reconciliation clause to see what partner needs to be printed
        reconciliation_clause = '(l.reconciled IS FALSE)'
        cr.execute('SELECT debit_move_id, credit_move_id FROM account_partial_reconcile where create_date > %s', (date_from,))
        reconciled_after_date = []
        for row in cr.fetchall():
            reconciled_after_date += [row[0], row[1]]
        if reconciled_after_date:
            reconciliation_clause = '(l.reconciled IS FALSE OR l.id IN %s)'
            arg_list += (tuple(reconciled_after_date),)
        arg_list += (date_from, user_company)
        if form['display_type'] == 'summary':
            #first = 'DISTINCT res_partner.id'
            query = '''
                SELECT DISTINCT res_partner.id AS id, res_partner.name AS name, UPPER(res_partner.name) AS uppername
                FROM res_partner,account_move_line AS l, account_account, account_move am
                WHERE (l.account_id = account_account.id)
                    AND (l.move_id = am.id)
                    AND (am.state IN %s)
                    AND (account_account.internal_type IN %s)
                    AND ''' + reconciliation_clause + '''
                    AND (l.partner_id = res_partner.id)
                    AND (l.date <= %s)
                    AND l.company_id = %s
                ORDER BY UPPER(res_partner.name)'''
        elif form['display_type'] in ('detail', 'salesperson', 'partner'):
            part = """res_partner.id = """+str(partner.id)+""" """
            query = '''
                SELECT DISTINCT l.id AS id, res_partner.name AS name, UPPER(res_partner.name) AS uppername, l.date AS date, l.name AS number, l.ref AS ref
                FROM res_partner, '''+ res_users +''' account_move_line AS l, account_account, account_move am
                WHERE (l.account_id = account_account.id)
                    AND (l.move_id = am.id)
                    AND (am.state IN %s)
                    AND (account_account.internal_type IN %s)
                    AND ''' + reconciliation_clause + '''
                    AND (l.partner_id = res_partner.id)
                    AND ('''+ part +''')
                    '''+ user_rel +'''
                    '''+ user_ids +'''
                    '''+ filter_result +'''
                    AND (l.date <= %s)
                    AND l.company_id = %s
                ORDER BY UPPER(res_partner.name), l.date, l.name, l.ref '''
            #print "===query===",query
        cr.execute(query, arg_list)

        partners = cr.dictfetchall()
        #print "===partners=",partners
        # put a total of 0
        for i in range(7):
            self.total_account.append(0)

        # Build a string like (1,2,3) for easy use in SQL query
        partner_ids = [partner['id'] for partner in partners]
        #print "===partner_ids==",partner_ids
        if not partner_ids:
            return []

        # This dictionary will store the not due amount of all partners
        future_past = {}
        query = '''SELECT l.id
                FROM '''+ res_partner +''' '''+ res_users +''' account_move_line AS l, account_account, account_move am
                WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                    AND (am.state IN %s)
                    AND (account_account.internal_type IN %s)
                    AND (COALESCE(l.date_maturity,l.date) > %s)
                    AND '''+ fill +'''
                    '''+ part_rel +'''
                    '''+ part_tot +'''
                    '''+ user_rel +'''
                    '''+ user_tot +'''
                AND (l.date <= %s)
                AND l.company_id = %s'''
        cr.execute(query, (tuple(move_state), tuple(account_type), date_from, tuple(partner_ids), date_from, user_company))
        aml_ids = cr.fetchall()
        aml_ids = aml_ids and [x[0] for x in aml_ids] or []
        #print "==aml_ids=",aml_ids
        for line in self.env['account.move.line'].browse(aml_ids):
            if line.partner_id.id not in future_past:
                if form['display_type'] in ('detail', 'salesperson', 'partner'):
                    future_past[line.id] = 0.0
                else:
                    future_past[line.partner_id.id] = 0.0
            line_amount = line.balance
            #print "===line_amount==",line.balance
            if line.balance == 0:
                continue
            for partial_line in line.matched_debit_ids:
                if partial_line.create_date[:10] <= date_from:
                    line_amount += partial_line.amount
            for partial_line in line.matched_credit_ids:
                if partial_line.create_date[:10] <= date_from:
                    line_amount -= partial_line.amount
            if form['display_type'] in ('detail', 'salesperson', 'partner'):
                future_past[line.id] += line_amount
            else:
                future_past[line.partner_id.id] += line_amount
            #print "=future_past=>",future_past[line.partner_id.id],line.partner_id.id

        # Use one query per period and store results in history (a list variable)
        # Each history will contain: history[1] = {'<partner_id>': <partner_debit-credit>}
        history = []
        for i in range(5):
            args_list = (tuple(move_state), tuple(account_type), tuple(partner_ids),)
            dates_query = '(COALESCE(l.date_maturity,l.date)'

            if form[str(i)]['start'] and form[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s)'
                args_list += (form[str(i)]['start'], form[str(i)]['stop'])
            elif form[str(i)]['start']:
                dates_query += ' >= %s)'
                args_list += (form[str(i)]['start'],)
            else:
                dates_query += ' <= %s)'
                args_list += (form[str(i)]['stop'],)
            args_list += (date_from, user_company)

            query = '''SELECT l.id
                    FROM ''' + res_partner + ''' ''' + res_users + ''' account_move_line AS l, account_account, account_move am
                    WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                        AND (am.state IN %s)
                        AND (account_account.internal_type IN %s)
                        AND '''+ fill +'''
                        AND ''' + dates_query + '''
                        ''' + part_rel + '''
                        ''' + part_tot + '''
                        ''' + user_rel + '''
                        ''' + user_tot + '''
                    AND (l.date <= %s)
                    AND l.company_id = %s'''
            #print "======",query,args_list
            cr.execute(query, args_list)
            partners_amount = {}
            aml_ids = cr.fetchall()
            aml_ids = aml_ids and [x[0] for x in aml_ids] or []
            for line in self.env['account.move.line'].browse(aml_ids):
                if line.partner_id.id not in partners_amount:
                    partners_amount[line.partner_id.id] = 0.0
                line_amount = line.balance
                if line.balance == 0:
                    continue
                for partial_line in line.matched_debit_ids:
                    #print "partial_debit===",partial_line.create_date,date_from
                    if partial_line.create_date[:10] <= date_from:
                        line_amount += partial_line.amount
                for partial_line in line.matched_credit_ids:
                    #print "partial_credit===",partial_line.create_date,date_from
                    if partial_line.create_date[:10] <= date_from:
                        line_amount -= partial_line.amount
                if form['display_type'] == 'summary':
                    partners_amount[line.partner_id.id] += line_amount
                    #print "===summary==",line_amount
                if form['display_type'] in ('detail','salesperson','partner'):
                    partners_amount[line.id] = line_amount
                    #print "===detail==",line_amount
            history.append(partners_amount)
        #print "=====history=====",future_past
        for partner in partners:
            values = {}
            at_least_one_amount = True
            # Query here is replaced by one query which gets the all the partners their 'after' value
            after = False
            #print "==after==",partner['id'],future_past
            if partner['id'] in future_past:  # Making sure this partner actually was found by the query
                after = [future_past[partner['id']]]

            self.total_account[6] = self.total_account[6] + (after and after[0] or 0.0)
            values['direction'] = after and after[0] or 0.0
            #print "==values['direction']===",values['direction']
            if not float_is_zero(values['direction'], precision_rounding=user.company_id.currency_id.rounding):
                at_least_one_amount = True

            for i in range(5):
                during = False
                if partner['id'] in history[i]:
                    during = [history[i][partner['id']]]
                # Adding counter
                self.total_account[(i)] = self.total_account[(i)] + (during and during[0] or 0)
                #print "===self.total_account[(i)]===",self.total_account[(i)]
                values[str(i)] = during and during[0] or 0.0
                if not float_is_zero(values[str(i)], precision_rounding=user.company_id.currency_id.rounding):
                    at_least_one_amount = True
            values['total'] = sum([values['direction']] + [values[str(i)] for i in range(5)])
            ## Add for total
            self.total_account[(i + 1)] += values['total']
            values['id'] = partner['id']
            values['name'] = partner['name']
            values['uppername'] = partner['uppername']
            values['date'] = ''
            values['number'] = ''
            values['invoice'] = ''
            values['ref'] = ''
            #values['user_id'] = ''
            #values['invoice_reason'] = ''
            if form['display_type'] == 'detail' or form['display_type'] == 'salesperson' or form['display_type'] == 'partner':
                values['date'] = partner['date']
                values['number'] = partner['number']
                values['ref'] = partner['ref']
                values['invoice'] = ''
                #values['user_id'] = ''
                #values['invoice_reason'] = ''
                move_line_obj = self.env['account.move.line']
                move_line = move_line_obj.browse(partner['id'])
                if move_line.move_id:
                    invoice_obj = self.env['account.invoice']
                    invoice_ids = invoice_obj.search([('number','=',move_line.move_id.name)])
                    #invoice_ids = invoice_obj.search(cr, uid, [('number','=',move_line.move_id.name),('type','in',('out_invoice','out_refund'))])
                    if invoice_ids:
                        inv = invoice_ids#invoice_obj.browse(invoice_ids)
                        #print "===invoice_ids==",invoice_ids,inv
                        values['invoice'] = inv.number
                        #values['user_id'] = inv.user_id and inv.user_id.name
                        #values['invoice_reason'] = inv.invoice_reason or ''
            if at_least_one_amount:
                res.append(values)

        total = 0.0
        totals = {}
        for r in res:
            total += float(r['total'] or 0.0)
            for i in range(5) + ['direction']:
                totals.setdefault(str(i), 0.0)
                totals[str(i)] += float(r[str(i)] or 0.0)
        return res

    def _get_move_lines_with_out_partner(self, partner, user_id, form, account_type, date_from, target_move):
        res = []
        
        if form['display_type'] == 'summary':
            #=====
            fill = 'l.partner_id IS NULL'
            part_rel = ''
            part_tot = ''
            res_partner = ''
            #=====
            user = ''
            user_rel = ''
            user_tot = ''
            res_users = ''
        elif form['display_type'] in ('detail', 'salesperson', 'partner'):
            #=====
            fill = 'l.partner_id IS NULL'
            part_rel = ""#"""AND (l.partner_id=res_partner.id) """
            part_tot = ""#"""AND (res_partner.id = """+str(partner.id)+""") """
            res_partner = ""#""" res_partner, """
            #=====
            if form['display_type'] in ('detail', 'partner'):
                user_ids = ''
                user_rel = ''
                user_tot = ''
                res_users = ''
            else:
                user_ids = """AND (res_users.id = """+str(user_id.id)+""") """
                user_rel = """AND (am.user_id=res_users.id) """
                user_tot = """AND (res_users.id = """+str(user_id.id)+""") """
                res_users = """ res_users, """
            #=====
            
        cr = self.env.cr
        uid = self.env.uid
        move_state = ['draft', 'posted']
        if target_move == 'posted':
            move_state = ['posted']

        user = self.env['res.users'].browse(uid)
        user_company = user.company_id.id
        ## put a total of 0
        for i in range(7):
            self.total_account.append(0)

        # This dictionary will store the not due amount of the unknown partner
        future_past = {'Unknown Partner': 0}
        query = '''SELECT l.id
                FROM '''+ res_partner +''' '''+ res_users +''' account_move_line AS l, account_account, account_move am
                WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                    AND (am.state IN %s)
                    AND (account_account.internal_type IN %s)
                    AND (COALESCE(l.date_maturity,l.date) > %s)
                    AND '''+ fill +'''
                    '''+ part_rel +'''
                    '''+ part_tot +'''
                    '''+ user_rel +'''
                    '''+ user_tot +'''
                AND (l.date <= %s)
                AND l.company_id = %s'''
        #print "===query===",query
        cr.execute(query, (tuple(move_state), tuple(account_type), date_from, date_from, user_company))
        aml_ids = cr.fetchall()
        aml_ids = aml_ids and [x[0] for x in aml_ids] or []
        for line in self.env['account.move.line'].browse(aml_ids):
            line_amount = line.balance
            if line.balance == 0:
                continue
            for partial_line in line.matched_debit_ids:
                if partial_line.create_date[:10] <= date_from:
                    line_amount += partial_line.amount
            for partial_line in line.matched_credit_ids:
                if partial_line.create_date[:10] <= date_from:
                    line_amount -= partial_line.amount
            future_past['Unknown Partner'] += line_amount

        history = []
        for i in range(5):
            args_list = (tuple(move_state), tuple(account_type))
            dates_query = '(COALESCE(l.date_maturity,l.date)'
            if form[str(i)]['start'] and form[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s)'
                args_list += (form[str(i)]['start'], form[str(i)]['stop'])
            elif form[str(i)]['start']:
                dates_query += ' > %s)'
                args_list += (form[str(i)]['start'],)
            else:
                dates_query += ' < %s)'
                args_list += (form[str(i)]['stop'],)
            args_list += (date_from, user_company)
            query = '''SELECT l.id
                    FROM ''' + res_partner + ''' ''' + res_users + ''' account_move_line AS l, account_account, account_move am
                    WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                        AND (am.state IN %s)
                        AND (account_account.internal_type IN %s)
                        AND '''+ fill +'''
                        AND ''' + dates_query + '''
                        ''' + part_rel + '''
                        ''' + part_tot + '''
                        ''' + user_rel + '''
                        ''' + user_tot + '''
                    AND (l.date <= %s)
                    AND l.company_id = %s'''
            cr.execute(query, args_list)
            history_data = {'Unknown Partner': 0}
            aml_ids = cr.fetchall()
            aml_ids = aml_ids and [x[0] for x in aml_ids] or []
            for line in self.env['account.move.line'].browse(aml_ids):
                line_amount = line.balance
                if line.balance == 0:
                    continue
                for partial_line in line.matched_debit_ids:
                    if partial_line.create_date[:10] <= date_from:
                        line_amount += partial_line.amount
                for partial_line in line.matched_credit_ids:
                    if partial_line.create_date[:10] <= date_from:
                        line_amount -= partial_line.amount
                #history_data['Unknown Partner'] += line_amount
                if form['display_type'] == 'summary':
                    history_data['Unknown Partner'] += line_amount
                if form['display_type'] in ('detail','salesperson','partner'):
                    history_data['Unknown Partner'] = line_amount
            history.append(history_data)

        values = {}
        after = False
        if 'Unknown Partner' in future_past:
            after = [future_past['Unknown Partner']]
        self.total_account[6] = self.total_account[6] + (after and after[0] or 0.0)
        values['direction'] = after and after[0] or 0.0

        for i in range(5):
            during = False
            if 'Unknown Partner' in history[i]:
                during = [history[i]['Unknown Partner']]
            self.total_account[(i)] = self.total_account[(i)] + (during and during[0] or 0)
            values[str(i)] = during and during[0] or 0.0

        values['total'] = sum([values['direction']] + [values[str(i)] for i in range(5)])
        ## Add for total
        self.total_account[(i + 1)] += values['total']
        values['name'] = _('Unknown Partner')
        values['date'] = ''
        values['number'] = ''
        values['invoice'] = ''
        values['ref'] = ''
        #values['user_id'] = ''
        #values['invoice_reason'] = ''
        if values['total']:
            res.append(values)

        total = 0.0
        totals = {}
        for r in res:
            total += float(r['total'] or 0.0)
            for i in range(5) + ['direction']:
                totals.setdefault(str(i), 0.0)
                totals[str(i)] += float(r[str(i)] or 0.0)
        return res
    
    def _get_partner_move_lines_sum(self, form, account_type, date_from, target_move):
        #print "=---_get_partner_move_lines_sum---=", form, account_type, date_from, target_move
        res = []
        self.total_account = []
        cr = self.env.cr
        uid = self.env.uid
        move_state = ['draft', 'posted']
        if target_move == 'posted':
            move_state = ['posted']

        user = self.env['res.users'].browse(uid)
        user_company = user.company_id.id
        
        arg_list = (tuple(move_state), tuple(account_type))
        #build the reconciliation clause to see what partner needs to be printed
        if form['with_zero_balance']:
            reconciliation_clause = ''
        else:
            reconciliation_clause = 'AND (l.reconciled IS FALSE)'
        cr.execute('SELECT debit_move_id, credit_move_id FROM account_partial_reconcile where create_date > %s', (date_from,))
        reconciled_after_date = []
        for row in cr.fetchall():
            if form['with_zero_balance']:
                reconciled_after_date = ''
            else:
                reconciled_after_date += [row[0], row[1]]
        if reconciled_after_date:
            if form['with_zero_balance']:
                reconciliation_clause = ''
            else:
                reconciliation_clause = 'AND (l.reconciled IS FALSE OR l.id IN %s)'
            #print "=====reconciled_after_date====",reconciled_after_date
            arg_list += (tuple(reconciled_after_date),)
        arg_list += (date_from, user_company)
        query = '''
            SELECT DISTINCT res_partner.id AS id, res_partner.name AS name, UPPER(res_partner.name) AS uppername
            /*, l.date AS date, l.date_maturity AS date_due, account_account.name AS account_name*/
            FROM res_partner,account_move_line AS l, account_account, account_move am
            WHERE (l.account_id = account_account.id)
                AND (l.move_id = am.id)
                AND (am.state IN %s)
                AND (account_account.internal_type IN %s)
                ''' +  reconciliation_clause + '''
                AND (l.partner_id = res_partner.id)
                AND (l.date <= %s)
                AND l.company_id = %s
            ORDER BY UPPER(res_partner.name)'''
        cr.execute(query, arg_list)
        #print "===reconciliation_clause====",reconciliation_clause
        partners = cr.dictfetchall()
        #print "===partners===",query,arg_list
        # put a total of 0
#         for i in range(7):
#             self.total_account.append(0)

        # Build a string like (1,2,3) for easy use in SQL query
        partner_ids = [partner['id'] for partner in partners]
        if not partner_ids:
            return []

        # This dictionary will store the not due amount of all partners
        future_past = {}
        future_past_debit = {}
        future_past_credit = {}
        query = '''SELECT l.id
                FROM account_move_line AS l, account_account, account_move am
                WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                    AND (am.state IN %s)
                    AND (account_account.internal_type IN %s)
                    AND (l.partner_id IN %s)
                AND (l.date <= %s)
                AND l.company_id = %s'''
        cr.execute(query, (tuple(move_state), tuple(account_type), tuple(partner_ids), date_from, user_company))
        aml_ids = cr.fetchall()
        aml_ids = aml_ids and [x[0] for x in aml_ids] or []
        amls = []
        #print "====aml_ids====",query,tuple(move_state), tuple(account_type), date_from, tuple(partner_ids), date_from, user_company
        for line in self.env['account.move.line'].browse(aml_ids):
            if line.partner_id.id not in future_past:
                future_past[line.partner_id.id] = 0.0
            if line.partner_id.id not in future_past_debit:
                future_past_debit[line.partner_id.id] = 0.0
            if line.partner_id.id not in future_past_credit:
                future_past_credit[line.partner_id.id] = 0.0
            
            line_amount = line.balance
            line_debit = line.debit
            line_credit = line.credit
            #print "--line_amount--",line,line_amount,line.debit,line.credit
            if line.balance == 0:
                continue
            for partial_line in line.matched_debit_ids:
                if partial_line.create_date[:10] <= date_from:
                    line_amount += partial_line.amount
                    #print "---matched_debit_ids.amount---",line_amount
            for partial_line in line.matched_credit_ids:
                if partial_line.create_date[:10] <= date_from:
                    line_amount -= partial_line.amount
                    #print "---matched_credit_ids.amount---",line_amount
            future_past[line.partner_id.id] += line_amount
            future_past_debit[line.partner_id.id] += line_debit
            future_past_credit[line.partner_id.id] += line_credit
            #if line
            if form['result_selection'] == 'supplier' and line.balance < 0.0:
                amls.append(line.id)
            elif form['result_selection'] == 'customer' and line.balance > 0.0:
                amls.append(line.id)

        for partner in partners:
            #print "====partner===",partner
            at_least_one_amount = True
            values = {}
            # Query here is replaced by one query which gets the all the partners their 'after' value
            after = after_debit = after_credit = False
            if partner['id'] in future_past:  # Making sure this partner actually was found by the query
                after = [future_past[partner['id']]]
            if partner['id'] in future_past_debit:  # Making sure this partner actually was found by the query
                after_debit = [future_past_debit[partner['id']]]
            if partner['id'] in future_past_credit:  # Making sure this partner actually was found by the query
                after_credit = [future_past_credit[partner['id']]]
 
            #self.total_account[6] = self.total_account[6] + (after and after[0] or 0.0)
            values['direction'] = after and after[0] or 0.0
            values['dir_debit'] = after_debit and after_debit[0] or 0.0
            values['dir_credit'] = after_credit and after_credit[0] or 0.0
            if not float_is_zero(values['direction'], precision_rounding=user.company_id.currency_id.rounding):
                at_least_one_amount = True
            values['total'] = sum([values['direction']])
            values['total_debit'] = sum([values['dir_debit']])
            values['total_credit'] = sum([values['dir_credit']])
            ## Add for total
            values['date'] = ''#partner['date']
            values['date_due'] = ''#partner['date_due']
            values['name'] = partner['name']
            values['account_name'] = ''#partner['account_name']
            values['amls'] = amls
            values['id'] = partner['id']
            #print "====aml_ids=====",aml_ids
            if at_least_one_amount:
                res.append(values)
        return res
    
    #===========================================================================
    # END OF AGED
    #===========================================================================
    
    def _get_partner_move_lines_payment(self, partner, result_selection, aml_ids):
        res = []        
        cr = self.env.cr
        uid = self.env.uid
        move_obj = self.env['account.move.line']
        move_lines = move_obj.search([('id','in',aml_ids),('partner_id','=',partner)])
        for line in move_lines:
            res.append(line)
        return res

    def _get_partner_move_lines_reconciled(self, result_selection, aml_id):
        res = []        
        cr = self.env.cr
        uid = self.env.uid
        if result_selection == 'customer':
            reconcile_ids = self.env['account.partial.reconcile'].search([('debit_move_id','=',aml_id)])
        elif result_selection == 'supplier':
            reconcile_ids = self.env['account.partial.reconcile'].search([('credit_move_id','=',aml_id)])
        if reconcile_ids:
            for rline in reconcile_ids:
                res.append(rline)
        return res
    
    def _get_move_lines_with_out_partner_sum(self, form, account_type, date_from, target_move):
        res = []
        cr = self.env.cr
        uid = self.env.uid
        move_state = ['draft', 'posted']
        if target_move == 'posted':
            move_state = ['posted']

        user = self.env['res.users'].browse(uid)
        user_company = user.company_id.id
        ## put a total of 0
        for i in range(7):
            self.total_account.append(0)

        # This dictionary will store the not due amount of the unknown partner
        future_past = {'Unknown Partner': 0}
        query = '''SELECT l.id
                FROM account_move_line AS l, account_account, account_move am
                WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                    AND (am.state IN %s)
                    AND (account_account.internal_type IN %s)
                    AND (COALESCE(l.date_maturity,l.date) > %s)\
                    AND (l.partner_id IS NULL)
                AND (l.date <= %s)
                AND l.company_id = %s'''
        cr.execute(query, (tuple(move_state), tuple(account_type), date_from, date_from, user_company))
        aml_ids = cr.fetchall()
        aml_ids = aml_ids and [x[0] for x in aml_ids] or []
        for line in self.env['account.move.line'].browse(aml_ids):
            line_amount = line.balance
            if line.balance == 0:
                continue
            for partial_line in line.matched_debit_ids:
                if partial_line.create_date[:10] <= date_from:
                    line_amount += partial_line.amount
            for partial_line in line.matched_credit_ids:
                if partial_line.create_date[:10] <= date_from:
                    line_amount -= partial_line.amount
            future_past['Unknown Partner'] += line_amount

        history = []
        for i in range(5):
            args_list = (tuple(move_state), tuple(account_type))
            dates_query = '(COALESCE(l.date_maturity,l.date)'
            if form[str(i)]['start'] and form[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s)'
                args_list += (form[str(i)]['start'], form[str(i)]['stop'])
            elif form[str(i)]['start']:
                dates_query += ' > %s)'
                args_list += (form[str(i)]['start'],)
            else:
                dates_query += ' < %s)'
                args_list += (form[str(i)]['stop'],)
            args_list += (date_from, user_company)
            query = '''SELECT l.id
                    FROM account_move_line AS l, account_account, account_move am
                    WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                        AND (am.state IN %s)
                        AND (account_account.internal_type IN %s)
                        AND (l.partner_id IS NULL)
                        AND ''' + dates_query + '''
                    AND (l.date <= %s)
                    AND l.company_id = %s'''
            cr.execute(query, args_list)
            history_data = {'Unknown Partner': 0}
            aml_ids = cr.fetchall()
            aml_ids = aml_ids and [x[0] for x in aml_ids] or []
            for line in self.env['account.move.line'].browse(aml_ids):
                line_amount = line.balance
                if line.balance == 0:
                    continue
                for partial_line in line.matched_debit_ids:
                    if partial_line.create_date[:10] <= date_from:
                        line_amount += partial_line.amount
                for partial_line in line.matched_credit_ids:
                    if partial_line.create_date[:10] <= date_from:
                        line_amount -= partial_line.amount
                history_data['Unknown Partner'] += line_amount
            history.append(history_data)

        values = {}
        after = False
        if 'Unknown Partner' in future_past:
            after = [future_past['Unknown Partner']]
        self.total_account[6] = self.total_account[6] + (after and after[0] or 0.0)
        values['direction'] = after and after[0] or 0.0

        for i in range(5):
            during = False
            if 'Unknown Partner' in history[i]:
                during = [history[i]['Unknown Partner']]
            self.total_account[(i)] = self.total_account[(i)] + (during and during[0] or 0)
            values[str(i)] = during and during[0] or 0.0

        values['total'] = sum([values['direction']] + [values[str(i)] for i in range(5)])
        ## Add for total
        self.total_account[(i + 1)] += values['total']
        values['name'] = _('Unknown Partner')

        if values['total']:
            res.append(values)

        total = 0.0
        totals = {}
        for r in res:
            total += float(r['total'] or 0.0)
            for i in range(5) + ['direction']:
                totals.setdefault(str(i), 0.0)
                totals[str(i)] += float(r[str(i)] or 0.0)
        return res
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
