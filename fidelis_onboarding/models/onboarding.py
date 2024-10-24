from odoo import models, api, fields, _
from odoo.exceptions import UserError


class Onboarding(models.Model):
    _name = 'onboarding'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', related='candidate_name')
    candidate_name = fields.Char(string='Candidate Name', store=True)
    email = fields.Char(string='Email', store=True)
    created_on = fields.Date(string='Created On', default=fields.Date.today())
    created_by = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user)
    stage = fields.Selection([('New', 'New'),
                              ('Recruiter', 'Recruiter'),
                              ('Accounting Manager', 'Accounting Manager'),
                              ('CFO', 'CFO'),
                              ('HR', 'HR')], default='New', strting='Status')
    # candidate Fields................................................................................
    contact_number = fields.Char(string='Contact Number')
    dob = fields.Date(string='Date of Birth')
    aadhar_no = fields.Char(string='Aadhar Number')
    pan_number = fields.Char(string='Pan Number')
    present_address = fields.Text(string='Present Address')
    permanent_address = fields.Text(string='Permanent Address')
    # candidate attachment Fields.....................................................................
    aadhar_card = fields.Many2many('ir.attachment', 'aadhar_card_rel', string='Aadhar')
    pan_card = fields.Many2many('ir.attachment', 'pan_card_rel', string='PAN')
    payslips_last_3_months = fields.Many2many('ir.attachment', 'payslips_rel', string='Payslips')
    bank_statement_6_months = fields.Many2many('ir.attachment', 'bank_statement_rel', string='Bank Stat')
    educational_highest = fields.Many2many('ir.attachment', 'educational_highest_rel', string='Educational')
    salary_revision_letter = fields.Many2many('ir.attachment', 'salary_revision_letter_rel', string='Salary Revision')
    experience_letter = fields.Many2many('ir.attachment', 'experience_letter_rel', string='Experience Letter')
    updated_resume = fields.Many2many('ir.attachment', 'updated_resume_rel', string='Resume')
    employee_photo = fields.Many2many('ir.attachment', 'employee_photo_rel', string='Photo')

    # recruiter Fields.................................................................................
    ctc = fields.Float(string='CTC', store=True)
    designation = fields.Char(string='Designation')
    candidate_type = fields.Selection([('New', 'New'),
                                       ('Replace', 'Replace')], string='Candidate Type')
    all_docs_verified = fields.Boolean(string='All Documents Verified', default=False, store=True)
    # finance Manager Fields...........................................................................
    po_number = fields.Char(string='PO Number', store=True)
    bill_number = fields.Char(string='Bill Number', store=True)

    # def action_send_mail(self):
    #     """Logic to trigger the onboarding mail wizard"""
    #     # You can call the mail wizard or implement your mail logic here
    #     mail_wizard = self.env['onboarding.mail.send'].create({
    #         'applicant_ids': [(6, 0, self.ids)]
    #     })
    #     return mail_wizard.action_send_mail()



