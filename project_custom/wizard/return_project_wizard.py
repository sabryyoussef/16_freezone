
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class Return(models.TransientModel):
    _inherit = 'return.project.wizard'

    def add_reason(self):
        res = super(Return, self).add_reason()
        for rec in self:
            project = rec.project_id
            if rec.type == 'hand':
                project.is_complete_return_hand = True
                project.is_complete_hand = False
                project.is_confirm_hand = False
                project.is_update_hand = False
                project.is_second_complete_hand_check = 1
                body = _(
                    "<b>Handover Returned.</b><br/>"
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

            if rec.type == 'compliance':
                project.is_complete_return_compliance = True
                project.is_complete_compliance = False
                project.is_confirm_compliance = False
                project.is_update_compliance = False
                project.is_second_complete_compliance_check = 1
                body = _(
                    "<b>Compliance Returned.</b><br/>"
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

        return res


