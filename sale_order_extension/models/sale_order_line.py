from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    pricelist_item = fields.Many2one('product.pricelist.item', string='Price List Item')

    @api.onchange('pricelist_item')
    def _onchange_pricelist_item(self):
        if self.pricelist_item:
            self.price_unit = self.pricelist_item.fixed_price
