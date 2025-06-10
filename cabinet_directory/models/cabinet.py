from odoo import api, fields, models
from odoo.exceptions import ValidationError

class CabinetDirectory(models.Model):
    _name = 'cabinet.directory'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char()
    work_location_id = fields.Many2one('hr.work.location', string='Work Location')
    user_id = fields.Many2one('res.users', string='Responsible Person')
    directory_ids = fields.One2many("directory.folder",'cabinet_id',string="Directory Folders")

