# -*- coding: utf-8 -*-

#import cStringIO

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
    
from odoo import models, api, _, fields

#from odoo.report.report_sxw import report_sxw
from odoo.addons.web.controllers.main import ExcelExport
from odoo.api import Environment
from datetime import datetime, timedelta

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

import logging
_logger = logging.getLogger(__name__)

try:
    import xlwt
    from xlwt.Style import default_style
except ImportError:
    _logger.debug('Can not import xls writer`.')


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

class ReportXls(ExcelExport):
    xls_types = {
        'bool': xlwt.Row.set_cell_boolean,
        'date': xlwt.Row.set_cell_date,
        'text': xlwt.Row.set_cell_text,
        'number': xlwt.Row.set_cell_number,
    }
    xls_types_default = {
        'bool': False,
        'date': None,
        'text': '',
        'number': 0,
    }

    # TO DO: move parameters infra to configurable data

    # header/footer
    hf_params = {
        'font_size': 8,
        'font_style': 'I',  # B: Bold, I:  Italic, U: Underline
    }

    # styles
    _pfc = '26'  # default pattern fore_color
    _bc = '22'   # borders color
    decimal_format = '#,##0.00'
    date_format = 'YYYY-MM-DD'
    xls_styles = {
        'xls_title': 'font: bold true, height 240;',
        'normal': '',
        'bold': 'font: bold true;',
        'underline': 'font: underline true;',
        'italic': 'font: italic true;',
        'fill': 'pattern: pattern solid, fore_color %s;' % _pfc,
        'fill_white': 'pattern: pattern solid, fore_color white;',
        'fill_blue': 'pattern: pattern solid, fore_color 27;',
        'fill_grey': 'pattern: pattern solid, fore_color 22;',
        'colour_index_black': 'font: colour_index black;',
        'colour_index_blue': 'font: colour_index blue;',
        'colour_index_red': 'font: colour_index red;',
        'colour_index_grey': 'font: colour_index grey;',
        'borders_top_bottom': 'borders: bottom thin, top thin;',
        'borders_all':
            'borders: '
            'left thin, right thin, top thin, bottom thin, '
            'left_colour %s, right_colour %s, '
            'top_colour %s, bottom_colour %s;'
            % (_bc, _bc, _bc, _bc),
        'left': 'align: horz left;',
        'center': 'align: horz center;',
        'right': 'align: horz right;',
        'wrap': 'align: wrap true;',
        'top': 'align: vert top;',
        'bottom': 'align: vert bottom;',
    }
    def create(self, cr, uid, ids, data, context=None):
        self.env = Environment(cr, uid, context)
        report_obj = self.env['ir.actions.report']
        report = report_obj.search([('report_name', '=', self.name[7:])])
        if report.ids:
            self.title = report.name
            if report.report_type == 'xls':
                return self.create_xlsx_report(ids, data, report)
        return super(ReportXls, self).create(cr, uid, ids, data, context)

    def create_xlsx_report(self, ids, data, report):
        self.parser_instance = self.parser(
            self.env.cr, self.env.uid, self.name2, self.env.context)
        objs = self.getObjects(
            self.env.cr, self.env.uid, ids, self.env.context)
        self.parser_instance.set_context(objs, data, ids, 'xls')
        file_data = io.StringIO()
        wb = xlwt.Workbook(encoding='utf-8')
        _p = AttrDict(self.parser_instance.localcontext)
        _xs = self.xls_styles
        self.xls_headers = {
            'standard': '',
        }
#         report_date = format_datetime.context_timestamp(
#             cr, uid, datetime.now(), context)
#         report_date = datetime.strptime(fields.Date.context_today(self), DF)
#         report_date = report_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        self.xls_footers = {
            'standard': (
                '&L&%(font_size)s&%(font_style)s'
                '&R&%(font_size)s&%(font_style)s&P / &N'
                ) % self.hf_params,
        }
        self.generate_xls_report(_p, _xs, data, objs, wb)
        n = io.StringIO()
        wb.save(n)
        n.seek(0)
        return (n.read(), 'xls')

    def generate_xls_report(self, parser, xls_styles, data, objects, wb):
        raise NotImplementedError()

    def xls_row_template(specs, wanted_list):
        """
        Returns a row template.

        Input :
        - 'wanted_list': list of Columns that will be returned in the
                         row_template
        - 'specs': list with Column Characteristics
            0: Column Name (from wanted_list)
            1: Column Colspan
            2: Column Size (unit = the width of the character ’0′
                            as it appears in the sheet’s default font)
            3: Column Type
            4: Column Data
            5: Column Formula (or 'None' for Data)
            6: Column Style
        """
        r = []
        col = 0
        for w in wanted_list:
            found = False
            for s in specs:
                if s[0] == w:
                    found = True
                    s_len = len(s)
                    c = list(s[:5])
                    # set write_cell_func or formula
                    if s_len > 5 and s[5] is not None:
                        c.append({'formula': s[5]})
                    else:
                        c.append({
                            'write_cell_func': ReportXls.xls_types[c[3]]})
                    # Set custom cell style
                    if s_len > 6 and s[6] is not None:
                        c.append(s[6])
                    else:
                        c.append(None)
                    # Set cell formula
                    if s_len > 7 and s[7] is not None:
                        c.append(s[7])
                    else:
                        c.append(None)
                    r.append((col, c[1], c))
                    col += c[1]
                    break
            if not found:
                _logger.warn("ReportXls.xls_row_template, "
                             "column '%s' not found in specs", w)
        return r

    def xls_write_row(ws, row_pos, row_data,
                      row_style=default_style, set_column_size=False):
        r = ws.row(row_pos)
        for col, size, spec in row_data:
            data = spec[4]
            formula = spec[5].get('formula') and \
                xlwt.Formula(spec[5]['formula']) or None
            style = spec[6] and spec[6] or row_style
            if not data:
                # if no data, use default values
                data = ReportXls.xls_types_default[spec[3]]
            if size != 1:
                if formula:
                    ws.write_merge(
                        row_pos, row_pos, col, col + size - 1, data, style)
                else:
                    ws.write_merge(
                        row_pos, row_pos, col, col + size - 1, data, style)
            else:
                if formula:
                    ws.write(row_pos, col, formula, style)
                else:
                    spec[5]['write_cell_func'](r, col, data, style)
            if set_column_size:
                ws.col(col).width = spec[2] * 256
        return row_pos + 1