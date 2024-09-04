from odoo import models, fields, api, _


class ResUsers(models.Model):
    _inherit = 'res.users'

    supply_type_ids = fields.Many2many('supply.type', 'supply_type_user_rel', 'user_id', 'supply_type_id', string='Supply Types')
    partner_id = fields.Many2one('res.partner', string='Partner')
