{
    'name': 'KPT Sale Order Extension',
    'version': '17.0.1.0.1',
    'category': 'Sales',
    'depends': ['sale_management', 'sale', 'sale_order_discount_approval_odoo','stock'],
    'data': [
        'views/sale_order_view.xml',
        'views/delivery_slip_template.xml',
        'views/kpt_sale_quotation_template.xml',
        'views/kpt_pro_forma_invoice.xml',
        'views/stock_picking.xml'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': True,
}
