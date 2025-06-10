
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    sub_folder_file_id = fields.Many2one('sub.folder.files', string='Sub Folder File')


class SubFolderFilesActivityWizard(models.TransientModel):
    _name = 'files.activity.wizard'

    date_from = fields.Datetime('Start Date', required=True)
    date_to = fields.Datetime('End Date', required=True)
    activity_type_id = fields.Many2one('mail.activity.type', string='Activity Type', required=True)
    assigned_to_id = fields.Many2one('res.users', string='Assigned To', required=True)
    summary = fields.Char('Summary', required=True)
    sub_folder_file_id = fields.Many2one('sub.folder.files', string='Sub Folder File')

    @api.model
    def default_get(self, fields):
        res = super(SubFolderFilesActivityWizard, self).default_get(fields)
        res['sub_folder_file_id'] = self.env.context.get('active_id')
        return res

    def create_activity(self):
        partners = [self.sub_folder_file_id.partner_id.id, self.create_uid.partner_id.id]
        partner_commands = [(6, 0, partners)]
        alarm_commands = [(6, 0, [1, 2])]
        calendar_event = self.env['calendar.event'].create({
            'name': self.summary,
            'start': self.date_from,
            'stop': self.date_to,
            'user_id': self.assigned_to_id.id,
            'show_as': 'free',
            'partner_ids': partner_commands,
            'alarm_ids': alarm_commands,
            'sub_folder_file_id': self.sub_folder_file_id.id,
        })
        return calendar_event
