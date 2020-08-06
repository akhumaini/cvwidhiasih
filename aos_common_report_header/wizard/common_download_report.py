
import time
from odoo import api, fields, models

class CommonDownloadReportSave(models.TransientModel):
    _name = "common.download.report.save"
     
    name = fields.Char('filename', readonly=True)
    data = fields.Binary('file', readonly=True)
    