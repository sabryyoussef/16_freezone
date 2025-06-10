
from odoo import api, fields, models,_
from odoo.exceptions import UserError, ValidationError

class Sites(models.Model):
    _name = 'password.tags'

    name = fields.Char(reuired=True)
    color = fields.Integer('Color')
