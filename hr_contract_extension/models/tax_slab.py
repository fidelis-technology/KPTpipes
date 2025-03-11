from odoo import models, fields, api
from datetime import timedelta

class TaxSlab(models.Model):
    _name = 'tax.slab'
    _description = 'Tax Slab'


    name = fields.Char(string='Regime Name', required=True)
    financial_year_name = fields.Char(string="Financial Year", help="Example: 2024-2025")
    date_start = fields.Date(string="FY Start Date", required=True)
    date_end = fields.Date(string="FY End Date", required=True)
    tax_regime_line_ids = fields.One2many('tax.slab.line', 'tax_regime_id', string='Tax Slab lines')
    age_classification = fields.Selection([
        ('regular', 'Regular Citizen (Below 60)'),
        ('senior', 'Senior Citizen (60-79 Years)'),
        ('super_senior', 'Super Senior Citizen(80+ Years)')],
        string="Age Classification",  default='regular')

    def _compute_display_name(self):
        for rec in self:
            if rec.date_start:
                age_classification = 'Regular Citizen (Below 60)'
                if rec.age_classification == 'senior':
                    age_classification = 'Senior Citizen (60-79 Years)'
                elif rec.age_classification == 'super_senior':
                    age_classification = 'Super Senior Citizen(80+ Years)'
                rec.display_name = f'{rec.name} FY({rec.date_start.year}-{rec.date_start.year+1}) {age_classification}'
            else:
                rec.display_name = f'{rec.name}'



    @api.onchange("date_start")
    def _onchange_date_start(self):
        """Automatically set name based on date_start"""
        if self.date_start:
            year = self.date_start.year
            self.date_end = self.date_start.replace(year=year + 1) - timedelta(days=1)
            self.financial_year_name = f"{year}-{year + 1}"


class TaxSlabLine(models.Model):
    _name = 'tax.slab.line'
    _description = 'Tax Slab Line'

    tax_regime_id = fields.Many2one('tax.slab', string='Tax Slab')
    tax_regime_description = fields.Char(string='Tax Slab Description')
    tax_regime_per = fields.Float(string='Tax %')
    tax_regime_amt_from = fields.Float(string='Applied From')
    tax_regime_amt_to = fields.Float(string='Applied To')
    surcharge = fields.Float('Surcharge')











