# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Fidelis Onboarding Addons',
    'version': '17.0',
    'summary': 'Fidelis Onboarding Addons',
    'sequence': 10,
    'description': """ Fidelis Onboarding Addons""",
    'category': 'Employee/Teams',
    'depends': ['base', 'web', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/onboarding.xml',
        'views/mail_template.xml',
        'views/onboarding_form_menu.xml',
        'views/onboarding_mail.xml',
        # 'views/onboarding_web_template.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
