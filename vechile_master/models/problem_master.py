from odoo import models, fields, api


class ProblemMaster(models.Model):
    _name = 'problem.master'
    _description = 'Problem Master'
    _rec_name = 'problem_name'

    problem_name = fields.Char(string='Problem Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)


class StatusMaster(models.Model):
    _name = 'status.master'
    _description = 'Status Master'
    _rec_name = 'status_name'

    status_name = fields.Char(string='Status Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)


class WorkSectionMaster(models.Model):
    _name = 'work.section.master'
    _description = 'Work Section Master'
    _rec_name = 'section_name'

    section_name = fields.Char(string='Section Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True, string='Active')


class RepairProblem(models.Model):
    _name = 'repair.problem'
    _description = 'Repair Problem'
    _order = 'sequence'

    sequence = fields.Integer(string='Sequence', default=10)
    repair_id = fields.Many2one('repair.order', string='Repair Order', required=True, ondelete='cascade')
    problem_id = fields.Many2one('problem.master', string='Problem/Fault', required=True)
    status_id = fields.Many2one('status.master', string='Work Status', required=True)
    remarks = fields.Text(string='remarks')

    # Work Section
    employee_id = fields.Many2one('hr.employee', string='Worker', domain="[('department_id.name', 'ilike', 'worker')]")
    work_description = fields.Text(string='Work Description')
    work_section_id = fields.Many2one('work.section.master', string='Work Section', required=True)
