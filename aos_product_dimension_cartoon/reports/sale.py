from odoo import models,fields
from io import BytesIO
from odoo.tools.misc import formatLang, format_date as odoo_format_date

from PIL import Image
import base64
	
class SaleReportXlsx(models.AbstractModel):
	_name = 'report.aos_product_dimension_cartoon.sale_report_xlsx'
	_inherit = 'report.report_xlsx.abstract'


	def _add_quotation_header(self, sheet, data, record, workbook):
		
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

			
			imgoptions = {'y_scale': 0.9,'x_scale':0.9, 'image_data':f, 'x_offset': 10, 'y_offset':10}
			sheet.insert_image('A%s' % row, 'product%s.jpg' % (record.company_id.partner_id.name,), imgoptions)

		# LEFT COMPANY INFO
		# COMPANY NAME IN BIG FONT
		sheet.merge_range("H1:S1", record.company_id.partner_id.name.upper(), workbook.add_format({
			'font_size':24,
			'bold':1,
			'align':'right'
		}))

		company_header2 = workbook.add_format({
			'font_size':11,
			'bold':1,
			'align':'right'
		})

		sheet.merge_range("H2:S2", record.company_id.partner_id.street + " %s" % (record.company_id.partner_id.street2 or '',)  , company_header2)

		sheet.merge_range("H3:S3", '%s%s%s%s%s' % (
				record.company_id.partner_id.city or '', 
				' - ' if record.company_id.partner_id.state_id.name else '', 
				record.company_id.partner_id.state_id.name or '', 
				' - ' if record.company_id.partner_id.country_id.id else '', 
				record.company_id.partner_id.country_id.name or '', 
			), 
			company_header2
		)


		sheet.merge_range("H4:S4", 'Phone: %s' % (record.company_id.partner_id.phone or '',)  , company_header2)
		sheet.merge_range("H5:S5", '%s' % (record.company_id.partner_id.website or '',)  , workbook.add_format({
			'font_size':11,
			'font_color':'green',
			'bold':1,
			'align':'right',
		}))
		sheet.merge_range("H6:S6", '%s' % (record.company_id.report_header or '',)  , workbook.add_format({
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
		SO_STATUS = dict(record._fields['state'].selection).get(record.state)
		sheet.merge_range('A%s:S%s' % (row,row,), SO_STATUS.upper(), QUOTATION_TITLE)
		

		# single record
		
		row += 1
		
		

		sheet.merge_range('A%s:D%s' % (row,row,), 'Seller Details.', quo_header_format_border)
		row += 1
		sheet.write('A%s' % (row,),'Name:',quo_header_format)

		# sheet.write('B%s' % (row,), ':', doubledotformat)
		sheet.write('C%s' % (row,), ':', quo_header_format)
		sheet.write('D%s' % (row,), record.company_id.display_name, quo_header_format_border_right)

		

		# START ADDRESS
		row += 1
		
		sheet.write('A%s' % (row,),'Address', quo_header_format)

		# sheet.write('B%s' % (row,), ':', doubledotformat)
		sheet.write('C%s' % (row,), ':', quo_header_format)
		sheet.write('D%s' % (row,), '{} {} {} {}'.format(
			record.company_id.partner_id.street,
			record.company_id.partner_id.street2,
			record.company_id.partner_id.city,
			record.company_id.partner_id.country_id.name,
		), quo_header_format_border_right)

		# UNCOMMENT IF SPLITTED
		# sheet.writeC'D%s' % (row,':', quo_header_format)
		# sheet.write('D%s' % (row,), '%s. %s' % (record.company_id.partner_id.street, record.company_id.partner_id.street2,), quo_header_format)

		# row += 1
		# sheet.writeC'D%s' % (row,':', quo_header_format)
		# sheet.write('D%s' % (row,), '%s - %s %s' % (record.company_id.partner_id.city, record.company_id.partner_id.state_id.name,record.company_id.partner_id.zip,), quo_header_format)

		# row += 1
		
		
		# sheet.writeC'D%s' % (row,':', quo_header_format)
		# sheet.write('D%s' % (row,), '%s' % (record.company_id.partner_id.country_id.name,), quo_header_format)

		# END ADDRESS

		row += 1
		sheet.write('A%s' % (row,),'Phone No.', quo_header_format)

		# sheet.write('B%s' % (row,), ':', doubledotformat)
		sheet.write('C%s' % (row,), ':', quo_header_format)
		sheet.write('D%s' % (row,), record.company_id.partner_id.phone or '', quo_header_format_border_right)


		row += 1
		sheet.write('A%s' % (row,),'Email Address', quo_header_format)

		# sheet.write('B%s' % (row,), ':', doubledotformat)
		sheet.write('C%s' % (row,), ':', quo_header_format)
		sheet.write('D%s' % (row,), record.company_id.partner_id.email or '', quo_header_format_border_right)


		row += 1
		# sheet.write('A%s' % (row,),'Buyer Detail', quo_header_format)
		sheet.merge_range('A%s:D%s' % (row,row,), 'Buyer Details.', quo_header_format_border)

		# sheet.write(BC%s' % (row,':', doubledotformat)
		# sheet.writeC'D%s' % (row,':'d.display_name)
		# sheet.write('D%s' % (row,), record.partner_id.display_name)


		row += 1
		sheet.write('A%s' % (row,),'Name', quo_header_format_border_left)

		# sheet.write('B%s' % (row,), ':', doubledotformat)
		sheet.write('C%s' % (row,), ':', quo_header_format)
		sheet.write('D%s' % (row,), record.partner_id.display_name, quo_header_format_border_right)


		row += 1
		sheet.write('A%s' % (row,),'PIC', quo_header_format_border_left)

		# sheet.write('B%s' % (row,), ':', doubledotformat)
		sheet.write('C%s' % (row,), ':', quo_header_format)
		sheet.write('D%s' % (row,), record.pic_id.name or '', quo_header_format_border_right)



		row += 1
		sheet.write('A%s' % (row,),'Address', quo_header_format_border_left)

		# sheet.write('B%s' % (row,), ':', doubledotformat)
		sheet.write('C%s' % (row,), ':', quo_header_format)
		sheet.write('D%s' % (row,), '{} {} {} {}'.format(
			record.partner_id.street,
			record.partner_id.street2,
			record.partner_id.city,
			record.partner_id.country_id.name,
		) , quo_header_format_border_right)


		row += 1
		sheet.write('A%s' % (row,),'Phone No:.', quo_header_format_border_left)

		# sheet.write('B%s' % (row,), ':', doubledotformat)
		sheet.write('C%s' % (row,), ':', quo_header_format)
		sheet.write('D%s' % (row,), record.partner_id.phone or '', quo_header_format_border_right)

		row += 1
		sheet.write('A%s' % (row,),'Email Address', quo_header_format_border_left_bottom)

		# sheet.write('B%s' % (row,), ':', doubledotformat)
		sheet.write('C%s' % (row,), ':', quo_header_format_border_bottom)
		sheet.write('D%s' % (row,), record.partner_id.email or '', quo_header_format_border_bottom)




		# RIGHT
		row = header2row + 1
		
		sheet.write('R%s' % row,'Quotation No', quo_header_format_border_left)
		# sheet.write('R%s' % row, ':', quo_header_format)
		sheet.write('S%s' % row, ": %s" % (record.name,), quo_header_format_border_right)

		row+=1
		sheet.write('R%s' % row,'Quotation Date', quo_header_format_border_right_top)
		# sheet.write('R%s' % row, ':', quo_header_format)
		sheet.write('S%s' % row, ": %s" % (odoo_format_date(env=record.env, value=record.date_order),), quo_header_format_border_right_top)

		row+=1
		sheet.write('R%s' % row,'Sales Person', quo_header_format_border_left)
		# sheet.write('R%s' % row, ':', quo_header_format)
		sheet.write('S%s' % row, ": %s" % (record.user_id.name,), quo_header_format_border_right)
		

		row+=1
		sheet.write('R%s' % row,'Mobile', quo_header_format_border_left)
		# sheet.write('R%s' % row, ':', quo_header_format)
		sheet.write('S%s' % row, ": %s" % (record.user_id.partner_id.mobile or '',), quo_header_format_border_right)

		row+=1
		sheet.write('R%s' % row,'Emails', quo_header_format_border_left)
		# sheet.write('R%s' % row, ':', quo_header_format)
		sheet.write('S%s' % row, ": %s" % (record.user_id.partner_id.email or '',), quo_header_format_border_right)

		row+=1
		sheet.write('R%s' % row,'Sales Terms', quo_header_format_border_left_top)
		# sheet.write('R%s' % row, ':', quo_header_format)
		sheet.write('S%s' % row, ": %s" % (record.incoterm.display_name or '',), quo_header_format_border_right_top)

		row+=1
		sheet.write('R%s' % row,'Estimated Deliveries', quo_header_format_border_left)
		# sheet.write('R%s' % row, ':', quo_header_format)
		sheet.write('S%s' % row, ": %s" % (odoo_format_date(env=record.env, value=record.estimated_delivery_date),), quo_header_format_border_right)

		row+=1
		sheet.write('R%s' % row,'Payment Terms', quo_header_format_border_left)
		# sheet.write('R%s' % row, ':', quo_header_format)
		sheet.write('S%s' % row, ": %s" % (record.payment_term_id.display_name or '',), quo_header_format_border_right)

		row+=1
		sheet.write('R%s' % row,'Port of Loading', quo_header_format_border_left)
		# sheet.write('R%s' % row, ':', quo_header_format)
		sheet.write('S%s' % row, ": %s" % (record.port_loading_id.name or '',), quo_header_format_border_right)

		row+=1
		sheet.write('R%s' % row,'Bank Name', quo_header_format_border_left)
		# sheet.write('R%s' % row, ':', quo_header_format)
		sheet.write('S%s' % row, ": %s" % (record.bank_account_id.display_name or '',), quo_header_format_border_right)

		row+=1
		sheet.write('R%s' % row,'Bank Addr', quo_header_format_border_left)
		# sheet.write('R%s' % row, ':', quo_header_format)
		sheet.write('S%s' % row, ": %s" % (record.bank_account_id.address or '',), quo_header_format_border_right)

		row+=1
		sheet.write('R%s' % row,'Bank A/C', quo_header_format_border_left)
		# sheet.write('R%s' % row, ':', quo_header_format)
		sheet.write('S%s' % row, ": %s" % (record.bank_account_id.bank_acc_number or '',), quo_header_format_border_right)

		row+=1
		sheet.write('R%s' % row,'Swift Code', quo_header_format_border_left_bottom)
		# sheet.write('R%s' % row, ':', quo_header_format)
		sheet.write('S%s' % row, ": %s" % (record.bank_account_id.swift_code or '',), quo_header_format_border_right_bottom)

		sheet.freeze_panes(row+2, 0)
		sheet.set_row(row+2, 40)


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

		sheet.merge_range('C%s:D%s' % (row,(row+1),), 'DESCRIPTION', header_format)
		
		sheet.merge_range('E%s:E%s' % (row,(row+1),), 'PRODUCT IMAGE', header_format)

		sheet.merge_range('F%s:F%s' % (row,(row+1),), 'BUYER REMARKS', header_format)


		# ITEM SIZE
		sheet.merge_range('G%s:I%s' % (row, row,), 'ITEM SIZE (%s)' % record.partner_uom_id.name, header_format)
		sheet.write('G%s' % (row+1),'L', header_format)
		sheet.write('H%s' % (row+1),'W', header_format)
		sheet.write('I%s' % (row+1),'H', header_format)

		sheet.merge_range('J%s:J%s' % (row,(row+1),), 'QTY / CTN', header_format)

		# CASE PACK SIZE
		sheet.merge_range('K%s:M%s' % (row, row,), 'CASE PACK SIZE (%s)' % record.partner_uom_id.name, header_format)
		sheet.write('K%s' % (row+1),'L', header_format)
		sheet.write('L%s' % (row+1),'W', header_format)
		sheet.write('M%s' % (row+1),'H', header_format)

		sheet.merge_range('N%s:N%s' % (row,(row+1),), 'CBM / CTN', header_format)

		sheet.merge_range('O%s:O%s' % (row,(row+1),), 'QTY CARTOON', header_format)

		sheet.merge_range('P%s:P%s' % (row,(row+1),), 'TOTAL QTY', header_format)

		sheet.merge_range('Q%s:Q%s' % (row,(row+1),), 'TOTAL CBM', header_format)

		sheet.merge_range('R%s:R%s' % (row,(row+1),), 'PRICE', header_format)

		sheet.merge_range('S%s:S%s' % (row,(row+1),), 'TOTAL AMOUNT', header_format)

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

			
			imgoptions = {'y_scale':0.5,'x_scale':0.5, 'image_data':f, 'x_offset': 50}
			sheet.insert_image('E%s' % row, 'product%s.jpg' % (line.product_id.default_code,), imgoptions)
		else:
			sheet.write('E%s' % row, '-', line_format)


		sheet.write('F%s' % row, line.buyer_remarks or '', line_format)

		sheet.write('G%s' % row, line.item_size_l, numeric_line_format)
		sheet.write('H%s' % row, line.item_size_w, numeric_line_format)
		sheet.write('I%s' % row, line.item_size_h, numeric_line_format)

		sheet.write('J%s' % row, line.qty_per_ctn, numeric_line_format)

		sheet.write('K%s' % row, line.case_pack_size_l, numeric_line_format)
		sheet.write('L%s' % row, line.case_pack_size_w, numeric_line_format)
		sheet.write('M%s' % row, line.case_pack_size_h, numeric_line_format)

		


		sheet.write('N%s' % row, line.cbm_per_ctn, numeric_line_format)
		sheet.write('O%s' % row, line.qty_cartoon, numeric_line_format)

		sheet.write('P%s' % row, line.product_uom_qty, numeric_line_format)

		sheet.write('Q%s' % row, line.total_cbm, numeric_line_format)

		sheet.write('R%s' % row, line.price_unit, numeric_line_format)
		sheet.write('S%s' % row, line.price_subtotal, numeric_line_format)

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
		sheet.merge_range('A%s:N%s' % (row,row,), record.note or '', wrapped)
		
		return 
		

	def generate_xlsx_report(self, workbook, data, records):
		for obj in records:
			report_name = obj.name
			# One sheet by partner
			sheet = workbook.add_worksheet(report_name[:31])
			sheet.set_column(0,0,4)
			sheet.set_column(1,1,20)
			# C
			sheet.set_column(2,2,3)
			# D
			sheet.set_column(3,3,40)
			# E
			sheet.set_column(4,4,30)

			# F
			sheet.set_column(5,5,15)

			# N
			sheet.set_column(13,13,16)
			# O
			sheet.set_column(14,14,16)
			# P
			sheet.set_column(15,15,16)
			# Q
			sheet.set_column(16,16,16)
			# R
			sheet.set_column(17,17,25)
			# S
			sheet.set_column(18,18,25)
			

			

			row = self._add_quotation_header(sheet, data, obj, workbook) + 1
			
			row = self._add_quotation_table_header(sheet,data,obj, workbook, row) + 1
			start_row = row
			seq = 1
			for line in obj.order_line:
				self._write_line(sheet, line, row, seq=seq, workbook=workbook)
				sheet.set_row((row-1), 60)
				row+=1
				seq+=1
			# write footer total
			
			grand_total_format = workbook.add_format({
				'align':'right',
				'bold':1,
				'border':1,
			})
			sheet.merge_range('A%s:N%s' % (row,row,), 'Grand Total',grand_total_format)

			footer_total_format = workbook.add_format({
				'align':'center',
				'bold':1,
				'border':1,
			})

			sheet.write_formula('O%s' % (row,), 'SUM(O%s:O%s)' % (start_row,(row-1),), footer_total_format)
			sheet.write_formula('P%s' % (row,), 'SUM(P%s:P%s)' % (start_row,(row-1),), footer_total_format)
			sheet.write_formula('Q%s' % (row,), 'SUM(Q%s:Q%s)' % (start_row,(row-1),), footer_total_format)
			sheet.write_formula('R%s' % (row,), 'SUM(R%s:R%s)' % (start_row,(row-1),), footer_total_format)
			sheet.write_formula('S%s' % (row,), 'SUM(S%s:S%s)' % (start_row,(row-1),), footer_total_format)
			
			row = row+1
			self._add_footer(sheet=sheet, data=data, record=obj, workbook=workbook, row=row)