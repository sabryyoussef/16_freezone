# -*- coding: utf-8 -*-

import logging
import math
import re
import time
from lxml import etree
from odoo import api, fields, models, tools, _

class AccountMove(models.Model):
    _inherit = 'account.move'

    usd_rate = fields.Float(compute='get_rates')
    euro_rate = fields.Float(compute='get_rates')
    bank_name = fields.Selection([('nbd', 'EMIRATES NBD'),('rak', 'RAKBank')],default='nbd', string='Bank Name')

    def get_rates(self):
        for rec in self:
            rec.usd_rate = self.env['res.currency'].sudo().search([('name','=','USD')], limit=1).rate
            rec.euro_rate = self.env['res.currency'].sudo().search([('name','=','EUR')], limit=1).rate

class Sales(models.Model):
    _inherit = 'sale.order'

    usd_rate = fields.Float(compute='get_rates')
    euro_rate = fields.Float(compute='get_rates')
    bank_name = fields.Selection([('nbd', 'EMIRATES NBD'), ('rak', 'RAKBank')], default='nbd', string='Bank Name')

    def _prepare_invoice(self, ):
        invoice_vals = super(Sales, self)._prepare_invoice()
        invoice_vals.update({
            'bank_name': self.bank_name,
        })
        return invoice_vals

    def get_rates(self):
        for rec in self:
            rec.usd_rate = self.env['res.currency'].sudo().search([('name','=','USD')], limit=1).rate
            rec.euro_rate = self.env['res.currency'].sudo().search([('name','=','EUR')], limit=1).rate


