from odoo import models
from io import BytesIO

from PIL import Image
import base64

from odoo.tools.misc import formatLang, format_date as odoo_format_date
	
class PurchaseReportXlsx(models.AbstractModel):
	_name = 'report.aos_product_dimension_cartoon.purchase_report_xlsx'
	_inherit = 'report.report_xlsx.abstract'


	def _write_header(self, sheet, data, record, workbook):
		quo_header_format = workbook.add_format({
			'bold':1,
		})
		

		# single record
		sheet.write('A4','Buyer Details',quo_header_format)
		
		
		sheet.write('A5','Name',quo_header_format)
		sheet.write('C5', record.company_id.display_name)
		
		sheet.write('A6','Address', quo_header_format)
		sheet.write('C6', record.company_id.partner_id.contact_address)
		
		sheet.write('A7','Phone No.', quo_header_format)
		sheet.write('C7', record.company_id.partner_id.phone)

		sheet.write('A8','Email Address', quo_header_format)
		sheet.write('C8', record.company_id.partner_id.email)

		sheet.write('A10','Vendor Detail', quo_header_format)
		sheet.write('C10', record.partner_id.display_name)

		sheet.write('A11','Name', quo_header_format)
		sheet.write('C11', record.partner_id.display_name)


		sheet.write('A12','Address', quo_header_format)
		sheet.write('C12', record.partner_id.contact_address)

		sheet.write('A13','Phone No.', quo_header_format)
		sheet.write('C13', record.partner_id.phone)
		sheet.write('A14','Email Address', quo_header_format)
		sheet.write('C14', record.partner_id.email)



		# RIGHT
		row = 4
		
		sheet.write('G%s' % row,'Purchase No', quo_header_format)
		sheet.write('I%s' % row,record.name)

		row+=1
		sheet.write('G%s' % row,'Purchase Date', quo_header_format)
		sheet.write('I%s' % row,record.date_order)

		row+=1
		sheet.write('G%s' % row,'Purchaser', quo_header_format)
		sheet.write('I%s' % row,record.create_uid.name)

		row+=1
		sheet.write('G%s' % row,'Mobile', quo_header_format)
		sheet.write('I%s' % row,record.create_uid.partner_id.mobile or '')

		row+=1
		sheet.write('G%s' % row,'Emails', quo_header_format)
		sheet.write('I%s' % row,record.create_uid.partner_id.email or '')

		row+=1
		sheet.write('G%s' % row,'Terms', quo_header_format)
		sheet.write('I%s' % row,record.incoterm_id.display_name or '')

		row+=1
		sheet.write('G%s' % row,'Estimated Deliveries', quo_header_format)
		sheet.write('I%s' % row,'')

		row+=1
		sheet.write('G%s' % row,'Payment Terms', quo_header_format)
		sheet.write('I%s' % row,record.payment_term_id.display_name or '')

		# row+=1
		# sheet.write('G%s' % row,'Port of Loading', quo_header_format)
		# sheet.write('I%s' % row,'')

		return row
		

	def _add_quotation_table_header(self, sheet, data, record, workbook, row):

		header_format = workbook.add_format({
			'bold':1,
			'border':1,
			'align':'center',
			'valign':'vcenter',
			
			
		})


		
		sheet.merge_range('A%s:A%s' % (row,(row+1),), 'No.', header_format)

		sheet.merge_range('B%s:B%s' % (row,(row+1),), 'ITEM CODE', header_format)

		sheet.merge_range('C%s:C%s' % (row,(row+1),), 'DESCRIPTION', header_format)
		
		sheet.merge_range('D%s:D%s' % (row,(row+1),), 'PRODUCT IMAGE', header_format)

		sheet.merge_range('E%s:E%s' % (row,(row+1),), 'BUYER REMARKS', header_format)


		# ITEM SIZE
		sheet.merge_range('F%s:H%s' % (row, row,), 'ITEM SIZE (%s)' % record.partner_uom_id.name, header_format)
		sheet.write('F%s' % (row+1),'L', header_format)
		sheet.write('G%s' % (row+1),'W', header_format)
		sheet.write('H%s' % (row+1),'H', header_format)

		

		# CASE PACK SIZE
		
		sheet.merge_range('I%s:I%s' % (row,(row+1),), 'TOTAL QTY', header_format)

		

		sheet.merge_range('J%s:J%s' % (row,(row+1),), 'PRICE', header_format)

		sheet.merge_range('K%s:K%s' % (row,(row+1),), 'TOTAL AMOUNT', header_format)

		return row+1

	def _write_line(self, sheet, line, row, seq, workbook):

		line_format = workbook.add_format({
			'border':1
		})
		sheet.write('A%s' % row, seq, line_format)

		sheet.write('B%s' % row, line.product_id.default_code, line_format)

		sheet.write('C%s' % row, line.name, line_format)

		if line.product_id.image_medium:
			base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
			url = '%s/%s' % (base_url, 'web/image?model=%s&field=%s&id=%s' % ('product.product','image_medium',line.product_id.id))
			
			
			f = BytesIO(base64.b64decode(line.product_id.image_medium))

			sheet.insert_image('D%s' % row, 'product%s.jpg' % (line.product_id.default_code,), {'image_data':f})
		else:
			sheet.write('D%s' % row, '-', line_format)


		

		sheet.write('E%s' % row, line.item_size_l, line_format)
		sheet.write('F%s' % row, line.item_size_w, line_format)
		sheet.write('G%s' % row, line.item_size_h, line_format)

		

		sheet.write('H%s' % row, line.product_qty, line_format)
		sheet.write('I%s' % row, line.price_unit, line_format)
		sheet.write('J%s' % row, line.price_subtotal, line_format)

	def generate_xlsx_report(self, workbook, data, records):
		for obj in records:
			report_name = obj.name
			# One sheet by partner
			sheet = workbook.add_worksheet(report_name[:31])
			sheet.set_column(0,0,4)
			sheet.set_column(1,1,20)
			# C
			sheet.set_column(2,2,40)
			# D
			sheet.set_column(3,3,40)
			# E
			sheet.set_column(4,4,15)

			

			# worksheet.set_column('A:R', 12)
			QUOTATION_TITLE = workbook.add_format({
				'bold':1,
				'border':0,
				'align':'center',
				'valign':'vcenter',
				'fg_color':'#d0f7f7',
				'font_size':16
			})
			sheet.merge_range('A1:R2', 'PURCHASE', QUOTATION_TITLE)

			row = self._write_header(sheet, data, obj, workbook) + 1
			

			row = self._add_quotation_table_header(sheet,data,obj, workbook, row)+1
			start_row = row
			seq = 1
			for line in obj.order_line:
				self._write_line(sheet, line, row, seq=seq, workbook=workbook)
				sheet.set_row((row-1), 100)
				row+=1
				seq+=1
			# write footer total
			
			grand_total_format = workbook.add_format({
				'align':'right',
				'bold':1,
				'border':1,
			})
			sheet.merge_range('A%s:H%s' % (row,row,), 'Grand Total',grand_total_format)

			footer_total_format = workbook.add_format({
				'align':'center',
				'bold':1,
				'border':1,
			})

			sheet.write_formula('I%s' % (row,), 'SUM(I%s:I%s)' % (start_row,(row-1),), footer_total_format)
			sheet.write_formula('J%s' % (row,), 'SUM(J%s:J%s)' % (start_row,(row-1),), footer_total_format)
			sheet.write_formula('K%s' % (row,), 'SUM(K%s:K%s)' % (start_row,(row-1),), footer_total_format)
			