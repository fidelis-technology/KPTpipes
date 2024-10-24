from odoo import models, api, fields, _
from odoo.exceptions import UserError


class OnboardingMailSend(models.TransientModel):
    _name = 'onboarding.mail.send'
    _inherit = 'mail.composer.mixin'
    _description = 'Send mails to applicants'

    applicant_ids = fields.Many2many('send.mail.candidate', string='Applications', required=True)
    author_id = fields.Many2one('res.partner', 'Author', required=True,
                                default=lambda self: self.env.user.partner_id.id)

    @api.depends('subject')
    def _compute_render_model(self):
        self.render_model = 'send.mail.candidate'

    def action_send_mail(self):
        """Send an email to the applicant using the onboarding mail template."""
        self.ensure_one()

        # Get the mail template
        template = self.env.ref('fidelis_onboarding.onboarding_mail_template')

        for applicant in self.applicant_ids:
            if not applicant.email:
                raise UserError(_('Applicant does not have an email address!'))

            # Prepare the template with the specific applicant
            template_values = {
                'email_to': applicant.email,
                'email_from': self.env.user.partner_id.email,  # Current user's email
                'subject': template.subject,  # Use the subject defined in the template
                'body_html': template.body_html,  # Use the HTML body defined in the template
            }

            # Send the email using the template
            template.write(template_values)
            template.send_mail(applicant.id, force_send=True)  # Send the mail to the applicant
            self.env['mail.message'].create({
                'model': 'send.mail.candidate',
                'subject': template.subject,
                'body': template.body_html,
                'message_type': 'notification',
                'subtype_id': self.env.ref('mail.mt_note').id,
            })
            # Log the message to the chatter of the applicant's record
            applicant.message_post(
                body=template.body_html,  # Message body
                subject=template.subject,  # Message subject
                message_type='comment',  # Type of message (comment, email, etc.)
                subtype_xmlid="mail.mt_note"  # Use 'note' or 'comment' subtype
            )
