from odoo import models, api, fields, _
from odoo.exceptions import MissingError, ValidationError, AccessError, UserError


class VehicleMaster(models.Model):
    _name = 'vehicle.master'
    _description = 'Vehicle Master'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']

    name = fields.Char(string="vehicle Serial Number", store=True)
    # Vehicle Details
    vehicle_name = fields.Char(string="Vehicle Number", store=True)
    number_plate = fields.Char(string="Number Plate", store=True)
    chassis_number = fields.Char('Chassis Number', help='Unique number written on the vehicle motor (VIN/SN number)',
                                 copy=False)
    create_date = fields.Date(string="Created On", store=True, default=fields.Date.today())
    # Vehicle Model Details
    model_name = fields.Char(string="Model name", store=True)
    model_year = fields.Char(string="Model Year")
    model_transmission = fields.Selection(
        [('manual', 'Manual'), ('automatic', 'Automatic')], 'Transmission', store=True, readonly=False)
    color = fields.Char(string="Vehicle Color")
    # Vehicle manufacturer Details
    manufacturer_name = fields.Char(string="Manufacturer Name", store=True)
    horse_power = fields.Char(string="Horse Power", store=True)
    engine_power = fields.Char(string="Engine Power", help='Power in KM Vehicle')
    fuel_type = fields.Selection(
        [('diesel', 'Diesel'),
         ('petrol', 'Petrol'),
         ('gasoline', 'Gasoline'),
         ('full_hybrid', 'Full Hybrid'),
         ('plug_in_hybrid_diesel', 'Plug-in Hybrid Diesel'),
         ('plug_in_hybrid_gasoline', 'Plug-in Hybrid Gasoline'),
         ('cng', 'CNG'),
         ('lpg', 'LPG'),
         ('hydrogen', 'Hydrogen'),
         ('electric', 'Electric')], 'Fuel Type', store=True, readonly=False)
    note = fields.Text(string="Description")
    image = fields.Image(string='Image')
    driver_id = fields.Many2one('hr.employee', string='Driver', domain="[('department_id.name', 'ilike', 'driver')]")
    driver_mobile = fields.Char(related='driver_id.mobile_phone', string='Mobile No', readonly=True)
    doc_attach = fields.Many2many(
        'ir.attachment',  # Model to relate to
        'vehicle_master_ir_attachment_rel',  # Name of the relationship table
        'vehicle_master_id',  # Field in the relationship table referring to this model
        'attachment_id',  # Field in the relationship table referring to `ir.attachment`
        string='Vehicle Docs',  # Label for the field
        help="Attach multiple documents related to the vehicle"
    )
    # New field to store the related repairs
    repair_order_ids = fields.One2many('repair.order', 'vehicle_name', string='Repairs Underway')

    # Smart button count
    repair_count = fields.Integer(string="Repair Orders Count", compute='_compute_repair_count')

    product_issue_count = fields.Integer(string='Product Issues', compute='_compute_product_issue_count')

    def _compute_product_issue_count(self):
        """Compute the count of product issues related to this vehicle."""
        for vehicle in self:
            vehicle.product_issue_count = self.env['product.issue'].search_count([('vehicle_id', '=', vehicle.id)])

    def action_view_product_issues(self):
        """Returns an action to view product issues related to this vehicle."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Issues',
            'view_mode': 'tree,form',
            'res_model': 'product.issue',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }

    @api.depends('repair_order_ids')
    def _compute_repair_count(self):
        for vehicle in self:
            vehicle.repair_count = len(vehicle.repair_order_ids)

    # Smart button action to view the repairs
    def action_view_repairs(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Repairs'),
            'res_model': 'repair.order',
            'view_mode': 'tree,form',
            'domain': [('vehicle_name', '=', self.id)],
            'context': {'default_vehicle_name': self.id},
        }

    @api.constrains('name')
    def _check_duplicate_name(self):
        for record in self:
            if self.search_count([('name', '=', record.name)]) > 1:
                raise ValidationError(f"The name '{record.name}' already exists. Please choose a different name.")
