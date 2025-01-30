from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = "stock.picking"

    amount_untaxed = fields.Monetary(string="Untaxed Amount", store=True, compute='_compute_amounts', tracking=5)
    amount_tax = fields.Monetary(string="Taxes", store=True, compute='_compute_amounts')
    amount_total = fields.Monetary(string="Total", store=True, compute='_compute_amounts', tracking=4)
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        compute='_compute_currency_id',
        store=True,
        ondelete='restrict'
    )
    tax_totals = fields.Binary(compute='_compute_tax_totals', exportable=False)
    note = fields.Text()
    amount_total_rounded = fields.Float(
        string="Rounded Total",
        compute="_compute_price_total_rounded",
        store=True,
        help="Price Total rounded to the nearest integer."
    )

    amount_total_difference = fields.Float(
        string="Rounding Difference",
        compute="_compute_price_total_difference",
        store=True,
        help="Difference between the rounded price total and the original price total."
    )

    @api.depends('amount_total')
    def _compute_price_total_rounded(self):
        """Compute the rounded value of the price_total field."""
        for picking in self:
            picking.amount_total_rounded = round(picking.amount_total) if picking.amount_total else 0.0

    @api.depends('amount_total', 'amount_total_rounded')
    def _compute_price_total_difference(self):
        """Compute the difference between the rounded value and the original price_total."""
        for picking in self:
            picking.amount_total_difference = (picking.amount_total_rounded - picking.amount_total) if picking.amount_total else 0.0

    @api.depends('company_id')
    def _compute_currency_id(self):
        for picking in self:
            picking.currency_id = picking.company_id.currency_id
            
            
    @api.depends_context('lang')
    @api.depends('move_ids_without_package.tax_id', 'move_ids_without_package.price_unit', 'amount_total', 'amount_untaxed', 'currency_id')
    def _compute_tax_totals(self):
        for picking in self:
            picking = picking.with_company(picking.company_id)
            picking_lines = picking.move_ids_without_package
            picking.tax_totals = picking.env['account.tax']._prepare_tax_totals(
                [x._convert_to_tax_base_line_dict() for x in picking_lines],
                picking.currency_id or picking.company_id.currency_id,
            )


    @api.depends('move_ids_without_package.price_subtotal', 'move_ids_without_package.price_tax', 'move_ids_without_package.price_total')
    def _compute_amounts(self):
        """Compute the total amounts of the SO."""
        for picking in self:
            picking = picking.with_company(picking.company_id)
            picking_lines = picking.move_ids_without_package

            if picking.company_id.tax_calculation_rounding_method == 'round_globally':
                tax_results = picking.env['account.tax']._compute_taxes([
                    line._convert_to_tax_base_line_dict()
                    for line in picking_lines
                ])
                totals = tax_results['totals']
                amount_untaxed = totals.get(picking.currency_id, {}).get('amount_untaxed', 0.0)
                amount_tax = totals.get(picking.currency_id, {}).get('amount_tax', 0.0)
            else:
                amount_untaxed = sum(picking_lines.mapped('price_subtotal'))
                amount_tax = sum(picking_lines.mapped('price_tax'))

            picking.amount_untaxed = amount_untaxed
            picking.amount_tax = amount_tax
            picking.amount_total = picking.amount_untaxed + picking.amount_tax




