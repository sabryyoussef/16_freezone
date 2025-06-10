
from odoo import api, fields, models

class Partner(models.Model):
    _inherit = 'res.partner'

    pass_ids = fields.One2many('password.password','partner_id')
