
from odoo import api, fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'

    commission_id = fields.Many2one('crm.commission')
