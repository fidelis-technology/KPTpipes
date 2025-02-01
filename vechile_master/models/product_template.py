from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = "product.template"

    minimum_quantity = fields.Float(
        string="Minimum Quantity",
        help="Minimum quantity threshold for stock",
        groups="stock.group_stock_user"
    )
    maximum_quantity = fields.Float(
        string="Maximum Quantity",
        help="Maximum quantity threshold for stock",
        groups="stock.group_stock_user"
    )
    low_on_stock = fields.Boolean(
        string="Low on Stock",
        compute="_compute_low_on_stock",
        store=True,
        groups="stock.group_stock_user",
        help="Indicates if the product is running low on stock"
    )

    @api.depends('product_variant_ids.qty_available', 'minimum_quantity')
    def _compute_low_on_stock(self):
        for product in self:
            orderpoints = self.env['stock.warehouse.orderpoint'].search([
                ('product_id', 'in', product.product_variant_ids.ids)
            ])
            qty_on_hand = sum(orderpoints.mapped('qty_on_hand')) if orderpoints else 0
            product.low_on_stock = qty_on_hand <= product.minimum_quantity if product.minimum_quantity > 0 else False
