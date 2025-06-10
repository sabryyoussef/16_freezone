
from odoo import api, fields, models

class Move(models.Model):
    _inherit = 'account.move'

    sale_id = fields.Many2one('sale.order')
    payment_method = fields.Selection(selection=[
        ('bank', "Bank"),
        ('visa', "Stripe"),
    ], string="Payment Method", tracking=3, default='bank')
