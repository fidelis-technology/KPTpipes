# models.py
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    display_discount_column = fields.Boolean(
        string="Display Discount Column in Quotation PDF",
        config_parameter='hide_discount_column.display_discount_column',
        default=True,
    )
