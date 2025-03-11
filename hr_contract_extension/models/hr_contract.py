from setuptools.unicode_utils import filesys_decode
from collections import defaultdict
from odoo import models, fields, api
import itertools

class HrContract(models.Model):
    _inherit = 'hr.contract'
    _description = 'Employee Contract'

    annual_salary = fields.Float(string='Annual Income')
    other_income = fields.Float(string='Other Income')
    gross_income = fields.Float(string='Gross Income',  compute='_compute_tax_slab', store=True)
    gross_qualify_income = fields.Float(string='Gross Qualify Amt',  store=True)
    total_deductions = fields.Float(string='Total Deductions', compute='_compute_tax_slab', store=True)
    taxable_amount = fields.Float(string='Taxable Amount', compute='_compute_tax_slab', store=True)
    tax_payable = fields.Float(string='Tax Payable')
    tax_payable_cess = fields.Float(string='Tax Payable Cess')
    tax_regime_slab = fields.Many2one('tax.slab', string='Tax Slab')
    tds_deduction_month = fields.Float(string='TDS Deduction Per month')
    tds_deduction_month_cess = fields.Float(string='TDS Deduction Per month Cess')
    deduction_ids = fields.One2many('deduction.description', 'hr_contract_id')

    tds_history_ids = fields.One2many('tds.history', 'hr_contract_id')
    grouped_deductions = fields.Text(compute="_compute_grouped_deductions", string="Summary", store=False)
    grouped_deductions_html = fields.Html(compute="_compute_grouped_deductions_html", sanitize=False, store=False)

    prepaid_tds = fields.Float('Prepaid TDS')
    tax_pay_ref = fields.Float('Tax Payable/Refundable')
    month_ids = fields.One2many('month.wise.tds', 'hr_contract_id')


    @api.onchange('month_ids')
    def _onchange_month_ids(self):
        for record in self:
            if record.month_ids:
                record.write({'tds_deduction_month': round(record.tax_payable / len(record.month_ids)), 'tds_deduction_month_cess': round(record.tax_payable_cess / len(record.month_ids))})

    @api.onchange("tax_payable_cess")
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

                # Clear old records and create new ones
                record.month_ids = [(5, 0, 0)]  # Remove existing lines
                record.month_ids = [(0, 0, {"months": month[0], "tds_month_amt": monthly_tds}) for month in months]
            else:
                record.month_ids = [(5, 0, 0)]

    @api.onchange('tax_payable_cess', 'prepaid_tds')
    def _onchange_prepaid_tds(self):
        for record in self:
            record.tax_pay_ref = record.tax_payable_cess - record.prepaid_tds

    @api.depends("deduction_ids")
    def _compute_grouped_deductions(self):
        for record in self:
            sections = defaultdict(list)
            for line in record.deduction_ids:
                sections[line.section_id.name].append((line.scheme_id.scheme_name, line.deduction_amt))

            formatted_text = ""
            for section, schemes in sections.items():
                total = sum(amount for _, amount in schemes)
                max_limit = 150000 if section == "80C" else 25000  # Example limits
                formatted_text += f"Section {section}:\n"
                for scheme, amount in schemes:
                    formatted_text += f"    {scheme}: {amount}\n"
                formatted_text += f"    --------------------------------------\n"
                formatted_text += f"    Max Limit ({max_limit}): {total}\n\n"

            record.grouped_deductions = formatted_text

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
            if set(combined_vals) - set(record.deduction_ids.section_id.mapped('name')):
                for group_name, sections in section_groups.items():
                    total_combined = sum(grouped[sec]["total"] if sec in grouped else 0 for sec in sections)
                    # total_deduction_amt -= total_combined,
                    max_limit_combined = min(grouped[sec]["max_limit"] if sec in grouped else 0 for sec in sections)
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
        # for contract in self:
        #     total_salary = contract.annual_salary + contract.other_income
        #     for slab in contract.tax_regime_slab.search([('tax_regime', '=', contract.tax_regime)]):
        #         if slab.tax_regime_amt_from <= total_salary<= slab.tax_regime_amt_to:
        #             contract.tax_regime_slab = slab
        #             contract.tax_payable = (slab.tax_regime_per / 100) * contract.taxable_amount
        #             contract.tds_deduction_month = contract.tax_payable / 12
        #             break

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




class DeductionDescription(models.Model):
    _name = 'deduction.description'
    _description = 'Deduction Description'

    hr_contract_id = fields.Many2one('hr.contract')
    name = fields.Char('Deduction Description')
    section_id = fields.Many2one('tds.section', string='Section')
    scheme_id = fields.Many2one('tds.section.scheme', string='Investment/Scheme')
    scheme_details = fields.Char(related='scheme_id.scheme_details', string='Scheme Details')
    max_limit_deduction = fields.Float(related='scheme_id.max_limit_deduction', string='Max Limit Deduction')
    deduction_amt = fields.Float('Amount')


class MonthWiseTDS(models.Model):
    _name = 'month.wise.tds'
    _description = 'Month Wise TDS'

    hr_contract_id = fields.Many2one('hr.contract')
    months = fields.Selection([
        ('january', 'January'),
        ('february', 'February'),
        ('march', 'March'),
        ('april', 'April'),
        ('may', 'May'),
        ('june', 'June'),
        ('july', 'July'),
        ('august', 'August'),
        ('september', 'September'),
        ('october', 'October'),
        ('november', 'November'),
        ('december', 'December'),
    ], string="Month")

    tds_month_amt = fields.Float('TDS Amt')


class TDSHistory(models.Model):
    _name = 'tds.history'
    _description = 'TDS History'

    hr_contract_id = fields.Many2one('hr.contract')
    employer_name = fields.Char('Employer Name')
    month = fields.Date('month')
    year = fields.Date('year')
    employer_tds = fields.Float('TDS Amount')