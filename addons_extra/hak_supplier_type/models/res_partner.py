# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from lxml import etree


# import simplejson


class Partner(models.Model):
    _inherit = "res.partner"

    supplier_type_id = fields.Many2many('supplier.type', string="Supplier Type", store=True)

    @api.model
    def default_get(self, fields):
        res = super(Partner, self).default_get(fields)
        if self.env.user.supplier_type_id:
            res['supplier_type_id'] = self.env.user.supplier_type_ids.id
        return res



