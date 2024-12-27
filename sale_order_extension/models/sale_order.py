
from odoo import models, fields, api

class SaleOrder(models.Model):
    """This is used to inherit 'sale.order' to add new fields and
    functionality"""
    _inherit = 'sale.order'

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






