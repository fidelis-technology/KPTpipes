from odoo import models, fields, api


class EquipmentMaster(models.Model):
    _name = 'equipment.master'
    _description = 'Equipment Master'
    _rec_name = 'equipment_name'

    equipment_name = fields.Char(string='Equipment Name', required=True)
    equipment_code = fields.Char(string='Equipment Code', required=True, readonly=True, default='New')
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('equipment_code', 'New') == 'New':
                vals['equipment_code'] = self.env['ir.sequence'].next_by_code('equipment.master') or 'New'
        return super(EquipmentMaster, self).create(vals_list)

    _sql_constraints = [
        ('equipment_code_uniq', 'unique(equipment_code)', 'Equipment Code must be unique!')
    ]
