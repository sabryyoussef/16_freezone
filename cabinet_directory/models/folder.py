from odoo import api, fields, models
from odoo.exceptions import ValidationError


class DirectoryFolder(models.Model):
    _name = 'directory.folder'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char()
    user_id = fields.Many2one('res.users', string='Responsible Person')
    cabinet_id = fields.Many2one('cabinet.directory', string='Cabinet Directory')
    license_authority_id = fields.Many2one('product.attribute.value', string='License Authority')
    sub_folders_ids = fields.One2many("sub.folder.files",'folder_id',string="Sub Folders")
