from odoo import fields, models
from random import randint

class RiskAssessment(models.Model):
    _description = 'Partner Tags'
    _name = 'partner.risk.assessment'
    _order = 'name'

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char(string='Name', required=True, translate=True)
    color = fields.Integer(string='Color', default=_get_default_color)


