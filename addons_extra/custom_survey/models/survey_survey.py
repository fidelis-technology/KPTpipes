from odoo import fields, api, models, _


class SurveyTemplate(models.Model):

    _inherit = 'survey.survey'

    department_id = fields.Many2one('hr.department', string='Department')
    team_ids = fields.Many2many('hr.team', string='Team')



