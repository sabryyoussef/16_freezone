
from odoo import api, fields, models

class Source(models.Model):
    _inherit = 'utm.source'

    is_required_referred = fields.Boolean('Is Required Referred')
