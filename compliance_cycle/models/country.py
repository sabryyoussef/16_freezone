
from odoo import api, fields, models

class Country(models.Model):
    _inherit = 'res.country'
    _rec_name = 'name'

    country_name = fields.Char(compute='get_country_name', store=True)

    @api.depends('phone_code','name')
    def get_country_name(self):
        for rec in self:
            name = str(rec.name)
            if rec.phone_code:
                name += ' (+'+ str(rec.phone_code)+')'
            rec.country_name = name


