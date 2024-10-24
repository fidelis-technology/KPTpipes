from odoo import models, api, fields, _


class SendMailCandidate(models.Model):
    _name = 'send.mail.candidate'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Candidate'

    candidate_name = fields.Char(string='Candidate Name', store=True)
    name = fields.Char(string='Name', related='candidate_name')
    email = fields.Char(string='Email', store=True)
    created_on = fields.Date(string='Created On', default=fields.Date.today())
    created_by = fields.Many2one('res.users', string='Recruiter', default=lambda self: self.env.user)
    stage = fields.Selection([('Draft', 'Draft'),
                              ('Confirm', 'Confirmed'),
                              ('Cancel', ' Cancelled')], default='Draft', strting='Status')

    def action_confirm(self):
        if self.stage == 'Draft':
            self.stage = 'Confirm'

    def action_send_mail(self):
        """Logic to trigger the onboarding mail wizard"""
        # You can call the mail wizard or implement your mail logic here
        mail_wizard = self.env['onboarding.mail.send'].create({
            'applicant_ids': [(6, 0, self.ids)]
        })
        return mail_wizard.action_send_mail()
