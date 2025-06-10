
from odoo import api, fields, models,_
from odoo.exceptions import UserError, ValidationError

class Sites(models.Model):
    _name = 'password.password'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(reuired=True, tracking=True)
    partner_id = fields.Many2one('res.partner',string='Contact', tracking=True)
    user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user, readonly=True, tracking=True)
    tag_ids = fields.Many2many('password.tags', string='Tags', tracking=True)
    username = fields.Char("Username", tracking=True)
    password = fields.Char("Password", tracking=True)
    site_id = fields.Many2one('password.sites', string='Site', tracking=True)
    active = fields.Boolean(default=True, tracking=True)

