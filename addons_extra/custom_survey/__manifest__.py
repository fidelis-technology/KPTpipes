# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Custom Internal Survey',
    'version': '1.1',
    'summary': 'Manage your Survey',
    'website': 'https://www.odoo.com/app/survey',
    'depends': ['survey'],
    'category': 'Survey',
    'sequence': 25,

    'data': [

        'views/survey_survey.xml',
        'views/survey_user.xml',

    ],
    'installable': True,
    'application': True,

    'license': 'LGPL-3',
}
