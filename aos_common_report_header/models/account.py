# -*- coding: utf-8 -*-

from odoo.osv import expression
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class account_financial_report(models.Model):
    _inherit = "account.financial.report"
    _description = "Account Report"
    _order = "sequence, parent_left asc"
    _parent_order = "code"
    _parent_store = True
    
    code = fields.Char('Code', size=64, required=False, select=1)
    name = fields.Char('Report Name', required=True, translate=True)
    parent_left = fields.Integer('Parent Left', index=True)
    parent_right = fields.Integer('Parent Right', index=True)
    account_report_ids = fields.Many2many('account.financial.report', 'account_financial_report_ids', 'report_id', 'account_report_id', 'Report Values')
    type = fields.Selection([
        ('view', 'View'),
        ('sum', 'Balance'),
        ('accounts', 'Accounts'),
        ('account_type', 'Account Type'),
        ('account_report', 'Report Value'),
        ('account_report_monthly', 'Report Value (Monthly)'),
        ], 'Type', default='view')
    child_level = fields.Integer('Child Level')
    style_font_xls = fields.Selection([
        ('normal', 'Normal Text'),
        ('italic', 'Italic Text'),
        ('bold', 'Bold Text'),
        ], 'Report Font Style Excel', default='normal',
        help="You can set up here the format you want this record to be displayed. If you leave the automatic formatting, it will be computed based on the financial reports hierarchy (auto-computed field 'level').")
    color_font_xls = fields.Selection([
        ('colour_index_black', 'Black'),
        ('colour_index_grey', 'Grey'),
        ('colour_index_red', 'Red'),
        ('colour_index_blue', 'Blue'),
        ], 'Report Color Font Style Excel', default='colour_index_black',
        help="You can set up here the format you want this record to be displayed. If you leave the automatic formatting, it will be computed based on the financial reports hierarchy (auto-computed field 'level').")
    color_fill_xls = fields.Selection([
        ('fill_white', 'White'),
        ('fill_blue', 'Blue'),
        ('fill_grey', 'Grey'),
        ], 'Report Fill Style Excel', default='fill_white',
        help="You can set up here the format you want this record to be displayed. If you leave the automatic formatting, it will be computed based on the financial reports hierarchy (auto-computed field 'level').")
    border_xls = fields.Selection([
        ('borders_all', 'All'),
        ('borders_top_bottom', 'Top Bottom'),
        ], 'Report Borders Style Excel', default='borders_all',
        help="You can set up here the format you want this record to be displayed. If you leave the automatic formatting, it will be computed based on the financial reports hierarchy (auto-computed field 'level').")
    report_method  = fields.Selection([
        ('profit_loss', 'Profit & Loss'),
        ('balance', 'Balance'),
        ('none', 'None'),
        ], 'Report Method', default='none',)
    date_range_type = fields.Selection([
        ('start_year', 'Start Year'),
        ('current', 'Current Year'),
        ('last_year', 'Last Year'),
        ('total', 'Total'),
        ('none', 'None'),
        ], 'Date Range Method', default='none',)
    strict_range = fields.Boolean('Strict Range Date')
    child_level = fields.Integer('Child Level')
    special_date_changer = fields.Selection([('from_beginning', 'From the beginning'), 
        ('to_beginning_of_period', 'At the beginning of the period'), 
        ('normal', 'Use given dates'), 
        ('strict_range', 'Force given dates for all accounts and account types')], default='normal')
    
    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code of the account must be unique !')
    ]
    #COMMENT
    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&'] + domain
        accounts = self.search(domain + args, limit=limit)
        return accounts.name_get()


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    
    @api.model
    def _query_get_daily(self, domain=None):
        context = dict(self._context or {})
        domain = domain and safe_eval(domain) or []

        date_field = 'date'
        if context.get('aged_balance'):
            date_field = 'date_maturity'
        if context.get('date_from'):
            domain += [(date_field, '>=', context['date_from'])]
        if context.get('date_to'):
            domain += [(date_field, '<=', context['date_to'])]

        if context.get('journal_ids'):
            domain += [('journal_id', 'in', context['journal_ids'])]

        state = context.get('state')
        if state and state.lower() != 'all':
            domain += [('move_id.state', '=', state)]

        if context.get('company_id'):
            domain += [('company_id', '=', context['company_id'])]

        if 'company_ids' in context:
            domain += [('company_id', 'in', context['company_ids'])]

        if context.get('reconcile_date'):
            domain += ['|', ('reconciled', '=', False), '|', ('matched_debit_ids.create_date', '>', context['reconcile_date']), ('matched_credit_ids.create_date', '>', context['reconcile_date'])]

        where_clause = ""
        where_clause_params = []
        tables = ''
        if domain:
            query = self._where_calc(domain)
            tables, where_clause, where_clause_params = query.get_sql()
        return tables, where_clause, where_clause_params
