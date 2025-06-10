
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HandoverWizard(models.TransientModel):
    _name = 'handover.wizard'

    attachment_ids = fields.Many2many('ir.attachment', string='Attachments', required=True)
    sub_folder_file_id = fields.Many2one('sub.folder.files', string='Sub Folder File')

    def action_add_attachments(self):
        self.sub_folder_file_id.attachment_ids = self.attachment_ids.ids
        self.sub_folder_file_id.state = 'handed'