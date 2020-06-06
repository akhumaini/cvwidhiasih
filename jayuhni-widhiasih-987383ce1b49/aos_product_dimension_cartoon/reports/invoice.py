from odoo import models
from io import BytesIO
from odoo.tools.misc import formatLang, format_date as odoo_format_date

from PIL import Image
import base64


	
class InvoiceReportXlsx(models.AbstractModel):
	_name = 'report.aos_product_dimension_cartoon.invoice_report_xlsx'
	_inherit = 'report.report_xlsx.abstract'


	def _add_header(self, sheet, data, record, workbook):
		quo_header_format = workbook.add_format({
			'bold':1,
		})
		

		# single record
		sheet.write('A4','Seller Details',quo_header_format)
		
		
		sheet.write('A5','Name',quo_header_format)
		sheet.write('C5', record.company_id.display_name)
		
		sheet.write('A6','Address', quo_header_format)
		sheet.write('C6', record.company_id.partner_id.contact_address)
		
		sheet.write('A7','Phone No.', quo_header_format)
		sheet.write('C7', record.company_id.partner_id.phone)

		sheet.write('A8','Email Address', quo_header_format)
		sheet.write('C8', record.company_id.partner_id.email)

		sheet.write('A10','Buyer Detail', quo_header_format)
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
		
		sheet.write('M%s' % row,'Invoice No', quo_header_format)
		sheet.write('P%s' % row,record.name or '-')

		row+=1
		sheet.write('M%s' % row,'Invoice Date', quo_header_format or '-')
		sheet.write('P%s' % row,record.date_invoice)

		row+=1
		sheet.write('M%s' % row,'Sales Person', quo_header_format or '-')
		sheet.write('P%s' % row,record.user_id.name)

		row+=1
		sheet.write('M%s' % row,'Mobile', quo_header_format)
		sheet.write('P%s' % row,record.user_id.partner_id.mobile or '-')

		row+=1
		sheet.write('M%s' % row,'Emails', quo_header_format)
		sheet.write('P%s' % row,record.user_id.partner_id.email or '-')

		row+=1
		sheet.write('M%s' % row,'Sales Terms', quo_header_format)
		sheet.write('P%s' % row,record.incoterms_id.display_name or '-')

		row+=1
		sheet.write('M%s' % row,'Estimated Deliveries', quo_header_format)
		sheet.write('P%s' % row, odoo_format_date(env=record.env, value=record.estimated_delivery_date) or '')

		row+=1
		sheet.write('M%s' % row,'Port of Loading', quo_header_format)
		sheet.write('P%s' % row, record.port_loading_id.name or '')

		row+=1
		sheet.write('M%s' % row,'Payment Terms', quo_header_format)
		sheet.write('P%s' % row,record.payment_term_id.display_name or '')

		row+=1
		sheet.write('M%s' % row,'Bank Name', quo_header_format)
		sheet.write('P%s' % row, record.bank_account_id.display_name or '')

		row+=1
		sheet.write('M%s' % row,'Bank Addr', quo_header_format)
		sheet.write('P%s' % row, record.bank_account_id.address or '')

		row+=1
		sheet.write('M%s' % row,'Bank A/C', quo_header_format)
		sheet.write('P%s' % row, record.bank_account_id.bank_acc_number or '')

		row+=1
		sheet.write('M%s' % row,'Swift Code', quo_header_format)
		sheet.write('P%s' % row, record.bank_account_id.swift_code or '')

		sheet.freeze_panes(row+2, 0)
		sheet.set_row(row+2, 40)

		return row

	def _add_content_table_header(self, sheet, data, record, workbook, row):

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

		sheet.merge_range('I%s:I%s' % (row,(row+1),), 'QTY / CTN', header_format)

		# CASE PACK SIZE
		sheet.merge_range('J%s:L%s' % (row, row,), 'CASE PACK SIZE (%s)' % record.partner_uom_id.name, header_format)
		sheet.write('J%s' % (row+1),'L', header_format)
		sheet.write('K%s' % (row+1),'W', header_format)
		sheet.write('L%s' % (row+1),'H', header_format)

		sheet.merge_range('M%s:M%s' % (row,(row+1),), 'CBM / CTN', header_format)

		sheet.merge_range('N%s:N%s' % (row,(row+1),), 'QTY CARTOON', header_format)

		sheet.merge_range('O%s:O%s' % (row,(row+1),), 'TOTAL QTY', header_format)

		sheet.merge_range('P%s:P%s' % (row,(row+1),), 'TOTAL CBM', header_format)

		sheet.merge_range('Q%s:Q%s' % (row,(row+1),), 'PRICE', header_format)

		sheet.merge_range('R%s:R%s' % (row,(row+1),), 'TOTAL AMOUNT', header_format)

		return row+1

	def _write_line(self, sheet, line, row, seq, workbook):
		line_format = workbook.add_format({
			'border':1
		})

		sheet.write('A%s' % row, seq, line_format)

		sheet.write('B%s' % row, line.product_id.default_code or '', line_format)

		sheet.write('C%s' % row, line.name or '', line_format)

		if line.product_id.image_medium:
			base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
			url = '%s/%s' % (base_url, 'web/image?model=%s&field=%s&id=%s' % ('product.product','image_medium',line.product_id.id))
			# sheet.write('D%s' % row, url, line_format)
			# image_data = BytesIO(urlopen(url).read())
			
			f = BytesIO(base64.b64decode(line.product_id.image_medium))

			imgoptions = {'y_scale': 0.9, 'image_data':f, 'x_offset': 15}
			sheet.insert_image('D%s' % row, 'product%s.jpg' % (line.product_id.default_code,), imgoptions)
		else:
			sheet.write('D%s' % row, '-', line_format)


		sheet.write('E%s' % row, line.buyer_remarks or '', line_format)

		sheet.write('F%s' % row, line.item_size_l, line_format)
		sheet.write('G%s' % row, line.item_size_w, line_format)
		sheet.write('H%s' % row, line.item_size_h, line_format)

		sheet.write('I%s' % row, line.qty_per_ctn, line_format)

		sheet.write('J%s' % row, line.case_pack_size_l, line_format)
		sheet.write('K%s' % row, line.case_pack_size_w, line_format)
		sheet.write('L%s' % row, line.case_pack_size_h, line_format)

		


		sheet.write('M%s' % row, line.cbm_per_ctn, line_format)
		sheet.write('N%s' % row, line.qty_cartoon, line_format)

		sheet.write('O%s' % row, line.quantity, line_format)

		sheet.write('P%s' % row, line.total_cbm, line_format)

		sheet.write('Q%s' % row, line.price_unit, line_format)
		sheet.write('R%s' % row, line.price_subtotal, line_format)

	def generate_xlsx_report(self, workbook, data, records):
		for obj in records:
			report_name = obj.name or 'Draft Invoice'
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
			TITLE = workbook.add_format({
				'bold':1,
				'border':0,
				'align':'center',
				'valign':'vcenter',
				'fg_color':'#d0f7f7',
				'font_size':16
			})
			
			sheet.merge_range('A1:R2', 'INVOICE', TITLE)

			row = self._add_header(sheet, data, obj, workbook)+1

			row = self._add_content_table_header(sheet,data,obj, workbook, row)+1
			start_row = row
			seq = 1
			for line in obj.invoice_line_ids:
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
			sheet.merge_range('A%s:M%s' % (row,row,), 'Grand Total',grand_total_format)

			footer_total_format = workbook.add_format({
				'align':'center',
				'bold':1,
				'border':1,
			})

			sheet.write_formula('N%s' % (row,), 'SUM(N%s:N%s)' % (start_row,(row-1),), footer_total_format)
			sheet.write_formula('O%s' % (row,), 'SUM(O%s:O%s)' % (start_row,(row-1),), footer_total_format)
			sheet.write_formula('P%s' % (row,), 'SUM(P%s:P%s)' % (start_row,(row-1),), footer_total_format)
			sheet.write_formula('Q%s' % (row,), 'SUM(Q%s:Q%s)' % (start_row,(row-1),), footer_total_format)
			sheet.write_formula('R%s' % (row,), 'SUM(R%s:R%s)' % (start_row,(row-1),), footer_total_format)
			