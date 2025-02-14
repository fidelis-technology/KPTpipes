from odoo import models, fields, api



class SaleOrderGSTAutomation(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_id', 'order_line')
    def _apply_gst_taxes(self):
        """Automatically selects GST based on customer location"""
        for order in self:
            if order.partner_id and order.company_id:
                customer_state = order.partner_id.state_id
                company_state = order.company_id.state_id

                # Fetch tax records
                cgst_sgst_tax = self.env['account.tax'].search([('name', 'ilike', 'CGST'), ('type_tax_use', '=', 'sale')], limit=1)
                sgst_tax = self.env['account.tax'].search([('name', 'ilike', 'SGST'), ('type_tax_use', '=', 'sale')], limit=1)
                igst_tax = self.env['account.tax'].search([('name', 'ilike', 'IGST'), ('type_tax_use', '=', 'sale')], limit=1)

                # Apply tax based on state
                for line in order.order_line:
                    if customer_state == company_state:
                        line.tax_id = [(6, 0, [cgst_sgst_tax.id, sgst_tax.id])]
                    else:
                        line.tax_id = [(6, 0, [igst_tax.id])]





class StockPickingGSTAutomation(models.Model):
    _inherit = 'stock.picking'

    @api.onchange('partner_id', 'move_ids_without_package')
    def _apply_gst_taxes(self):
        """Ensures GST tax is correctly applied in delivery orders"""
        for picking in self:
            if picking.partner_id and picking.company_id:
                customer_state = picking.partner_id.state_id
                company_state = picking.company_id.state_id

                # Fetch tax records
                cgst_sgst_tax = self.env['account.tax'].search([
                    ('name', 'ilike', 'CGST'),
                    ('type_tax_use', '=', 'sale')
                ], limit=1)
                sgst_tax = self.env['account.tax'].search([
                    ('name', 'ilike', 'SGST'),
                    ('type_tax_use', '=', 'sale')
                ], limit=1)
                igst_tax = self.env['account.tax'].search([
                    ('name', 'ilike', 'IGST'),
                    ('type_tax_use', '=', 'sale')
                ], limit=1)

                for move in picking.move_ids_without_package:
                    # If sale_line_id exists (linked to Sale Order)
                    if move.sale_line_id:
                        if customer_state == company_state:
                            move.tax_id = [(6, 0, [cgst_sgst_tax.id, sgst_tax.id])]
                        else:
                            move.tax_id = [(6, 0, [igst_tax.id])]

                    # For manual Inventory deliveries (no Sale Order)
                    elif move.product_id:
                        if customer_state == company_state:
                            move.tax_id = [(6, 0, [cgst_sgst_tax.id, sgst_tax.id])]
                        else:
                            move.tax_id = [(6, 0, [igst_tax.id])]


class AccountMoveGSTAutomation(models.Model):
    _inherit = 'account.move'

    @api.onchange('partner_id')
    def _apply_gst_taxes(self):
        """Automatically selects GST based on vendor location"""
        for move in self:
            if move.partner_id and move.company_id:
                vendor_state = move.partner_id.state_id
                company_state = move.company_id.state_id

                cgst_sgst_tax = self.env['account.tax'].search([('name', '=', 'CGST+SGST')], limit=1)
                igst_tax = self.env['account.tax'].search([('name', '=', 'IGST')], limit=1)

                tax_to_apply = cgst_sgst_tax if vendor_state == company_state else igst_tax

                for line in move.invoice_line_ids:
                    line.tax_ids = [(6, 0, tax_to_apply.ids)]

