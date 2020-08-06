# -*- coding: utf-8 -*-

from odoo import api, models


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.model
    def _check_selection_field_value(self, field, value):
        if field == 'report_type' and value == 'xls':
            return
        return super(IrActionsReport, self)._check_selection_field_value(field, value)
