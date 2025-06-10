
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class Return(models.TransientModel):
    _name = 'return.project.wizard'

    reason = fields.Text(string="Reason")
    project_id = fields.Many2one('project.project',string='Current Stage')
    user_id = fields.Many2one('res.users', string='User', required=True)
    type = fields.Selection(string="Typ", selection=[('hand', 'Handover'), ('compliance', 'Compliance'),
                                                     ('required', 'Required'), ('deliverable', 'Deliverable'),
                                                     ('partner_fields', 'Partner Fields'), ], required=False, )

    def add_reason(self):
        for rec in self:
            project = rec.project_id
            if rec.type == 'partner_fields':
                project.is_complete_return_partner_fields = True
                project.is_complete_partner_fields = False
                project.is_confirm_partner_fields = False
                project.is_update_partner_fields = False
                project.is_second_complete_partner_fields_check = 1
                body = _(
                    "<b>Partner Fields Returned.</b><br/>"
                    "<b>Comment:</b> %(comment)s<br/>"
                    "<b>Comment for:</b> <a href='#' data-oe-model='res.partner' data-oe-id='%(partner_id)d'>@%(user_name)s</a><br/><br/>"
                ) % {
                           'comment': self.reason or 'No Comment',
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

            if rec.type == 'required':
                project.is_complete_return_required = True
                project.is_complete_required = False
                project.is_confirm_required = False
                project.is_update_required = False
                project.is_second_complete_required_check = 1
                body = _(
                    "<b>Required Returned.</b><br/>"
                    "<b>Comment:</b> %(comment)s<br/>"
                    "<b>Comment for:</b> <a href='#' data-oe-model='res.partner' data-oe-id='%(partner_id)d'>@%(user_name)s</a><br/><br/>"
                ) % {
                           'comment': self.reason or 'No Comment',
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

            if rec.type == 'deliverable':
                project.is_complete_return_deliverable = True
                project.is_complete_deliverable = False
                project.is_confirm_deliverable = False
                project.is_update_deliverable = False
                project.is_second_complete_deliverable_check = 1
                body = _(
                    "<b>Deliverable Returned.</b><br/>"
                    "<b>Comment:</b> %(comment)s<br/>"
                    "<b>Comment for:</b> <a href='#' data-oe-model='res.partner' data-oe-id='%(partner_id)d'>@%(user_name)s</a><br/><br/>"
                ) % {
                           'comment': self.reason or 'No Comment',
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



