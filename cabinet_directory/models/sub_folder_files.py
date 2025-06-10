from odoo import api, fields, models
from odoo.exceptions import ValidationError

class SubFolderFiles(models.Model):
    _name = 'sub.folder.files'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char()
    lead_id = fields.Many2one('crm.lead', string='Pipeline')
    partner_id = fields.Many2one('res.partner', string='Contact')
    folder_id = fields.Many2one('directory.folder', string='Folder')
    user_id = fields.Many2one('res.users', string='Responsible Person')
    state = fields.Selection([('on_file', 'ON FILE'), ('handed', 'HANDED OVER')], default='on_file',string='State', tracking=True)
    document_ids = fields.Many2many('res.partner.document', string='Documents')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments', required=True)

    def action_handed_over(self):
        return {
            'res_model': 'handover.wizard',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'context': {'default_sub_folder_file_id': self.id},
            'view_id': self.env.ref("cabinet_directory.handover_wizard_form_view").id,
            'target': 'new'
        }

    def action_on_file(self):
        for rec in self:
            rec.state = 'on_file'

    def action_schedule_meeting(self, smart_calendar=True):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("calendar.action_calendar_event")
        partner_ids = self.env.user.partner_id.ids
        if self.partner_id:
            partner_ids.append(self.partner_id.id)
        current_opportunity_id = self.lead_id.id or False

        # Add the domain to filter events by the sub_folder_file_id
        action['domain'] = [('sub_folder_file_id', '=', self.id)]

        action['context'] = {
            'search_default_opportunity_id': current_opportunity_id,
            'default_opportunity_id': current_opportunity_id,
            'default_partner_id': self.partner_id.id,
            'default_partner_ids': partner_ids,
            'default_name': self.name,
            'default_sub_folder_file_id': self.id,  # Pass the sub_folder_file_id to the new event
        }
        # 'Smart' calendar view: get the most relevant time period to display to the user.
        if current_opportunity_id and smart_calendar:
            mode, initial_date = self._get_opportunity_meeting_view_parameters()
            action['context'].update({'default_mode': mode, 'initial_date': initial_date})
        return action

    def open_create_activity_popup(self):
        return {
            'res_model': 'files.activity.wizard',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'context': {'default_sub_folder_file_id': self.id},
            'view_id': self.env.ref("cabinet_directory.cabinet_meeting_form_view").id,
            'target': 'new'
        }

    def send_email_activity(self):
        # Search for the correct event based on sub_folder_file_id
        event = self.env['calendar.event'].sudo().search([('sub_folder_file_id', '=', self.id)], limit=1)
        print('event ========', event)

        if event:
            # Call action_open_composer and ensure the correct context is passed
            action = event.sudo().action_open_composer()

            # Update the action to explicitly set the res_id to the event's ID
            if action:
                action['context'].update({
                    'default_res_id': event.id,  # Ensure the correct record is used
                    'default_model': 'calendar.event',  # Explicitly set the model
                })
                return action




