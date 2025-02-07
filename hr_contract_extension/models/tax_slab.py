from odoo import models, fields

class TaxSlab(models.Model):
    _name = 'tax.slab'
    _description = 'Tax Slab'


    tax_regime = fields.Selection([('old_regime', 'Old Tax Regime'), ('new_regime', 'New Tax Regime'), ('other_regime', 'Other Tax Regime')], string='Tax Regime')
    tax_regime_description = fields.Char(string='Tax Slab Description')
    tax_regime_per = fields.Float(string='Tax %')
    tax_regime_amt_from = fields.Float(string='Applied From')
    tax_regime_amt_to = fields.Float(string='Applied To')

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f'{rec.tax_regime_description} - ({rec.tax_regime_per} %)'





