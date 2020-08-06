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

		quo_header_format_border_bottom = workbook.add_format({
			'bold':1,
			'bottom':1,
		})

		quo_header_format_border_right = workbook.add_format({
			'right':1,
		})
		quo_header_format_border_left = workbook.add_format({
			'left':1,
			'bold':1,
		})
		quo_header_format_border_left_bottom = workbook.add_format({
			'left':1,
			'bottom':1,
			'bold':1,
		})

		quo_header_format_border_right_bottom = workbook.add_format({
			'right':1,
			'bottom':1,
			
		})

		quo_header_format_border_left_top = workbook.add_format({
			'left':1,
			'top':1,
		})
		quo_header_format_border_right_top = workbook.add_format({
			'right':1,
			'top':1,
		})

		quo_header_format_border_left_right_top = workbook.add_format({
			'left':1,
			'top':1,
			'right':1,
		})

		quo_header_format_border_left_right_top_bold = workbook.add_format({
			'left':1,
			'top':1,
			'right':1,
			'bold':1,
		})
		

		addr_format = workbook.add_format({
			'bold':1,
		})
		addr_format.set_text_wrap()

		quo_header_format_border = workbook.add_format({
			'bold':1,
			'top':2,
			'left':1,
			'right':1,
		})
		doubledotformat = workbook.add_format({
			'align':'right'
		})

		row=1

		if record.company_id.partner_id.image_medium:
			base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
			url = '%s/%s' % (base_url, 'web/image?model=%s&field=%s&id=%s' % ('res.partner','image_medium',record.company_id.partner_id.id))
			
			
			f = BytesIO(base64.b64decode(record.company_id.partner_id.image_medium))

			
			imgoptions = {'y_scale': 0.9,'x_scale':0.9, 'image_data':f, 'x_offset': 40, 'y_offset':10}
			sheet.insert_image('A%s' % row, 'product%s.jpg' % (record.company_id.partner_id.name,), imgoptions)
		

		# LEFT COMPANY INFO
		# COMPANY NAME IN BIG FONT
		sheet.merge_range("F1:J1", record.company_id.partner_id.name.upper(), workbook.add_format({
			'font_size':24,
			'bold':1,
			'align':'right'
		}))

		company_header2 = workbook.add_format({
			'font_size':11,
			'bold':1,
			'align':'right'
		})

		sheet.merge_range("F2:J2", record.company_id.partner_id.street + ". %s" % (record.company_id.partner_id.street2 or '',)  , company_header2)

		sheet.merge_range("F3:J3", '%s%s%s%s%s' % (
				record.company_id.partner_id.city or '', 
				' - ' if record.company_id.partner_id.state_id.name else '', 
				record.company_id.partner_id.state_id.name or '',
				' - ' if record.company_id.partner_id.country_id.id else '', 
				record.company_id.partner_id.country_id.name or '', 
			), 
			company_header2
		)


		sheet.merge_range("F4:J4", 'Phone: %s' % (record.company_id.partner_id.phone or '',)  , company_header2)
		sheet.merge_range("F5:J5", '%s' % (record.company_id.partner_id.website or '',)  , workbook.add_format({
			'font_size':11,
			'font_color':'green',
			'bold':1,
			'align':'right',
		}))
		sheet.merge_range("F6:J6", '%s' % (record.company_id.report_header or '',)  , workbook.add_format({
			'font_size':11,
			'bold':1,
			'align':'right',
		}))

		

		

		row = header2row = 8
		QUOTATION_TITLE = workbook.add_format({
			'bold':1,
			'border':0,
			'align':'center',
			'valign':'vcenter',
			'fg_color':'#d0f7f7',
			'font_size':14
		})
		
		if record.state in ('draft','sent','to approve'):
			STATUS_CAPTION = 'REQUEST FOR QUOTATION'
		elif record.state in ('cancel'):
			STATUS_CAPTION = 'CANCELED PO'
		elif record.state in ('done','purchase'):
			STATUS_CAPTION = 'PURCHASE ORDER'
		
		sheet.merge_range('A%s:J%s' % (row,row,), STATUS_CAPTION, QUOTATION_TITLE)
		

		# single record		
		row += 1
		sheet.merge_range('A%s:C%s' % (row,row,),'Buyer Details', quo_header_format_border_left_right_top)
		

		row += 1
		sheet.write('A%s' % (row,),'Name',quo_header_format_border_left)
		sheet.write('C%s' % (row,), ': %s' % record.company_id.display_name, quo_header_format_border_right)

		row += 1
		sheet.write('A%s' % (row,),'Address', quo_header_format_border_left)
		sheet.write('C%s' % (row,), ': {} {} {} {}'.format(
			record.company_id.partner_id.street,
			record.company_id.partner_id.street2,
			record.company_id.partner_id.city,
			record.company_id.partner_id.country_id.name,
		), quo_header_format_border_right)

		row += 1
		sheet.write('A%s' % (row,),'Phone No.', quo_header_format_border_left)
		sheet.write('C%s' % (row,), ': %s' % record.company_id.partner_id.phone, quo_header_format_border_right)

		row += 1
		sheet.write('A%s' % (row,),'Email Address', quo_header_format_border_left)
		sheet.write('C%s' % (row,), ': %s' % record.company_id.partner_id.email, quo_header_format_border_right)

		row += 1
		sheet.merge_range('A%s:C%s' % (row,row,),'Vendor Detail', quo_header_format_border_left_right_top)
		# sheet.merge_range('A%s:A%s' % (row,(row+1),), 'No.', header_format)
		# sheet.write%sC % (row,)10', ': %s' % record.partner_id.display_name)

		row += 1
		sheet.write('A%s' % (row,),'Name', quo_header_format_border_left)
		sheet.write('C%s' % (row,), ': %s' % record.partner_id.display_name, quo_header_format_border_right)


		row += 1
		sheet.write('A%s' % (row,),'Address', quo_header_format_border_left)
		sheet.write('C%s' % (row,), ': {} {} {} {}'.format(
			record.partner_id.street,
			record.partner_id.street2,
			record.partner_id.city,
			record.partner_id.country_id.name,
		), quo_header_format_border_right)

		row += 1
		sheet.write('A%s' % (row,),'Phone No.', quo_header_format_border_left)
		sheet.write('C%s' % (row,), ': %s' % record.partner_id.phone, quo_header_format_border_right)

		row += 1
		sheet.merge_range('A%s:B%s' % (row,row,),'Email Address', quo_header_format_border_left_bottom)
		sheet.write('C%s' % (row,), ': %s' % record.partner_id.email, quo_header_format_border_right_bottom)



		# RIGHT
		# row = header2row
		header2row+=1
		sheet.merge_range('I%s:J%s' % (header2row,header2row,),'Purchase Details', quo_header_format_border_left_right_top_bold)

		header2row+=1
		sheet.write('I%s' % header2row,'Purchase No', quo_header_format_border_left)
		sheet.write('J%s' % header2row,': %s' % record.name, quo_header_format_border_right)

		header2row+=1
		sheet.write('I%s' % header2row,'Purchase Date', quo_header_format_border_left)
		sheet.write('J%s' % header2row,': %s' % odoo_format_date(env=record.env, value=record.date_order), quo_header_format_border_right)

		header2row+=1
		sheet.write('I%s' % header2row,'Purchaser', quo_header_format_border_left)
		sheet.write('J%s' % header2row,': %s' % record.create_uid.name, quo_header_format_border_right)

		header2row+=1
		sheet.write('I%s' % header2row,'Mobile', quo_header_format_border_left)
		sheet.write('J%s' % header2row,': %s' % record.create_uid.partner_id.mobile or '' if record.create_uid.partner_id.mobile else '', quo_header_format_border_right)

		header2row+=1
		sheet.write('I%s' % header2row,'Emails', quo_header_format_border_left)
		sheet.write('J%s' % header2row,': %s' % record.create_uid.partner_id.email or '', quo_header_format_border_right)

		header2row+=1
		sheet.write('I%s' % header2row,'Terms', quo_header_format_border_left)
		sheet.write('J%s' % header2row,': %s' % record.incoterm_id.name or '' if record.incoterm_id.id else '', quo_header_format_border_right)

		header2row+=1
		sheet.write('I%s' % header2row,'Estimated Deliveries', quo_header_format_border_left)
		sheet.write('J%s' % header2row,': %s' % (odoo_format_date(env=record.env, value=record.date_planned)), quo_header_format_border_right)

		header2row+=1
		sheet.write('I%s' % header2row,'Payment Terms', quo_header_format_border_left_bottom)
		sheet.write('J%s' % header2row,': %s' % record.payment_term_id.display_name or '', quo_header_format_border_right_bottom)

		# header2row+=1
		# sheet.write('I%s' % header2row,'Port of Loading', quo_header_format)
		# sheet.write('J%s' % header2row,'')

		return row
		

	def _add_quotation_table_header(self, sheet, data, record, workbook, row):

		header_format = workbook.add_format({
			'bold':1,
			'border':1,
			'align':'center',
			'valign':'vcenter',
			
			
		})


		row+=1
		sheet.merge_range('A%s:A%s' % (row,(row+1),), 'No.', header_format)

		sheet.merge_range('B%s:B%s' % (row,(row+1),), 'ITEM CODE', header_format)

		sheet.merge_range('C%s:C%s' % (row,(row+1),), 'DESCRIPTION', header_format)
		
		sheet.merge_range('D%s:D%s' % (row,(row+1),), 'PRODUCT IMAGE', header_format)

		


		# ITEM SIZE
		sheet.merge_range('E%s:G%s' % (row, row,), 'ITEM SIZE (%s)' % record.partner_uom_id.name, header_format)
		sheet.write('E%s' % (row+1),'L', header_format)
		sheet.write('F%s' % (row+1),'W', header_format)
		sheet.write('G%s' % (row+1),'H', header_format)

		

		# CASE PACK SIZE
		
		sheet.merge_range('H%s:H%s' % (row,(row+1),), 'TOTAL QTY', header_format)

		

		sheet.merge_range('I%s:I%s' % (row,(row+1),), 'PRICE', header_format)

		sheet.merge_range('J%s:J%s' % (row,(row+1),), 'TOTAL AMOUNT', header_format)

		return row+1

	def _write_line(self, sheet, line, row, seq, workbook):

		line_format = workbook.add_format({
			'border':1
		})

		numeric_line_format = workbook.add_format({
			'border':1,
			'num_format': '#,##0.00',
		})

		sheet.write('A%s' % row, seq, line_format)

		sheet.write('B%s' % row, line.product_id.default_code, line_format)

		sheet.write('C%s' % row, line.name, line_format)

		if line.product_id.image_medium:
			base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
			url = '%s/%s' % (base_url, 'web/image?model=%s&field=%s&id=%s' % ('product.product','image_medium',line.product_id.id))
			
			
			f = BytesIO(base64.b64decode(line.product_id.image_medium))

			imgoptions = {'y_scale': 0.9,'x_scale':0.9, 'image_data':f, 'x_offset': 10, 'y_offset':10}
			sheet.insert_image('D%s' % row, 'product%s.jpg' % (line.product_id.default_code,), imgoptions)
		else:
			sheet.write('D%s' % row, '-', line_format)


		

		sheet.write('E%s' % row, line.item_size_l, line_format)
		sheet.write('F%s' % row, line.item_size_w, line_format)
		sheet.write('G%s' % row, line.item_size_h, line_format)

		

		sheet.write('H%s' % row, line.product_qty, line_format)
		sheet.write('I%s' % row, line.price_unit, line_format)
		sheet.write('J%s' % row, line.price_subtotal, line_format)

	def _add_footer(self, sheet, data, record, workbook, row):
		bold = workbook.add_format({
			'bold':1,
		})
		wrapped = workbook.add_format({
			'text_wrap':1,
			'align':'top'
		})
		sheet.write('A%s' % row, 'Terms and Conditions:', bold)
		row+=1
		sheet.set_row(row-1, 90)
		sheet.merge_range('A%s:N%s' % (row,row,), record.notes or '', wrapped)
		
		return 

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
			# sheet.set_column(4,4,15)
			# H
			sheet.set_column(7,7,40)
			# I
			sheet.set_column(8,8,40)
			# J
			sheet.set_column(9,9,40)

			

			# worksheet.set_column('A:R', 12)
			# QUOT_TITLE_FORMAT = workbook.add_format({
			# 	'bold':1,
			# 	'border':0,
			# 	'align':'center',
			# 	'valign':'vcenter',
			# 	'fg_color':'#d0f7f7',
			# 	'font_size':16
			# })
			# QUOT_TITLE = 'QUOTATION' if obj.state in ['draft','sent'] else "PURCHASE ORDER"
			# sheet.merge_range('A1:K2', QUOT_TITLE, QUOT_TITLE_FORMAT)

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
			sheet.merge_range('A%s:G%s' % (row,row,), 'Grand Total',grand_total_format)

			footer_total_format = workbook.add_format({
				'align':'center',
				'bold':1,
				'border':1,
			})

			sheet.write_formula('H%s' % (row,), 'SUM(H%s:H%s)' % (start_row,(row-1),), footer_total_format)
			sheet.write_formula('I%s' % (row,), 'SUM(I%s:I%s)' % (start_row,(row-1),), footer_total_format)
			sheet.write_formula('J%s' % (row,), 'SUM(J%s:J%s)' % (start_row,(row-1),), footer_total_format)

			row = row+1
			self._add_footer(sheet=sheet, data=data, record=obj, workbook=workbook, row=row)
			