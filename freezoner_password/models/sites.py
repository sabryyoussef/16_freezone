
from odoo import api, fields, models,_
from odoo.exceptions import UserError, ValidationError

class Sites(models.Model):
    _name = 'password.sites'

    name = fields.Char(reuired=True)
    website = fields.Char('Website Link')