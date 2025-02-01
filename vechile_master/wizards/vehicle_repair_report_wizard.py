from odoo import models, fields, api
import base64
import io
import xlsxwriter
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class VehicleRepairReportWizard(models.TransientModel):
    _name = 'vehicle.repair.report.wizard'
    _description = 'Vehicle Repair Report Wizard'

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True, default=fields.Date.context_today)
    all_vehicles = fields.Boolean(string='Include All Vehicles', default=False)
    vehicle_id = fields.Many2one('vehicle.master', string='Vehicle', required=False)
    include_product_issues = fields.Boolean(string="Include Product Issues", default=False)

    @api.onchange('all_vehicles')
    def _onchange_all_vehicles(self):
        if self.all_vehicles:
            self.vehicle_id = False

    @api.onchange('vehicle_id')
    def _onchange_vehicle_id(self):
        if self.vehicle_id:
            self.all_vehicles = False

    def generate_excel_report(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Vehicle Repair Report')

        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'border': 1
        })
        cell_format = workbook.add_format({
            'align': 'left',
            'border': 1
        })
        amount_format = workbook.add_format({
            'align': 'right',
            'border': 1,
            'num_format': '#,##0.00'
        })

        # Add color formats
        pink_format = workbook.add_format({
            'align': 'center',
            'border': 1,
            'bg_color': '#FFB6C1'  # Light pink
        })
        green_format = workbook.add_format({
            'align': 'center',
            'border': 1,
            'bg_color': '#90EE90'  # Light green
        })
        pink_amount_format = workbook.add_format({
            'align': 'right',
            'border': 1,
            'num_format': '#,##0.00',
            'bg_color': '#FFB6C1'  # Light pink
        })
        green_amount_format = workbook.add_format({
            'align': 'right',
            'border': 1,
            'num_format': '#,##0.00',
            'bg_color': '#90EE90'  # Light green
        })

        # Define alternate row format
        alt_row_format = workbook.add_format({
            'align': 'left',
            'border': 1,
            'bg_color': '#F5F5F5'  # Light grey
        })

        # Define new formats
        title_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'bg_color': '#FFB6C1',  # Light pink
            'border': 1,
            'font_size': 24
        })
        month_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'bg_color': '#ADD8E6',  # Light blue
            'border': 1
        })
        total_format = workbook.add_format({
            'bold': True,
            'align': 'right',
            'bg_color': '#90EE90',  # Light green
            'border': 1
        })
        issue_header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'bg_color': '#DDA0DD',  # Plum color for product issues
            'border': 1
        })

        # Fetch company currency symbol
        company_currency = self.env.user.company_id.currency_id.symbol
        currency_format = workbook.add_format({'border': 1})
        total_currency_format = workbook.add_format(
            {'num_format': f'#,##0.00 {company_currency}', 'border': 1})

        # Set column widths
        worksheet.set_column('A:A', 12)  # Date
        worksheet.set_column('B:B', 20)  # Repair/Issue ID
        worksheet.set_column('C:C', 20)  # Product
        worksheet.set_column('D:D', 10)  # Quantity
        worksheet.set_column('E:E', 12)  # Unit Price
        worksheet.set_column('F:F', 15)  # Total Price
        worksheet.set_column('G:G', 12)  # Extra Cost
        worksheet.set_column('H:H', 15)  # Workshop/Source
        worksheet.set_column('I:I', 15)  # Equipments/Notes

        # Fetch repair records based on selection
        domain = [
            ('schedule_date', '>=', self.start_date),
            ('schedule_date', '<=', self.end_date)
        ]
        if not self.all_vehicles:
            domain.append(('vehicle_name', '=', self.vehicle_id.id))

        repair_records = self.env['repair.order'].search(domain, order='vehicle_name, schedule_date asc')

        _logger.info(f'Fetched {len(repair_records)} repair records')

        # Get product issues if include_product_issues is True
        product_issues = []
        if self.include_product_issues:
            product_issues = self.env['product.issue'].search([
                ('vehicle_id', '=', self.vehicle_id.id if not self.all_vehicles else False),
                ('issue_date', '>=', self.start_date),
                ('issue_date', '<=', self.end_date),
                ('state', '=', 'done')
            ], order='issue_date asc')

        # Combine and sort all records by date
        all_records = []
        for repair in repair_records:
            # Convert datetime to date for comparison
            repair_date = repair.schedule_date.date() if isinstance(repair.schedule_date,
                                                                    datetime) else repair.schedule_date
            all_records.append({
                'date': repair_date,
                'type': 'repair',
                'record': repair
            })

        for issue in product_issues:
            # Ensure issue_date is a date object
            issue_date = issue.issue_date.date() if isinstance(issue.issue_date, datetime) else issue.issue_date
            all_records.append({
                'date': issue_date,
                'type': 'issue',
                'record': issue
            })

        all_records.sort(key=lambda x: x['date'])

        # Group records by vehicle and month
        records_by_vehicle = {}
        for record in all_records:
            vehicle_id = record['record'].vehicle_name.id if record['type'] == 'repair' else record['record'].vehicle_id.id
            vehicle_name = record['record'].vehicle_name.name if record['type'] == 'repair' else record['record'].vehicle_id.name
            month_year = record['date'].strftime('%Y-%m')
            
            if vehicle_id not in records_by_vehicle:
                records_by_vehicle[vehicle_id] = {'name': vehicle_name, 'months': {}}
            
            if month_year not in records_by_vehicle[vehicle_id]['months']:
                records_by_vehicle[vehicle_id]['months'][month_year] = []
            
            records_by_vehicle[vehicle_id]['months'][month_year].append(record)

        # Calculate total cost for all vehicles and individual vehicles
        grand_total = 0.0
        vehicle_totals = {}
        
        for vehicle_id, vehicle_data in records_by_vehicle.items():
            vehicle_total = 0.0
            for month_repairs in vehicle_data['months'].values():
                for record in month_repairs:
                    if record['type'] == 'repair' and record['record'].state == 'done':
                        repair = record['record']
                        # Calculate costs from move lines (parts)
                        for move in repair.move_ids:
                            move_total = move.product_uom_qty * move.product_cost
                            vehicle_total += move_total
                            grand_total += move_total
                        # Calculate costs from extra costs
                        for extra in repair.extra_cost_ids:
                            vehicle_total += extra.extra_price
                            grand_total += extra.extra_price
                    elif record['type'] == 'issue':
                        issue = record['record']
                        for line in issue.product_line_ids:
                            line_total = line.quantity * line.standard_price
                            vehicle_total += line_total
                            grand_total += line_total
            
            vehicle_totals[vehicle_id] = vehicle_total

        # Write report title
        title = 'All Vehicles Repair Report' if self.all_vehicles else f'Vehicle: {self.vehicle_id.name}'
        worksheet.merge_range('A1:I1', f'{title} | Total Expenses: {grand_total:.2f} {self.env.user.company_id.currency_id.symbol}',
                            title_format)

        # Write data grouped by vehicle and month
        row = 2
        headers = ['Date', 'Reference', 'Product', 'Quantity', 'Unit Price', 'Total Price', 'Extra Cost', 'Workshop',
                   'Equipment']

        for vehicle_id, vehicle_data in records_by_vehicle.items():
            if self.all_vehicles:
                # Write vehicle header with its total
                worksheet.merge_range(row, 0, row, 8, 
                    f'Vehicle: {vehicle_data["name"]} | Total Cost: {vehicle_totals[vehicle_id]:.2f} {self.env.user.company_id.currency_id.symbol}', 
                    workbook.add_format({
                        'bold': True,
                        'align': 'center',
                        'bg_color': '#4F81BD',  # Blue color for vehicle header
                        'font_color': 'white',
                        'border': 1
                    }))
                row += 1

            for month_year, records in vehicle_data['months'].items():
                formatted_month = datetime.strptime(month_year, '%Y-%m').strftime('%B %Y')
                worksheet.merge_range(row, 0, row, 8, f'Month: {formatted_month}', month_format)
                row += 1

                # Write headers
                for col, header in enumerate(headers):
                    worksheet.write(row, col, header, header_format)
                row += 1

                month_total = 0.0
                for record in records:
                    if record['type'] == 'repair' and record['record'].state == 'done':
                        repair = record['record']
                        # Write repair records
                        worksheet.write(row, 0, repair.schedule_date.strftime('%Y-%m-%d'), cell_format)
                        worksheet.write(row, 1, repair.name, cell_format)

                        for move in repair.move_ids:
                            row_format = alt_row_format if row % 2 == 0 else cell_format
                            move_total = move.product_uom_qty * move.product_cost
                            worksheet.write(row, 2, move.product_id.name, row_format)
                            worksheet.write(row, 3, move.product_uom_qty, row_format)
                            worksheet.write(row, 4, move.product_cost, currency_format)
                            worksheet.write(row, 5, move_total, currency_format)
                            worksheet.write(row, 6, '', currency_format)
                            worksheet.write(row, 7, move.picking_id.partner_id.name or '', row_format)
                            worksheet.write(row, 8, 'Parts', row_format)
                            month_total += move_total
                            row += 1

                        for extra in repair.extra_cost_ids:
                            row_format = alt_row_format if row % 2 == 0 else cell_format
                            worksheet.write(row, 2, 'Extra Cost', row_format)
                            worksheet.write(row, 3, 1, row_format)
                            worksheet.write(row, 4, extra.extra_price, currency_format)
                            worksheet.write(row, 5, '', currency_format)
                            worksheet.write(row, 6, extra.extra_price, currency_format)
                            worksheet.write(row, 7, extra.workshop_id.workshop_name or '', row_format)
                            worksheet.write(row, 8, extra.equipment_name, row_format)
                            month_total += extra.extra_price
                            row += 1

                    elif record['type'] == 'issue':
                        issue = record['record']
                        # Write issue lines
                        for line in issue.product_line_ids:
                            row_format = alt_row_format if row % 2 == 0 else cell_format
                            line_total = line.quantity * line.standard_price
                            worksheet.write(row, 0, issue.issue_date.strftime('%Y-%m-%d'), cell_format)
                            worksheet.write(row, 1, issue.name, cell_format)
                            worksheet.write(row, 2, line.product_id.name, row_format)
                            worksheet.write(row, 3, line.quantity, row_format)
                            worksheet.write(row, 4, line.standard_price, currency_format)
                            worksheet.write(row, 5, line_total, currency_format)
                            worksheet.write(row, 6, '', currency_format)
                            worksheet.write(row, 7, issue.warehouse_id.name or '', row_format)
                            worksheet.write(row, 8, 'Product Issue', row_format)
                            month_total += line_total
                            row += 1

                    # Add a blank row between records
                    worksheet.write_blank(row, 0, None, cell_format)
                    row += 1

                # Write monthly total
                worksheet.merge_range(row, 0, row, 5, f'Total Cost for {formatted_month}:', total_format)
                worksheet.write(row, 6, month_total, total_currency_format)
                row += 2

        workbook.close()

        # Create attachment
        attachment_name = f'Vehicle_Repair_Report_{self.vehicle_id.name if not self.all_vehicles else "All Vehicles"}_{datetime.now().strftime("%Y%m%d")}.xlsx'
        attachment_data = {
            'name': attachment_name,
            'datas': base64.b64encode(output.getvalue()),
            'res_model': 'vehicle.repair.report.wizard',
            'res_id': self.id,
            'type': 'binary',
        }

        attachment = self.env['ir.attachment'].create(attachment_data)

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }