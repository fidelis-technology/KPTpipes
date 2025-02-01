from odoo import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'
    _name = 'stock.move'  # Explicitly redefine the model name
    _inherit = ['stock.move', 'mail.thread']  # Add mail.thread for logging functionality

    unit_cost = fields.Float(
        string='Unit Cost',
        digits='Product Price',
        tracking=True,
        copy=False
    )
    display_taxes = fields.Many2many(
        'account.tax',
        string='Customer Taxes',
        compute='_compute_product_info',
        store=False
    )
    total_cost = fields.Float(
        string='Subtotal',
        compute='_compute_total_costs',
        store=True,
        digits='Product Price'
    )
    total_cost_with_tax = fields.Float(
        string='Total With Tax',
        compute='_compute_total_costs',
        store=True,
        digits='Product Price'
    )

    @api.model
    def create(self, vals):
        if vals.get('product_id'):
            product = self.env['product.product'].browse(vals['product_id'])
            vals['unit_cost'] = product.standard_price
        return super().create(vals)

    @api.depends('product_id')
    def _compute_product_info(self):
        for move in self:
            if not move.unit_cost and move.product_id:
                move.unit_cost = move.product_id.standard_price
            move.display_taxes = move.product_id.taxes_id if move.product_id else False

    @api.depends('quantity', 'unit_cost', 'display_taxes')
    def _compute_total_costs(self):
        for move in self:
            quantity = move.quantity or 0.0  # Use the 'quantity' field instead of 'product_uom_qty'
            unit_cost = move.unit_cost or 0.0
            subtotal = quantity * unit_cost

            # Calculate total with taxes
            total_with_tax = subtotal
            if move.display_taxes:
                for tax in move.display_taxes:
                    if tax.amount_type == 'percent':
                        total_with_tax += subtotal * (tax.amount / 100.0)

            move.total_cost = subtotal
            move.total_cost_with_tax = total_with_tax

    def write(self, vals):
        # Track changes in unit cost
        if 'unit_cost' in vals:
            for record in self:
                if record.unit_cost != vals['unit_cost']:
                    message = f"Unit Cost changed from {record.unit_cost} to {vals['unit_cost']}"
                    record.message_post(body=message)  # Use message_post for tracking
        return super().write(vals)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_inventory_operation = fields.Boolean(
        compute='_compute_is_inventory_operation',
        store=False
    )
    total_picking_cost = fields.Float(
        string='Total Cost',
        compute='_compute_picking_totals',
        store=True,
        digits='Product Price'
    )
    total_picking_cost_with_tax = fields.Float(
        string='Total With Tax',
        compute='_compute_picking_totals',
        store=True,
        digits='Product Price'
    )

    @api.depends('picking_type_id', 'picking_type_code')
    def _compute_is_inventory_operation(self):
        for rec in self:
            rec.is_inventory_operation = (
                    rec.picking_type_code in ('incoming', 'outgoing', 'internal') and
                    not self.env.context.get('default_repair_id')
            )

    @api.depends('move_ids_without_package.quantity', 'move_ids_without_package.total_cost',
                 'move_ids_without_package.total_cost_with_tax')
    def _compute_picking_totals(self):
        for picking in self:
            # Calculate totals based on the 'quantity' field from related stock moves
            picking.total_picking_cost = sum(picking.move_ids_without_package.mapped('total_cost'))
            picking.total_picking_cost_with_tax = sum(picking.move_ids_without_package.mapped('total_cost_with_tax'))
