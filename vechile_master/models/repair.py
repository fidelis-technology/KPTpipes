from odoo import models, api, fields, _, exceptions

import logging

_logger = logging.getLogger(__name__)


# -------------------------------------
# Repair Order Model
# -------------------------------------
class RepairOrder(models.Model):
    _inherit = 'repair.order'

    # Vehicle field
    vehicle_name = fields.Many2one(comodel_name='vehicle.master', string='Vehicle Name', store=True, required=True)
    number_plate = fields.Char(string='Number Plate', compute='_compute_vehicle_details', store=True)
    chassis_number = fields.Char(string='Chassis Number', compute='_compute_vehicle_details', store=True)
    driver_id = fields.Many2one('hr.employee', string='Driver', domain="[('department_id.name', 'ilike', 'driver')]")
    driver_mobile = fields.Char(string='Driver Mobile', related='driver_id.mobile_phone', readonly=True)

    # Time tracking
    time_in = fields.Datetime(string='Time In')
    time_out = fields.Datetime(string='Time Out')

    # state = fields.Selection([
    #     ('new', 'New'),
    #     ('under_repair', 'Under Repair'),
    #     ('done', 'Done'),
    # ], default='new', string='State', readonly=True)

    problem_ids = fields.One2many('repair.problem', 'repair_id', string='Problems', copy=True)

    def action_start_repair(self):
        """Start the repair process and update the in time."""
        self.ensure_one()
        if self.time_in:
            raise exceptions.UserError('The repair has already been started.')
        self.time_in = fields.Datetime.now()

    def action_end_repair(self):
        """End the repair process and update the out time."""
        self.ensure_one()
        if not self.time_in:
            raise exceptions.UserError('The repair must be started before it can be ended.')
        if self.time_out:
            raise exceptions.UserError('The repair has already been completed.')
        self.time_out = fields.Datetime.now()

    @api.onchange('vehicle_name')
    def _onchange_vehicle_name(self):
        if self.vehicle_name and self.vehicle_name.driver_id:
            self.driver_id = self.vehicle_name.driver_id

    @api.depends('vehicle_name')
    def _compute_vehicle_details(self):
        for repair in self:
            if repair.vehicle_name:
                repair.number_plate = repair.vehicle_name.number_plate
                repair.chassis_number = repair.vehicle_name.chassis_number

    # Subtotal Field
    subtotal = fields.Float(string="Subtotal", compute='_compute_subtotal')
    extra_cost_ids = fields.One2many('repair.order.extra.cost', 'repair_id', string="Extra Costs")

    # Extra cost field for third-party costs
    extra_cost = fields.Float(string="Extra Cost", compute='_compute_extra_cost')

    # Final cost field (subtotal + extra cost)
    final_cost = fields.Float(string="Final Cost", compute='_compute_final_cost')

    @api.depends('move_ids.total_cost')
    def _compute_subtotal(self):
        for repair in self:
            subtotal = sum(line.product_uom_qty * line.product_cost for line in repair.move_ids)
            repair.subtotal = subtotal

    @api.depends('extra_cost_ids.extra_price')
    def _compute_extra_cost(self):
        for repair in self:
            # Summing up all extra prices from the related extra costs
            repair.extra_cost = sum(extra.extra_price for extra in repair.extra_cost_ids)

    @api.depends('subtotal', 'extra_cost')
    def _compute_final_cost(self):
        for repair in self:
            repair.final_cost = repair.subtotal + repair.extra_cost

    # Smart button function to view extra cost details
    def action_view_extra_costs(self):
        return {
            'name': _('Extra Costs'),
            'view_mode': 'tree,form',
            'res_model': 'repair.order.extra.cost',
            'type': 'ir.actions.act_window',
            'domain': [('repair_id', '=', self.id)],  # Filter records related to this repair order
            'context': {'default_repair_id': self.id}  # Pre-fill repair_id when creating new extra costs
        }

    def action_set_to_draft(self):
        """Set the state of the repair order to draft."""
        self.write({'state': 'draft'})


# -------------------------------------
# Workshop Master Model
# -------------------------------------
class WorkshopMaster(models.Model):
    _name = 'workshop.master'
    _description = 'Workshop Master'

    name = fields.Char(string="Workshop Name", required=True)
    address = fields.Char(string="Workshop Address")
    contact_person = fields.Char(string="Contact Person")
    phone_number = fields.Char(string="Phone Number")
    email = fields.Char(string="Email")


# -------------------------------------
# Repair Order Extra Cost Model
# -------------------------------------
class RepairOrderExtraCost(models.Model):
    _name = 'repair.order.extra.cost'
    _description = 'Extra Cost for Repair Order'

    # Fields in the extra cost model
    repair_id = fields.Many2one('repair.order', string="Repair Order", required=True)
    equipment_name = fields.Char(string="Equipment Name", required=True)
    serial_number = fields.Char(string="Serial Number", required=True)
    workshop_id = fields.Many2one('workshop.master', string="Workshop", required=True)
    repair_date = fields.Date(string="Repair Date", default=fields.Date.context_today, required=True)
    extra_price = fields.Float(string="Extra Price", required=True)
    description = fields.Text(string="Description", required=False)

    supporting_documents = fields.Many2many('ir.attachment', string="Supporting Documents")

    # Sequence field
    sequence = fields.Integer(string="Sequence", compute="_compute_sequence", store=True)

    @api.depends('repair_id')
    def _compute_sequence(self):
        for record in self:
            if record.repair_id:
                # Get all related extra costs for the same repair order, ordered by ID
                extra_costs = self.search([('repair_id', '=', record.repair_id.id)], order='id')
                # Assign sequence based on the order of appearance
                for idx, line in enumerate(extra_costs, 1):
                    line.sequence = idx


