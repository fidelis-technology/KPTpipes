from odoo import models, fields, api

class HrDepartment(models.Model):
    _inherit = 'hr.department'

    team_ids = fields.One2many('hr.team', 'department_id', string='Teams')