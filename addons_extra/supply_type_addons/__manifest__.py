
{
    'name': 'supply_type_addons',
    'version': '1.0',
    'license': 'LGPL-3',
    'depends': ['base', 'account', 'sale', 'purchase'],
    'data': [
        'views/res_partner.xml',
        'views/res_user.xml',
        'views/supply_type.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
    ],
    'installable': True,
    'application': True,

}
