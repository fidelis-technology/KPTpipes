from odoo import models, api, fields, _


class StockLot(models.Model):
    _inherit = 'stock.lot'

    customer_name = fields.Many2one(comodel_name='res.partner', string="Delivered Customer", compute='find_customer_name')
    stock_ids = fields.One2many('stock.move.line', 'lot_id', string='stock_ids')
    vendor_warr_date = fields.Date(related='stock_ids.vendor_warranty_date', string='vendor date')
    customer_warr_date = fields.Date(related='stock_ids.warranty_date_lot', string="Customer Warr Date")
    vendor_warranty_date = fields.Date(string="Vendor Warranty Date", store=True, compute='cal_vals')
    warranty_date_lot = fields.Date(string='Customer Warranty Date', store=True, related='stock_ids.warranty_date_lot')

    def find_customer_name(self):
        for rec in self:
            rec.customer_name = rec.repair_line_ids.partner_id

    @api.depends('vendor_warr_date')
    def cal_vals(self):
        for rec in self:
            rec.vendor_warranty_date = rec.vendor_warr_date

