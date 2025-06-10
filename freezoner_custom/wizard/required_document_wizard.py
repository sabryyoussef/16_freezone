
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class Return(models.TransientModel):
    _name = 'required.documents.wizard'

    project_id = fields.Many2one('project.project')
    user_id = fields.Many2one('res.users', string='User', required=True)
    name = fields.Char('Document Name', required=True)

    def action_upload(self):
        for rec in self:
            project = rec.project_id
            body = _(
                "<b>Upload Document.</b><br/>"
                "<b>Comment:</b> %(comment)s<br/>"
                "<b>Comment for:</b> <a href='#' data-oe-model='project.project' data-oe-id='%(partner_id)d'>@%(user_name)s</a><br/><br/>"
            ) % {
                       'comment': 'Upload Document',
                       'partner_id': self.user_id.partner_id.id if self.user_id.partner_id else 0,
                       'user_name': self.user_id.partner_id.name if self.user_id.partner_id else 'Unknown User'
                   }

            # Log a note in the chatter
            message = project.message_post(
                body=body,
                message_type="comment",
                subtype_xmlid="mail.mt_note",
                partner_ids=[self.user_id.partner_id.id] if self.user_id.partner_id else [],
                notification=False  # Prevents automatic notification for all followers
            )

            # Create a notification manually for only the mentioned user if it doesn't already exist
            if message and self.user_id.partner_id:
                existing_notification = self.env["mail.notification"].search([
                    ("mail_message_id", "=", message.id),
                    ("res_partner_id", "=", self.user_id.partner_id.id)
                ], limit=1)

                if not existing_notification:
                    self.env["mail.notification"].create({
                        "mail_message_id": message.id,
                        "res_partner_id": self.user_id.partner_id.id,  # Notify only this partner
                        "notification_type": "inbox",  # Store in inbox, no email
                        "is_read": False,  # Mark as unread
                    })
            return {
                'name': "Document",
                'type': 'ir.actions.act_window',
                'res_model': 'documents.document',
                'view_mode': 'form',  # Kanban view only
                'context': {
                    'default_project_id': self.project_id.id,
                    'default_folder_id': self.project_id.documents_folder_id.id,
                    'default_user_id': self.user_id.id,
                },
                'target': 'new',
            }

    def action_request(self):
        for rec in self:
            project = rec.project_id
            body = _(
                "<b>Request Document.</b><br/>"
                "<b>Comment:</b> %(comment)s<br/>"
                "<b>Comment for:</b> <a href='#' data-oe-model='project.project' data-oe-id='%(partner_id)d'>@%(user_name)s</a><br/><br/>"
            ) % {
                       'comment': 'Add New Required Document',
                       'partner_id': self.user_id.partner_id.id if self.user_id.partner_id else 0,
                       'user_name': self.user_id.partner_id.name if self.user_id.partner_id else 'Unknown User'
                   }

            # Log a note in the chatter
            message = project.message_post(
                body=body,
                message_type="comment",
                subtype_xmlid="mail.mt_note",
                partner_ids=[self.user_id.partner_id.id] if self.user_id.partner_id else [],
                notification=False  # Prevents automatic notification for all followers
            )

            # Create a notification manually for only the mentioned user if it doesn't already exist
            if message and self.user_id.partner_id:
                existing_notification = self.env["mail.notification"].search([
                    ("mail_message_id", "=", message.id),
                    ("res_partner_id", "=", self.user_id.partner_id.id)
                ], limit=1)

                if not existing_notification:
                    self.env["mail.notification"].create({
                        "mail_message_id": message.id,
                        "res_partner_id": self.user_id.partner_id.id,  # Notify only this partner
                        "notification_type": "inbox",  # Store in inbox, no email
                        "is_read": False,  # Mark as unread
                    })
                # Ensure values exist before creating the record
            folder_id = project.documents_folder_id.id if project.documents_folder_id else False
            project_id = project.id if project else False
            owner_id = rec.user_id.id if rec.user_id else False

            # Step 1: Create the record in 'documents.request_wizard'
            wizard = self.env['documents.request_wizard'].create({
                'name': self.name,
                'folder_id': folder_id,
                'project_id': project_id,
                'owner_id': owner_id,
            })

            # Debugging to confirm record creation
            print(f"Created Wizard Record ID: {wizard.id}")

            # Step 2: Open the newly created record in the form view
            return {
                'name': "Request Document",
                'type': 'ir.actions.act_window',
                'res_model': 'documents.request_wizard',
                'view_mode': 'form',
                'res_id': wizard.id,  # Open the specific record
                'target': 'new',
            }

