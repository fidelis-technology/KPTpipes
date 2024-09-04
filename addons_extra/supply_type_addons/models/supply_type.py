from odoo import models, api, fields, _


class SupplyType(models.Model):
    _name = 'supply.type'

    name = fields.Char(string='Supply Type', store=True)

