
from odoo import api, models, tools
from odoo import _, api, fields, models
from odoo.http import request

class ResCompany(models.Model):
    _inherit = "res.company"

    @api.model
    def get_active_company(self):
        """Get active company from request"""
        if self.env.user.has_group("base.group_multi_company"):
            cids = request.httprequest.cookies.get("cids", str(self.env.company.id))
            try:
                company_id = int(cids.split(",")[0])
                company = self.browse(company_id)
            except ValueError:
                company = self.env.company
        else:
            company = self.env.company
        return company

class CustomMailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    # @api.returns('mail.message', lambda value: value.id)
    # def message_post(self, *,
    #                  body='', subject=None, message_type='notification',
    #                  email_from=None, author_id=None, parent_id=False,
    #                  subtype_xmlid=None, subtype_id=False, partner_ids=None,
    #                  attachments=None, attachment_ids=None,
    #                  **kwargs):
    #     """ Post a new message in an existing thread, returning the new mail.message.
    #
    #     :param str body: body of the message, usually raw HTML that will
    #         be sanitized
    #     :param str subject: subject of the message
    #     :param str message_type: see mail_message.message_type field. Can be anything but
    #         user_notification, reserved for message_notify
    #     :param str email_from: from address of the author. See ``_message_compute_author``
    #         that uses it to make email_from / author_id coherent;
    #     :param int author_id: optional ID of partner record being the author. See
    #         ``_message_compute_author`` that uses it to make email_from / author_id coherent;
    #     :param int parent_id: handle thread formation
    #     :param int subtype_id: subtype_id of the message, used mainly for followers
    #         notification mechanism;
    #     :param list(int) partner_ids: partner_ids to notify in addition to partners
    #         computed based on subtype / followers matching;
    #     :param list(tuple(str,str), tuple(str,str, dict)) attachments : list of attachment
    #         tuples in the form ``(name,content)`` or ``(name,content, info)`` where content
    #         is NOT base64 encoded;
    #     :param list attachment_ids: list of existing attachments to link to this message
    #         -Should only be set by chatter
    #         -Attachment object attached to mail.compose.message(0) will be attached
    #             to the related document.
    #
    #     Extra keyword arguments will be used either
    #       * as default column values for the new mail.message record if they match
    #         mail.message fields;
    #       * propagated to notification methods;
    #
    #     :return record: newly create mail.message
    #     """
    #     self.ensure_one()  # should always be posted on a record, use message_notify if no record
    #     # split message additional values from notify additional values
    #     msg_kwargs = dict((key, val) for key, val in kwargs.items() if key in self.env['mail.message']._fields)
    #     notif_kwargs = dict((key, val) for key, val in kwargs.items() if key not in msg_kwargs)
    #
    #     # preliminary value safety check
    #     partner_ids = set(partner_ids or [])
    #     if self._name == 'mail.thread' or not self.id or message_type == 'user_notification':
    #         raise ValueError(
    #             _('Posting a message should be done on a business document. Use message_notify to send a notification to an user.'))
    #     if 'channel_ids' in kwargs:
    #         raise ValueError(
    #             _("Posting a message with channels as listeners is not supported since Odoo 14.3+. Please update code accordingly."))
    #     if 'model' in msg_kwargs or 'res_id' in msg_kwargs:
    #         raise ValueError(
    #             _("message_post does not support model and res_id parameters anymore. Please call message_post on record."))
    #     if 'subtype' in kwargs:
    #         raise ValueError(
    #             _("message_post does not support subtype parameter anymore. Please give a valid subtype_id or subtype_xmlid value instead."))
    #     if any(not isinstance(pc_id, int) for pc_id in partner_ids):
    #         raise ValueError(_('message_post partner_ids and must be integer list, not commands.'))
    #
    #     self = self._fallback_lang()  # add lang to context immediately since it will be useful in various flows latter.
    #
    #     # Find the message's author
    #     guest = self.env['mail.guest']._get_guest_from_context()
    #     if self.env.user._is_public() and guest:
    #         author_guest_id = guest.id
    #         author_id, email_from = False, False
    #     else:
    #         author_guest_id = False
    #         author_id, email_from = self._message_compute_author(author_id, email_from, raise_on_email=True)
    #
    #     if subtype_xmlid:
    #         subtype_id = self.env['ir.model.data']._xmlid_to_res_id(subtype_xmlid)
    #     if not subtype_id:
    #         subtype_id = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note')
    #
    #     # automatically subscribe recipients if asked to
    #     if self._context.get('mail_post_autofollow') and partner_ids:
    #         self.message_subscribe(partner_ids=list(partner_ids))
    #
    #     msg_values = dict(msg_kwargs)
    #     if 'email_add_signature' not in msg_values:
    #         msg_values['email_add_signature'] = True
    #     if not msg_values.get('record_name'):
    #         # use sudo as record access is not always granted (notably when replying
    #         # a notification) -> final check is done at message creation level
    #         msg_values['record_name'] = self.sudo().display_name
    #     new_mails = msg_values.update({
    #         'author_id': author_id,
    #         'author_guest_id': author_guest_id,
    #         'email_from': email_from,
    #         'model': self._name,
    #         'res_id': self.id,
    #         # content
    #         'body': body,
    #         'subject': subject or False,
    #         'message_type': message_type,
    #         'parent_id': self._message_compute_parent_id(parent_id),
    #         'subtype_id': subtype_id,
    #         # recipients
    #         'partner_ids': {self.env.user.sudo().partner_id.id, self.env.user.sudo().partner_id.id},
    #     })
    #     msg_values.update({
    #         'author_id': author_id,
    #         'author_guest_id': author_guest_id,
    #         'email_from': email_from,
    #         'model': self._name,
    #         'res_id': self.id,
    #         # content
    #         'body': body,
    #         'subject': subject or False,
    #         'message_type': message_type,
    #         'parent_id': self._message_compute_parent_id(parent_id),
    #         'subtype_id': subtype_id,
    #         # recipients
    #         'partner_ids': partner_ids,
    #     })
    #
    #     attachments = attachments or []
    #     attachment_ids = attachment_ids or []
    #     attachement_values = self._message_post_process_attachments(attachments, attachment_ids, msg_values)
    #     msg_values.update(attachement_values)  # attachement_ids, [body]
    #
    #     new_message = self._message_create(new_mails)
    #     new_message = self._message_create(msg_values)
    #
    #     # Set main attachment field if necessary. Call as sudo as people may post
    #     # without read access on the document, notably when replying on a
    #     # notification, which makes attachments check crash.
    #     self.sudo()._message_set_main_attachment_id(msg_values['attachment_ids'])
    #
    #     if msg_values['author_id'] and msg_values['message_type'] != 'notification' and not self._context.get(
    #             'mail_create_nosubscribe'):
    #         if self.env['res.partner'].browse(
    #                 msg_values['author_id']).active:  # we dont want to add odoobot/inactive as a follower
    #             self._message_subscribe(partner_ids=[msg_values['author_id']])
    #
    #     self._message_post_after_hook(new_message, msg_values)
    #     self._notify_thread(new_message, msg_values, **notif_kwargs)
    #     print(' new_message  ===>  ', new_message)
    #     return new_message

    def _notify_get_reply_to_formatted_email(self, record_email, record_name):
        company = self.env["res.company"].get_active_company()
        # name = " ".join((" ".join(company_name), record_name)).rstrip()
        name = self.env.user.name
        return tools.formataddr(
            (f"{name} {'|'} {company.name}", record_email)
        )

class MailMessage(models.Model):
    _inherit = "mail.message"

    @api.model
    def _prepare_default_email_from(self, user, email_from):
        if user == self.env.user:
            company = self.env["res.company"].get_active_company()
        else:
            company = user.company_id
        user_name = user.name
        return tools.formataddr(
            (f"{user_name} {'|'} {company.name}", email_from)
        )

    @api.model_create_multi
    def create(self, vals_list):
        # Proceed only if Author is an internal user
        if self._context.get("email_from_skip_create"):
            return super(MailMessage, self).create(vals_list)
        res_users_obj = self.env["res.users"]
        for vals in filter(lambda v: v.get("author_id"), vals_list):
            user = res_users_obj.search(
                [("partner_id", "=", vals.get("author_id"))], limit=1
            )
            if user and user.has_group("base.group_user"):
                email_from = vals.get("email_from", False)
                vals.update(
                    email_from=self._prepare_default_email_from(user, email_from)
                )
        return super(MailMessage, self).create(vals_list)


