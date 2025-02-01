from odoo import models, fields


class RepairOrder(models.Model):
    _inherit = 'repair.order'

    repair_line_type = fields.Selection(default='add', selection=[('add', 'Add'), ('remove', 'Remove')],
                                        string='Repair Line Type')
    sequence = fields.Integer(string='Sequence')
