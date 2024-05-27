# -*- coding: utf-8 -*-
from odoo import models, fields

class CDRLog(models.Model):
    _inherit = 'cdr.log'

    #Field to extract the Outgoing and Incoming Calls
    length = fields.Integer(string='Length', store=True)