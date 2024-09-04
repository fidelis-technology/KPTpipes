# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrTeams(models.Model):
    _name = 'hr.team'
    _description = 'Hr Teams'
    _inherit = ['mail.thread']

    # description
    name = fields.Char('Team Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=10)
    active = fields.Boolean(default=True, help="If the active field is set to false, it will allow you to hide the Sales Team without removing it.")
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Team Leader')
    employee_id = fields.Many2one("hr.employee", string="Team Manager")
    department_id = fields.Many2one('hr.department', string='Department')
    member_ids = fields.One2many('hr.team.members', 'team_id', string='Employee Members')


class HrTeamsMembers(models.Model):
    _name = 'hr.team.members'
    _description = 'Hr Teams'

    team_id = fields.Many2one("hr.team", string="Team")
    employee_id = fields.Many2one("hr.employee", string="Employee")





