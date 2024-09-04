from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_customer = fields.Boolean(string='Is Customer', store=True)
    is_supplier = fields.Boolean(string='Is Vendor', store=True)
    supply_type = fields.Many2many('supply.type', string='Vendor Supply Type', store=True)
    user_id = fields.Many2one('res.users', string='User id', store=True)

    @api.onchange('is_supplier')
    def _onchange_is_supplier(self):
        """Update the user_id and supply_type based on changes to is_supplier."""
        if self.is_supplier:
            self.user_id = self.env.user
            self.supply_type = self.env.user.supply_type_ids

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=None):
        """Filter partners based on the user's supply types during name search."""
        if args is None:
            args = []
        user = self.env.user
        if user and user.supply_type_ids:
            args += [('supply_type', 'in', user.supply_type_ids.ids)]
        return super(ResPartner, self).name_search(name=name, args=args, operator=operator, limit=limit)
