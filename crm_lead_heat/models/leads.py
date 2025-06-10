from odoo import fields, models


class Leads(models.Model):
    _inherit = 'crm.lead'
    lead_heat = fields.Selection([
        ('cold', 'Cold'),
        ('worm', 'Warm'),
        ('hot', 'Hot'),
    ], required=1, default='cold')
