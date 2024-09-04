# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Custom Internal Hr',
    'version': '1.1',
    'summary': 'Manage your stock and logistics activities',
    'website': 'https://www.odoo.com/app/inventory',
    'depends': ['hr'],
    'category': 'Employee/Teams',
    'sequence': 25,

    'data': [

        'security/ir.model.access.csv',

        'views/hr_team.xml',
        'views/hr_department.xml',
        'views/hr_employee.xml',

    ],
    'installable': True,
    'application': True,

    'license': 'LGPL-3',
}
