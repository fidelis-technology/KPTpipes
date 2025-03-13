from odoo import models, api, fields
from collections import defaultdict
import itertools
from datetime import datetime
from odoo.exceptions import ValidationError

class HrTDS(models.Model):
    _name = 'hr.tds'
    _description = 'HR TDS'

    hr_contract_id = fields.Many2one('hr.contract', string='Contract')
    hr_employee_id = fields.Many2one('hr.employee', string='Employee', copy=False)
    annual_salary = fields.Float(string='Annual Income')
    total_deductions = fields.Float(string='Total Deductions', compute='_compute_tax_slab', store=True)
    taxable_amount = fields.Float(string='Taxable Amount', compute='_compute_tax_slab', store=True)
    tax_payable = fields.Float(string='Tax Payable')
    tax_payable_cess = fields.Float(string='Tax Payable Cess')
    tax_regime_slab = fields.Many2one('tax.slab', string='Tax Slab', copy=False)
    tds_deduction_month = fields.Float(string='TDS Deduction Per month')
    tds_deduction_month_cess = fields.Float(string='TDS Deduction Per month Cess')
    deduction_ids = fields.One2many('deduction.description', 'hr_tds_id')
    grouped_deductions_html = fields.Html(compute="_compute_grouped_deductions_html", sanitize=False, store=False)
    prepaid_tds = fields.Float('Prepaid TDS')
    tax_pay_ref = fields.Float('Tax Payable/Refundable')
    month_ids = fields.One2many('month.wise.tds', 'hr_tds_id', store=True)
    tds_from_month = fields.Char('TDS From', compute='_compute_month_ids', store=True)
    tds_to_month = fields.Char('TDS To', compute='_compute_month_ids', store=True)
    is_tds_payslip = fields.Boolean(string="Appears On Payslip", default=False)

    _sql_constraints = [
        ('unique_employee_taxslab_field', 'unique(hr_employee_id, tax_regime_slab)',
         'The combination of Employee and Tax Slab Field must be unique!')
    ]


    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.hr_employee_id.name or ''} - {rec.tax_regime_slab.display_name or ''}"

    @api.constrains('hr_employee_id', 'tax_regime_slab')
    def _check_unique_employee_taxslab_field(self):
        for record in self:
            existing_record = self.search([
                ('hr_employee_id', '=', record.hr_employee_id.id),
                ('tax_regime_slab', '=', record.tax_regime_slab.id),
                ('id', '!=', record.id)
            ])
            if existing_record:
                raise ValidationError("The combination of Employee and Tax Slab Field must be unique!")

    def sort_financial_year(self, month_years):
        # Define the correct order for financial year sorting (April to March)
        financial_order = {
            "April": 1, "May": 2, "June": 3, "July": 4, "August": 5, "September": 6,
            "October": 7, "November": 8, "December": 9, "January": 10, "February": 11, "March": 12
        }

        # Custom sorting key
        def financial_key(month_year):
            month, year = month_year.split(" ")
            return (int(year), financial_order[month])

        return sorted(month_years, key=financial_key)

    @api.depends('month_ids')
    def _compute_month_ids(self):
        for record in self:
            if record.month_ids:
                record.write({'tds_deduction_month': round(record.tax_payable / len(record.month_ids)), 'tds_deduction_month_cess': round(record.tax_payable_cess / len(record.month_ids))})
                month_years = sorted(record.month_ids.mapped("tds_month_year"))
                sorted_month_years = self.sort_financial_year(month_years)
                record.tds_from_month = sorted_month_years[0] if sorted_month_years else False
                record.tds_to_month = sorted_month_years[-1] if sorted_month_years else False

    @api.onchange("tax_payable_cess", "annual_salary", "tax_regime_slab")
    def _onchange_tds_per_year(self):
        """Dynamically generate 12 months and distribute TDS per year equally."""
        for record in self:
            if record.tax_payable_cess:
                monthly_tds = round(record.tax_payable_cess / 12) # Divide by 12 months
                record.write({'tds_deduction_month': round(record.tax_payable / 12), 'tds_deduction_month_cess': round(record.tax_payable_cess / 12)})
                months = [
                    ("april", "April"), ("may", "May"), ("june", "June"), ("july", "July"), ("august", "August"),
                    ("september", "September"), ("october", "October"), ("november", "November"),
                    ("december", "December"), ("january", "January"), ("february", "February"), ("march", "March")
                ]

                current_year = datetime.today().year
                fiscal_start_year = current_year if datetime.today().month >= 4 else current_year - 1
                fiscal_end_year = fiscal_start_year + 1

                # Assign years based on fiscal year
                month_years = [
                    (month[0], f"{month[1]} {fiscal_start_year if idx < 9 else fiscal_end_year}")
                    for idx, month in enumerate(months)
                ]

                # Clear old records and create new ones
                record.month_ids = [(5, 0, 0)]  # Remove existing lines
                record.month_ids = [(0, 0, {"months": month, "tds_month_amt": monthly_tds, "tds_month_year": month_year})
                                    for month, month_year in month_years]
                record.update({'tds_from_month': month_years[0][1], 'tds_to_month': month_years[-1][1]})
            else:
                record.month_ids = [(5, 0, 0)]
                record.update({'tds_from_month': False, 'tds_to_month': False})

    @api.onchange('tax_payable_cess', 'prepaid_tds')
    def _onchange_prepaid_tds(self):
        for record in self:
            record.tax_pay_ref = record.tax_payable_cess - record.prepaid_tds


    @api.depends('deduction_ids', 'deduction_ids.deduction_amt')
    def _compute_grouped_deductions_html(self):
        for record in self:
            grouped = defaultdict(lambda: {"schemes": [], "total": 0, "max_limit": 0})
            combined_limits = defaultdict(lambda: {"sections": [], "total": 0, "max_limit": 0})
            total_deduction_amt = 0  # Initialize total deduction amount
            #
            # # Define combined section groups (e.g., 80C + 80CCD(1) together have a max limit of ₹1,50,000)
            section_groups = {
                "80C": ["80C", "80CCC", "80CCD(1)"],  # These sections share a limit of ₹1,50,000
            }

            # Step 1: Group schemes under each section
            for line in record.deduction_ids:
                section_name = line.section_id.name
                grouped[section_name]["schemes"].append(
                    {"name": line.scheme_id.scheme_name, "amount": line.deduction_amt})
                grouped[section_name]["total"] += line.deduction_amt
                grouped[section_name]["max_limit"] = line.max_limit_deduction  # Ensure this field exists
                # total_deduction_amt += line.deduction_amt
            # Step 2: Handle combined limits
            combined_vals = list(itertools.chain(*section_groups.values()))
            if set(combined_vals) & set(record.deduction_ids.section_id.mapped('name')):
                for group_name, sections in section_groups.items():
                    total_combined = sum(grouped[sec]["total"] if sec in grouped else 0 for sec in sections)
                    # total_deduction_amt -= total_combined,
                    max_limit_combined = min(grouped[sec]["max_limit"] for sec in sections if sec in grouped)
                    total_deduction_amt += min(total_combined, max_limit_combined)  # Ensure it doesn't exceed max limit

            for line in record.deduction_ids:
                section_name = line.section_id.name
                if section_name not in combined_vals:
                    total_deduction_amt += min(line.max_limit_deduction, line.deduction_amt) if line.scheme_id.type_of_deduction == 'amount' else line.deduction_amt


            # Step 3: Assign total deduction amount to the field
            record.total_deductions = total_deduction_amt

            # Step 4: Build HTML output
            html_content = "<div class='deduction-summary'>"
            for section, data in grouped.items():
                html_content += f"""
                 <div class='section'>
                     <strong>Section {section}:</strong>
                     <div class='scheme-list'>
                 """
                for scheme in data["schemes"]:
                    html_content += f"""
                         <div class='scheme'>
                             <span>{scheme['name']}:</span>
                             <span class='amount'>{scheme['amount']}</span>
                         </div>
                     """

                html_content += f"""
                     </div>
                     <hr/>
                     <div class='max-limit'>
                         <span>Max Limit ({data['max_limit']})</span>
                         <span class='amount'>{data['total']}</span>
                     </div>
                 </div>
                 """

            html_content += "</div>"

            # Assign the final HTML to the field
            record.grouped_deductions_html = html_content



    @api.depends('annual_salary',  'tax_regime_slab', 'total_deductions')
    def _compute_tax_slab(self):
        for contract in self:
            contract.taxable_amount = contract.annual_salary  - contract.total_deductions



    @api.onchange('annual_salary', 'taxable_amount', 'tax_regime_slab', 'total_deductions')
    def _onchange_annual_salary(self):


        for contract in self:
            if not contract.tax_regime_slab or not contract.annual_salary:
                contract.tax_payable = 0
                contract.tds_deduction_month = 0
                continue

            annual_income = contract.taxable_amount
            total_tax = 0
            slabs = contract.tax_regime_slab.tax_regime_line_ids

            # if contract.tax_regime == 'new_regime' and annual_income <= 700000:
            #     contract.computed_tax = 0  # Rebate under New Regime
            #     continue

            remaining_income = annual_income

            # Apply slab-based tax calculation
            for slab in slabs.sorted(lambda s: s.tax_regime_amt_from):
                if remaining_income > slab.tax_regime_amt_from:
                    taxable_income = min(remaining_income, slab.tax_regime_amt_to) - slab.tax_regime_amt_from
                    tax = (taxable_income * slab.tax_regime_per) / 100
                    total_tax += tax

            contract.tax_payable = round(total_tax)
            # contract.tds_deduction_month = round(contract.tax_payable / 12)
            # # Apply 4% Health & Education Cess

            cess = (total_tax * 4) / 100
            total_tax += cess

            contract.tax_payable_cess = round(total_tax)
            # contract.tds_deduction_month_cess = round(contract.tax_payable_cess / 12)


    @api.model_create_multi
    def create(self, vals):
        """Automatically ensure only one True value per employee_id during creation."""
        res = super(HrTDS, self).create(vals)
        if res.is_tds_payslip:
            # Set all other records' boolean_field to False for the same employee
            self.search([
                ('hr_employee_id', '=', res.hr_employee_id.id),
                ('id', '!=', res.id)
            ]).write({'is_tds_payslip': False})
        return res

    def write(self, vals):
        """Ensure only one True value per employee_id during updates."""
        res = super(HrTDS, self).write(vals)
        if 'is_tds_payslip' in vals and vals['is_tds_payslip']:
            for record in self:
                # Set all other records' boolean_field to False for the same employee
                self.search([
                    ('hr_employee_id', '=', record.hr_employee_id.id),
                    ('id', '!=', record.id)
                ]).write({'is_tds_payslip': False})
        return res