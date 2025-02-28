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

    def _compute_display_name(self):
        for rec in self:
            if rec.date_start:
                rec.display_name = f'{rec.name} FY({rec.date_start.year}-{rec.date_start.year+1})'
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





