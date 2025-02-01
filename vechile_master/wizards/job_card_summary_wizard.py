from odoo import models, fields, api
import base64
import io
import xlsxwriter
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class JobCardSummaryWizard(models.TransientModel):
    _name = 'job.card.summary.wizard'
    _description = 'Job Card Summary Report'

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True, default=fields.Date.context_today)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    def generate_excel_report(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Job Card Summary')

        # Define formats
        title_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 20,
            'font_name': 'Arial',
            'border': 2,
            'bg_color': '#1F497D',  # Dark blue
            'font_color': 'white'
        })

        subtitle_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 14,
            'font_name': 'Arial',
            'border': 1,
            'bg_color': '#8DB4E2',  # Light blue
            'font_color': 'black'
        })

        address_format = workbook.add_format({
            'align': 'center',
            'font_size': 12,
            'font_name': 'Arial',
            'border': 1,
            'bg_color': '#DAEEF3'  # Very light blue
        })

        table_header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'border': 2,
            'bg_color': '#4F81BD',  # Medium blue
            'font_color': 'white',
            'font_size': 11,
            'border_color': '#1F497D'
        })

        cell_format = workbook.add_format({
            'align': 'center',
            'border': 1,
            'font_size': 10,
            'border_color': '#8DB4E2'
        })

        amount_format = workbook.add_format({
            'align': 'right',
            'border': 1,
            'num_format': '#,##0.00',
            'font_size': 10,
            'border_color': '#8DB4E2'
        })

        date_format = workbook.add_format({
            'align': 'center',
            'border': 1,
            'num_format': 'dd/mm/yyyy',
            'font_size': 10,
            'border_color': '#8DB4E2'
        })

        total_format = workbook.add_format({
            'bold': True,
            'align': 'right',
            'border': 2,
            'num_format': '#,##0.00',
            'bg_color': '#C6EFCE',  # Light green
            'font_color': '#006100',  # Dark green
            'font_size': 11,
            'border_color': '#006100'
        })

        grand_total_format = workbook.add_format({
            'bold': True,
            'align': 'right',
            'border': 2,
            'num_format': '#,##0.00',
            'bg_color': '#FFC7CE',  # Light red
            'font_color': '#9C0006',  # Dark red
            'font_size': 12,
            'border_color': '#9C0006'
        })

        # Set column widths
        worksheet.set_column('A:A', 8)   # Sl.No
        worksheet.set_column('B:B', 15)  # Date
        worksheet.set_column('C:C', 20)  # Job Card No.
        worksheet.set_column('D:D', 15)  # Veh.No.
        worksheet.set_column('E:G', 15)  # Cost columns
        worksheet.set_column('H:H', 18)  # Total Cost

        # Write company header
        row = 0
        worksheet.merge_range('A1:H1', 'HARMAN STAR WORK SHOP', title_format)
        row += 1
        worksheet.merge_range(row, 0, row, 7, self.company_id.street or '', address_format)
        row += 1
        if self.company_id.street2:
            worksheet.merge_range(row, 0, row, 7, self.company_id.street2, address_format)
            row += 1
        worksheet.merge_range(row, 0, row, 7, 
            f"{self.company_id.city}, {self.company_id.state_id.name}, {self.company_id.zip}", address_format)
        row += 2

        # Write report title
        worksheet.merge_range(row, 0, row, 7, 'JOB CARD SUMMARY', subtitle_format)
        row += 1
        worksheet.merge_range(row, 0, row, 7, 
            f'Period: {self.start_date.strftime("%d/%m/%Y")} to {self.end_date.strftime("%d/%m/%Y")}', 
            address_format)
        row += 2

        # Write table headers with borders
        headers = ['Sl.No.', 'Date', 'Job Card No.', 'Veh.No.', 'Spare Parts', 'Extra Cost', 'Labour', 'Total Cost']
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, table_header_format)
        row += 1

        # Fetch repair orders
        repair_orders = self.env['repair.order'].search([
            ('schedule_date', '>=', self.start_date),
            ('schedule_date', '<=', self.end_date),
            ('state', '=', 'done')
        ], order='schedule_date asc')

        # Write data with alternating row colors
        sl_no = 1
        grand_total = {'parts': 0, 'extra': 0, 'labour': 0, 'total': 0}

        # Create formats for alternating rows
        even_row_format = workbook.add_format({
            'align': 'center',
            'border': 1,
            'bg_color': '#F2F2F2',  # Light gray
            'border_color': '#8DB4E2'
        })

        odd_row_format = workbook.add_format({
            'align': 'center',
            'border': 1,
            'border_color': '#8DB4E2'
        })

        even_amount_format = workbook.add_format({
            'align': 'right',
            'border': 1,
            'num_format': '#,##0.00',
            'bg_color': '#F2F2F2',  # Light gray
            'border_color': '#8DB4E2'
        })

        odd_amount_format = workbook.add_format({
            'align': 'right',
            'border': 1,
            'num_format': '#,##0.00',
            'border_color': '#8DB4E2'
        })

        for repair in repair_orders:
            # Calculate costs
            parts_cost = sum(move.product_uom_qty * move.product_cost for move in repair.move_ids)
            extra_cost = sum(extra.extra_price for extra in repair.extra_cost_ids)
            labour_cost = repair.labour_cost if hasattr(repair, 'labour_cost') else 0
            total_cost = parts_cost + extra_cost + labour_cost

            # Update grand totals
            grand_total['parts'] += parts_cost
            grand_total['extra'] += extra_cost
            grand_total['labour'] += labour_cost
            grand_total['total'] += total_cost

            # Choose format based on row number
            current_row_format = even_row_format if sl_no % 2 == 0 else odd_row_format
            current_amount_format = even_amount_format if sl_no % 2 == 0 else odd_amount_format

            # Write row
            worksheet.write(row, 0, sl_no, current_row_format)
            worksheet.write(row, 1, repair.schedule_date.strftime('%d/%m/%Y'), current_row_format)
            worksheet.write(row, 2, repair.name, current_row_format)
            worksheet.write(row, 3, repair.vehicle_name.name, current_row_format)
            worksheet.write(row, 4, parts_cost, current_amount_format)
            worksheet.write(row, 5, extra_cost, current_amount_format)
            worksheet.write(row, 6, labour_cost, current_amount_format)
            worksheet.write(row, 7, total_cost, current_amount_format)
            
            row += 1
            sl_no += 1

        # Write grand total with special formatting
        worksheet.write(row, 0, 'TOTAL', table_header_format)
        worksheet.merge_range(row, 1, row, 3, '', table_header_format)
        worksheet.write(row, 4, grand_total['parts'], grand_total_format)
        worksheet.write(row, 5, grand_total['extra'], grand_total_format)
        worksheet.write(row, 6, grand_total['labour'], grand_total_format)
        worksheet.write(row, 7, grand_total['total'], grand_total_format)

        workbook.close()

        # Create attachment
        attachment_name = f'Job_Card_Summary_{self.start_date.strftime("%Y%m%d")}_{self.end_date.strftime("%Y%m%d")}.xlsx'
        attachment_data = {
            'name': attachment_name,
            'datas': base64.b64encode(output.getvalue()),
            'res_model': 'job.card.summary.wizard',
            'res_id': self.id,
            'type': 'binary',
        }

        attachment = self.env['ir.attachment'].create(attachment_data)

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
