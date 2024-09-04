# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from lxml import etree


# import simplejson


class Partner(models.Model):
    _inherit = "res.users"

    supplier_type_ids = fields.Many2many('supplier.type', string='Allowed Supplier Types')

