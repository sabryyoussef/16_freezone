
from odoo import api, fields, models

class PartnersStages(models.Model):
    _name = 'partner.stage'
    _order = 'sequence'

    name = fields.Char(required=True)
    sequence = fields.Integer(string="Sequence")

