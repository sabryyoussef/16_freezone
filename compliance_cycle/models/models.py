from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PartnerAddress(models.Model):
    _name = 'res.partner.address'

    partner_id = fields.Many2one("res.partner")
    type = fields.Selection(
        [
            ('invoice', 'Invoice Address'),
            ('delivery', 'Delivery Address'),
            ('private', 'Private Address'),
            ('current', 'Current Address'),
            ('permanent', 'Permanent Address'),
            ('other', 'Other Address'),
        ], string='Address Type',
        default='contact')
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')


class Nationality(models.Model):
    _name = 'res.nationality'

    name = fields.Char(required=True)
