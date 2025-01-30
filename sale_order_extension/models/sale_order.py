
from odoo import models, fields, api

class SaleOrder(models.Model):
    """This is used to inherit 'sale.order' to add new fields and
    functionality"""
    _inherit = 'sale.order'


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
        for sale in self:
            sale.amount_total_rounded = round(sale.amount_total) if sale.amount_total else 0.0

    @api.depends('amount_total', 'amount_total_rounded')
    def _compute_price_total_difference(self):
        """Compute the difference between the rounded value and the original price_total."""
        for sale in self:
            sale.amount_total_difference = (sale.amount_total_rounded - sale.amount_total) if sale.amount_total else 0.0


    def _find_mail_template(self):
        """ Get the appropriate mail template for the current sales order based on its state.

        If the SO is confirmed, we return the mail template for the sale confirmation.
        Otherwise, we return the quotation email template.

        :return: The correct mail template based on the current status
        :rtype: record of `mail.template` or `None` if not found
        """
        self.ensure_one()
        if self.env.context.get('proforma') or self.state != 'sale':
            if self.env.context.get('proforma'):
                return self.env.ref('sale_order_extension.email_template_edi_sale', raise_if_not_found=False)
            return self.env.ref('sale_order_extension.email_template_edi_sale_quotation',
                                raise_if_not_found=False)
        else:
            return self._get_confirmation_template()


    def action_revert(self):
        self.ensure_one()
        self.state = 'draft'






