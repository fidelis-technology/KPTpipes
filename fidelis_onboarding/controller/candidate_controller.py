import base64
from werkzeug.utils import secure_filename
from odoo.http import request, Controller, route


class WebFormController(Controller):
    @route('/webform', auth='public', website=True)
    def web_form(self, **kwargs):
        return request.render('fidelis_onboarding.web_form_template')

    @route('/webform/submit', type='http', auth='public', website=True, methods=['POST'])
    def web_form_submit(self, **post):
        # Function to process files and create ir.attachment records
        def process_file(file, res_model, res_id):
            if file:
                attachment = request.env['ir.attachment'].sudo().create({
                    'name': file.filename,
                    'res_model': res_model,
                    'res_id': res_id,
                    'datas': base64.b64encode(file.read()),
                    'type': 'binary',
                    'mimetype': file.content_type
                })
                return [(4, attachment.id)]  # Many2many 'link' operation
            return False

        # Create the onboarding record first to get the ID
        onboarding_record = request.env['onboarding'].sudo().create({
            'candidate_name': post.get('candidate_name'),
            'email': post.get('email'),
            'contact_number': post.get('contact_number'),
            'dob': post.get('date_of_birth'),
            'aadhar_no': post.get('aadhar_no'),
            'pan_number': post.get('pan_number'),
            'present_address': post.get('present_address'),
            'permanent_address': post.get('permanent_address'),
        })

        # Process each file input and attach them to the onboarding record
        onboarding_record.write({
            'aadhar_card': process_file(post.get('aadhar_card'), 'onboarding', onboarding_record.id),
            'pan_card': process_file(post.get('pan_card'), 'onboarding', onboarding_record.id),
            'payslips_last_3_months': process_file(post.get('payslips_last_3_months'), 'onboarding', onboarding_record.id),
            'bank_statement_6_months': process_file(post.get('bank_statement_6_months'), 'onboarding', onboarding_record.id),
            'educational_highest': process_file(post.get('educational_highest'), 'onboarding', onboarding_record.id),
            'salary_revision_letter': process_file(post.get('salary_revision_letter'), 'onboarding', onboarding_record.id),
            'experience_letter': process_file(post.get('experience_letter'), 'onboarding', onboarding_record.id),
            'updated_resume': process_file(post.get('updated_resume'), 'onboarding', onboarding_record.id),
            'employee_photo': process_file(post.get('employee_photo'), 'onboarding', onboarding_record.id),
        })

        # Redirect to the "Thank You" page after submission
        return request.redirect('/thank-you-page')

    @route('/thank-you-page', auth='public', website=True)
    def thank_you_page(self, **kwargs):
        return request.render('fidelis_onboarding.thank_you_page_template')
