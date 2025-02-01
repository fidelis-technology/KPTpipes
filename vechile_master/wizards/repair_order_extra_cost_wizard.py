from odoo import models, fields, api
from datetime import datetime

class RepairOrderExtraCostWizard(models.TransientModel):
    _name = 'repair.order.extra.cost.wizard'
    _description = 'Add Extra Cost to Repair Order'

    repair_id = fields.Many2one('repair.order', string='Repair Order', required=True)
    workshop_id = fields.Many2one('workshop.master', string='Workshop', required=True)
    repair_date = fields.Date(string='Repair Date', default=fields.Date.context_today)
    invoice_number = fields.Char(string='Invoice Number')
    source_document = fields.Binary(string='Source Document')
    source_document_filename = fields.Char(string='Document Filename')
    equipment_line_ids = fields.One2many('repair.order.extra.cost.equipment.line', 'wizard_id', string='Equipment Lines')
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount', store=True)
    remarks = fields.Text(string='Remarks')

    @api.model
    def default_get(self, fields_list):
        res = super(RepairOrderExtraCostWizard, self).default_get(fields_list)
        if self._context.get('active_model') == 'repair.order' and self._context.get('active_id'):
            res['repair_id'] = self._context.get('active_id')
        return res

    @api.depends('equipment_line_ids.amount')
    def _compute_total_amount(self):
        for wizard in self:
            wizard.total_amount = sum(wizard.equipment_line_ids.mapped('amount'))

    def action_add_extra_cost(self):
        for wizard in self:
            description = f"""
Workshop: {wizard.workshop_id.workshop_name}
Invoice Number: {wizard.invoice_number or 'N/A'}

Equipment Details:"""
            for i, line in enumerate(wizard.equipment_line_ids, 1):
                description += f"\nSerial Number {i}: {line.equipment_id.equipment_name} - {line.amount}"
            
            if wizard.remarks:
                description += f"\n\nRemarks: {wizard.remarks}"

            for line in wizard.equipment_line_ids:
                self.env['repair.order.extra.cost'].create({
                    'repair_id': wizard.repair_id.id,
                    'workshop_id': wizard.workshop_id.id,
                    'repair_date': wizard.repair_date,
                    'extra_price': line.amount,
                    'description': description,
                    'equipment_name': line.equipment_id.equipment_name,
                    'serial_number': line.sequence,
                })

class RepairOrderExtraCostEquipmentLine(models.TransientModel):
    _name = 'repair.order.extra.cost.equipment.line'
    _description = 'Equipment Line for Extra Cost'

    wizard_id = fields.Many2one('repair.order.extra.cost.wizard', string='Wizard')
    equipment_id = fields.Many2one('equipment.master', string='Equipment', required=True)
    amount = fields.Float(string='Amount', required=True)
    sequence = fields.Integer(string='Serial Number', compute='_compute_sequence', store=True)

    @api.depends('wizard_id.equipment_line_ids')
    def _compute_sequence(self):
        for line in self:
            if line.wizard_id:
                line.sequence = list(line.wizard_id.equipment_line_ids).index(line) + 1
            else:
                line.sequence = 0
