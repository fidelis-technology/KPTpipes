from odoo import models, fields, api

class WorkshopMaster(models.Model):
    _name = 'workshop.master'
    _description = 'Workshop Master'
    _rec_name = 'workshop_name'

    workshop_name = fields.Char(string='Workshop Name', required=True)
    workshop_code = fields.Char(string='Workshop Code', required=True, readonly=True, default='New')
    address = fields.Text(string='Address')
    phone = fields.Char(string='Phone Number')
    email = fields.Char(string='Email')
    contact_person = fields.Char(string='Contact Person')
    active = fields.Boolean(default=True)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('workshop_code', 'New') == 'New':
                vals['workshop_code'] = self.env['ir.sequence'].next_by_code('workshop.master') or 'New'
        return super(WorkshopMaster, self).create(vals_list)
