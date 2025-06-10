
from odoo import models, fields, api
from datetime import date, datetime, time

class Product(models.Model):
    _inherit = 'product.product'

    profit_margin = fields.Float("Profit Margin", compute='get_profit_margin')

    @api.depends('lst_price','standard_price')
    def get_profit_margin(self):
        for rec in self:
            rec.profit_margin = rec.lst_price - rec.standard_price