# -------------------------------------
# Wizard to Add Extra Cost
# -------------------------------------
class RepairOrderExtraCostWizard(models.TransientModel):
    _name = 'repair.order.extra.cost.wizard'
    _description = 'Wizard to Add Extra Cost for Repair Order'

    # Link to the repair order
    repair_id = fields.Many2one('repair.order', string="Repair Order", required=True)

    # Fields to capture extra repair details
    equipment_name = fields.Char(string="Equipment Name", required=True)
    serial_number = fields.Char(string="Serial Number", required=True)
    workshop_id = fields.Many2one('workshop.master', string="Workshop", required=True)
    repair_date = fields.Date(string="Repair Date", default=fields.Date.context_today, required=True)
    extra_price = fields.Float(string="Extra Price", required=True)
    supporting_documents = fields.Many2many('ir.attachment', string="Supporting Documents")

    def add_extra_price(self):
        """Add the extra price as a new record to repair.order.extra.cost"""
        self.ensure_one()

        # Create a new extra cost record linked to the repair order
        self.env['repair.order.extra.cost'].create({
            'repair_id': self.repair_id.id,
            'equipment_name': self.equipment_name,
            'serial_number': self.serial_number,
            'workshop_id': self.workshop_id.id,
            'repair_date': self.repair_date,
            'extra_price': self.extra_price,
            'supporting_documents': [(6, 0, self.supporting_documents.ids)],
        })

        # Close the wizard
        return {'type': 'ir.actions.act_window_close'}


# -------------------------------------
# Stock Move Model
# -------------------------------------
class StockMove(models.Model):
    _inherit = 'stock.move'

    vehicle_name = fields.Char(string='Vehicle Name', compute='compute_name', store=True)
    repair_remarks = fields.Text(string='Repair Remarks', store=True)
    vendor_warranty_date = fields.Date(related='move_line_ids.vendor_warranty_date', string='Vendor Warranty Date',
                                       store=True)
    customer_warranty_date = fields.Date(related='move_line_ids.warranty_date_lot', string='Customer Warranty Date',
                                         store=True)
    product_cost = fields.Float(string="Cost", store=True)
    total_cost = fields.Float(string="Total Cost", compute="compute_cost_price", store=True)

    partner_ids = fields.Many2many('res.partner', string='Responsible Users')

    product_qty_available = fields.Integer(
        string='Quantity Available',
        compute='_compute_product_qty_available',
        store=True
    )

    @api.depends('product_id')
    def _compute_product_qty_available(self):
        for move in self:
            move.product_qty_available = move.product_id.qty_available if move.product_id else 0.0

    @api.depends('repair_id.vehicle_name')
    def compute_name(self):
        for rec in self:
            rec.vehicle_name = rec.repair_id.vehicle_name.name

    @api.onchange('product_id')
    def compute_product_cost_price(self):
        for rec in self:
            rec.product_cost = rec.product_id.standard_price

    @api.depends('product_cost', 'quantity')
    def compute_cost_price(self):
        for rec in self:
            rec.total_cost = rec.product_cost * rec.quantity


# -------------------------------------
# Stock Move Line Model
# -------------------------------------
class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    vehicle_name = fields.Char(string='Vehicle Name', compute='compute_veh_name', store=True)
    repair_remarks = fields.Char(string='Repair Remarks', compute='compute_remarks', store=True)
    vendor_warranty_date = fields.Date(string="Vendor Warranty Date", store=True)
    warranty_date_lot = fields.Date(string='Customer Warranty Date')
    total_cost = fields.Float(string="Total Cost", compute="compute_total_price", store=True)
    extra_price = fields.Float(string="Extra Price", compute="compute_extra_price", store=True)
    repair_id = fields.Many2one('repair.order', string="Repair Order", ondelete='cascade')

    @api.depends('move_id.vehicle_name')
    def compute_veh_name(self):
        for rec in self:
            rec.vehicle_name = rec.move_id.vehicle_name

    @api.depends('move_id.repair_remarks')
    def compute_remarks(self):
        for rec in self:
            if rec.move_id:
                rec.repair_remarks = rec.move_id.repair_remarks

    @api.depends('move_id.total_cost')
    def compute_total_price(self):
        for rec in self:
            if rec.move_id:
                rec.total_cost = rec.move_id.total_cost

    @api.depends('move_id.repair_id.extra_cost_ids.extra_price')
    def compute_extra_price(self):
        for line in self:
            if line.move_id.repair_id:
                # Sum all the extra costs for the related repair order
                repair_order = line.move_id.repair_id
                extra_price_sum = sum(extra_cost.extra_price for extra_cost in repair_order.extra_cost_ids)
                line.extra_price = extra_price_sum
            else:
                line.extra_price = 0.0


# -------------------------------------
# Stock Picking Model
# -------------------------------------
class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # Link to the repair order
    repair_id = fields.Many2one('repair.order', string='Repair Order')

    vehicle_ids = fields.Many2many('vehicle.master', string='Vehicle Names')
