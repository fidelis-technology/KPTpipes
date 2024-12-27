from odoo import models, fields, api

class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f'{rec.pricelist_id.name} ({rec.fixed_price} Price)'
