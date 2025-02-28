from setuptools.unicode_utils import filesys_decode

from odoo import models, fields, api

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



    @api.depends('annual_salary', 'other_income', 'deduction_ids.deduction_amt', 'tax_regime_slab', 'gross_qualify_income')
    def _compute_tax_slab(self):
        for contract in self:

            contract.gross_income = contract.annual_salary + contract.other_income

            if contract.deduction_ids:
                contract.total_deductions = sum(contract.deduction_ids.mapped('deduction_amt'))
            else:
                contract.total_deductions = 0

            contract.taxable_amount = contract.annual_salary - contract.gross_qualify_income - contract.total_deductions



    @api.onchange('annual_salary', 'other_income', 'taxable_amount', 'tax_regime_slab')
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
            contract.tds_deduction_month = round(contract.tax_payable / 12)
            # # Apply 4% Health & Education Cess

            cess = (total_tax * 4) / 100
            total_tax += cess

            contract.tax_payable_cess = round(total_tax)
            contract.tds_deduction_month_cess = round(contract.tax_payable_cess / 12)




class DeductionDescription(models.Model):
    _name = 'deduction.description'
    _description = 'Deduction Description'

    hr_contract_id = fields.Many2one('hr.contract')
    name = fields.Char('Deduction Description')
    deduction_amt = fields.Float('Amount')


class TDSHistory(models.Model):
    _name = 'tds.history'
    _description = 'TDS History'

    hr_contract_id = fields.Many2one('hr.contract')
    employer_name = fields.Char('Employeer Name')
    month = fields.Date('month')
    year = fields.Date('year')
    employer_tds = fields.Float('TDS Amount')