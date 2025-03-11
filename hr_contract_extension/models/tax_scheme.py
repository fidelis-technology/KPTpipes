from odoo import models, fields


class TdsSection(models.Model):
    _name = 'tds.section'
    _description = 'Tds Section'

    name = fields.Char('Section Name')
    tds_schemes_ids = fields.One2many('tds.section.scheme', 'section_id')

class TdsSectionScheme(models.Model):
    _name = 'tds.section.scheme'
    _description = 'Tds Section Scheme'


    section_id = fields.Many2one('tds.section')
    scheme_name = fields.Char('Investment/Scheme')

    scheme_details = fields.Char('Scheme Details')
    type_of_deduction = fields.Selection([('amount', 'Amount'), ('percentage', 'Percentage %')], string='Deduction Type')
    max_limit_deduction = fields.Float('Max Limit Deduction')


    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f'{rec.scheme_name}'
