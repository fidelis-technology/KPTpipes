from xlsxwriter.contenttypes import defaults

from odoo import models, fields, api
from odoo.addons.test_impex.models import field


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    team_id = fields.Many2one("hr.team", string="Team")
    current_ctc = fields.Float(string="Current CTC", default=0.0)
    emp_id = fields.Char(string="Employee Id")
    target_ids = fields.One2many('hr.target', 'employee_id', string='Target Details')
    joining_date = fields.Date(string="Date of Joining")

