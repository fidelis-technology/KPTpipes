# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'HR Contract Extension',
    'version': '1.2',
    'sequence': 31,
    'depends': ['hr_contract', 'hr_work_entry_contract'],
    'description': """
        This module adds an Extension of hr contract.
    """,
    "data": [
        'security/ir.model.access.csv',
        'views/tax_slab.xml',
        'views/hr_contract.xml',
        'views/res_company.xml',
        'views/tax_scheme.xml',
    ],
    'installable': True,
    'license': 'OEEL-1',
    'auto_install': False,
}
