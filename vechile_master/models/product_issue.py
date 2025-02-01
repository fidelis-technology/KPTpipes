from odoo import models, fields, api, _
import base64


class ProductIssue(models.Model):
    _name = 'product.issue'
    _description = 'Product Issue to Vehicle'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference', required=True, readonly=True, copy=False, default=lambda self: _('New'))
    issue_date = fields.Date(string='Issue Date', default=fields.Date.context_today, required=True, tracking=True)
    vehicle_id = fields.Many2one('vehicle.master', string='Vehicle', required=True, tracking=True)
    number_plate = fields.Char(string='Number Plate', related='vehicle_id.number_plate', readonly=True)
    chassis_number = fields.Char(string='Chassis Number', related='vehicle_id.chassis_number', readonly=True)
    driver_id = fields.Many2one(related='vehicle_id.driver_id', string='Driver', readonly=True, store=True)
    product_line_ids = fields.One2many('product.issue.line', 'issue_id', string='Product Lines')
    remarks = fields.Text(string='Remarks')

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id', store=True)

    total_untaxed = fields.Monetary(string='Untaxed Amount', compute='_compute_totals', store=True)
    total_tax = fields.Monetary(string='Tax Amount', compute='_compute_totals', store=True)
    total_amount = fields.Monetary(string='Total Amount', compute='_compute_totals', store=True)

    receiver_id = fields.Many2one('hr.employee', string='Receiver', tracking=True)
    issued_by = fields.Many2one('hr.employee', string='Issued By', tracking=True)
    store_keeper = fields.Many2one('hr.employee', string='Store Keeper', tracking=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True,
        default=lambda self: self.env['stock.warehouse'].search([], limit=1))

    location_dest_id = fields.Many2one(
        'stock.location',
        string='Destination Location',
        default=lambda self: self.env.ref('stock.stock_location_customers', False),
        required=True
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    document_ids = fields.Many2many(
        'ir.attachment',
        'product_issue_attachment_rel',
        'issue_id',
        'attachment_id',
        string='Documents'
    )
    document_count = fields.Integer(compute='_compute_document_count', string='Document Count')

    @api.depends('product_line_ids.subtotal', 'product_line_ids.tax_amount', 'product_line_ids.total')
    def _compute_totals(self):
        for issue in self:
            issue.total_untaxed = sum(line.subtotal for line in issue.product_line_ids)
            issue.total_tax = sum(line.tax_amount for line in issue.product_line_ids)
            issue.total_amount = sum(line.total for line in issue.product_line_ids)

    @api.depends('document_ids')
    def _compute_document_count(self):
        for record in self:
            record.document_count = len(record.document_ids)

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_done(self):
        for line in self.product_line_ids:
            line._action_done()
        self.write({'state': 'done'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_view_documents(self):
        self.ensure_one()
        return {
            'name': 'Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.document_ids.ids)],
            'context': {'default_res_model': self._name, 'default_res_id': self.id},
        }

    def action_save_issue_slip(self):
        self.ensure_one()
        report_action = self.env.ref('vechile_master.action_product_issue_slip')
        pdf_content, _ = report_action._render_qweb_pdf([self.id])

        attachment = self.env['ir.attachment'].create({
            'name': f'Issue Slip - {self.name}.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf'
        })

        self.write({'document_ids': [(4, attachment.id)]})

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('product.issue') or _('New')
        return super(ProductIssue, self).create(vals)


class ProductIssueLine(models.Model):
    _name = 'product.issue.line'
    _description = 'Product Issue Line'

    issue_id = fields.Many2one('product.issue', string='Product Issue', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', required=True, default=1.0)
    available_qty = fields.Float(string='Available Qty', compute='_compute_available_qty')
    standard_price = fields.Float(string='Unit Cost', related='product_id.standard_price', readonly=True, store=True)
    tax_ids = fields.Many2many(related='product_id.taxes_id', string='Taxes', readonly=True)

    currency_id = fields.Many2one(related='issue_id.currency_id')
    subtotal = fields.Monetary(string='Subtotal', compute='_compute_amounts', store=True)
    tax_amount = fields.Monetary(string='Tax Amount', compute='_compute_amounts', store=True)
    total = fields.Monetary(string='Total with Tax', compute='_compute_amounts', store=True)

    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        related='issue_id.warehouse_id',
        store=True
    )
    stock_move_ids = fields.One2many('stock.move', 'issue_line_id', string='Stock Moves')

    @api.depends('quantity', 'standard_price', 'tax_ids')
    def _compute_amounts(self):
        for line in self:
            subtotal = line.quantity * line.standard_price

            if line.tax_ids:
                taxes = line.tax_ids.compute_all(
                    price_unit=line.standard_price,
                    currency=line.currency_id,
                    quantity=line.quantity,
                    product=line.product_id,
                    partner=False
                )
                line.subtotal = taxes['total_excluded']
                line.tax_amount = taxes['total_included'] - taxes['total_excluded']
                line.total = taxes['total_included']
            else:
                line.subtotal = subtotal
                line.tax_amount = 0.0
                line.total = subtotal

    @api.depends('product_id')
    def _compute_available_qty(self):
        stock_quant = self.env['stock.quant']
        warehouse = self.env['stock.warehouse'].search([], limit=1)

        for line in self:
            if line.product_id and warehouse.lot_stock_id:
                line.available_qty = stock_quant._get_available_quantity(
                    line.product_id,
                    warehouse.lot_stock_id
                )
            else:
                line.available_qty = 0.0

    def _prepare_stock_move_vals(self):
        self.ensure_one()
        return {
            'name': f'{self.issue_id.name} - {self.product_id.name}',
            'product_id': self.product_id.id,
            'product_uom_qty': self.quantity,
            'product_uom': self.product_id.uom_id.id,
            'location_id': self.warehouse_id.lot_stock_id.id,
            'location_dest_id': self.issue_id.location_dest_id.id,
            'issue_line_id': self.id,
            'company_id': self.issue_id.company_id.id
        }

    def _action_done(self):
        for line in self:
            move_vals = line._prepare_stock_move_vals()
            move = self.env['stock.move'].create(move_vals)
            move._action_confirm()
            move._action_assign()
            move._action_done()




class StockMove(models.Model):
    _inherit = 'stock.move'

    issue_line_id = fields.Many2one('product.issue.line', string='Issue Line')