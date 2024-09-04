from odoo import fields, Command, models, api, _
from odoo.exceptions import UserError
from datetime import date


class SupplierType(models.Model):
    _name = 'supplier.type'

    name = fields.Char('Name')
