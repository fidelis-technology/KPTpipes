from odoo import models, fields, api
from odoo.addons.test_impex.models import field


class HrTarget(models.Model):
    _name = 'hr.target'
    _description = 'Hr Target'

    target = fields.Float(string='Target')
    achieved = fields.Float(string='Achieved')
    outstanding = fields.Float(string='Outstanding')
    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    employee_id = fields.Many2one("hr.employee", string="Employee")
