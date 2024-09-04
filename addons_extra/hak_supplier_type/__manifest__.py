# -*- coding: utf-8 -*-

{
    'name': "Supplier Types",
    'company': '',
    'website': '',
    'version': '17.0.1.0.1',
    'support': '',
    'category': 'Purchase',
    'summary': "Define Supplier Types",
    'description': """
    """,
    'depends': ['base', 'account', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/supplier_type.xml',
        'views/res_partner.xml',
        'views/res_users.xml',
    ],
    "images": ["static/description/icon.png"],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': False,
}
