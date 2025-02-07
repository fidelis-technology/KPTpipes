
from odoo import models, fields, api

class HrContract(models.Model):
    _inherit = 'hr.contract'
    _description = 'Employee Contract'

    annual_salary = fields.Float(string='Annual Salary')
    tax_regime = fields.Selection([('old_regime', 'Old Tax Regime'), ('new_regime', 'New Tax Regime'), ('other_regime', 'Other Tax Regime')], string='Regime')
    other_income = fields.Float(string='Other Income')
    gross_income = fields.Float(string='Gross Income', compute='_compute_tax_slab', store=True)
    total_deductions = fields.Float(string='Total Deductions', compute='_compute_tax_slab', store=True)
    taxable_amount = fields.Float(string='Taxable Amount', compute='_compute_tax_slab', store=True)
    tax_payable = fields.Float(string='Tax Payable')
    tax_regime_slab = fields.Many2one('tax.slab', string='Tax Slab')
    tds_deduction_month = fields.Float(string='TDS Deduction Per month')
    deduction_ids = fields.One2many('deduction.description', 'hr_contract_id')



    @api.depends('annual_salary', 'other_income', 'deduction_ids.deduction_amt', 'tax_regime')
    def _compute_tax_slab(self):
        for contract in self:
            contract.gross_income = contract.annual_salary + contract.other_income

            if contract.deduction_ids:
                contract.total_deductions = sum(contract.deduction_ids.mapped('deduction_amt'))
            else:
                contract.total_deductions = 0

            contract.taxable_amount = contract.gross_income - contract.total_deductions


    @api.onchange('annual_salary', 'other_income', 'taxable_amount', 'tax_regime')
    def _onchange_annual_salary(self):
        for contract in self:
            total_salary = contract.annual_salary + contract.other_income
            for slab in contract.tax_regime_slab.search([('tax_regime', '=', contract.tax_regime)]):
                if slab.tax_regime_amt_from <= total_salary<= slab.tax_regime_amt_to:
                    contract.tax_regime_slab = slab
                    contract.tax_payable = (slab.tax_regime_per / 100) * contract.taxable_amount
                    contract.tds_deduction_month = contract.tax_payable / 12
                    break

class DeductionDescription(models.Model):
    _name = 'deduction.description'
    _description = 'Deduction Description'

    hr_contract_id = fields.Many2one('hr.contract')
    name = fields.Char('Deduction Description')
    deduction_amt = fields.Float('Amount')
