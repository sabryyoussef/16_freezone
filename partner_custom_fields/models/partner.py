
from odoo import api, fields, models

class Partner(models.Model):
    _inherit = 'res.partner'

    primary_support_id = fields.Many2one('hr.employee', string='Primary Support')
    secondary_support_id = fields.Many2one('hr.employee', string='Secondary Support')
    accountant1_id = fields.Many2one('hr.employee', string='Accountant 1')
    accountant2_id = fields.Many2one('hr.employee', string='Accountant 2')
