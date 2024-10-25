# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# __manifest__.py

{
    'name': 'KPT addons',
    'version': '1.0',
    'category': 'Sales',
    'author': 'Rakesh kumar sutar',
    'depends': ['sale'],  # Depends on the Sales module
    'data': [
        'views/quotation.xml',
        'views/resconfigsettingsviews.xml'# This file contains our report modification
    ],
    'installable': True,
    'application': False,
}

