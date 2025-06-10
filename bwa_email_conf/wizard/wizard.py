
import ast
import base64
import re

from odoo import _, api, fields, models, tools, Command
from odoo.exceptions import UserError
from odoo.osv import expression

class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def _partner_ids_domain(self):
        return expression.OR([
            [('type', '!=', 'private')],
            [('id', 'in', self.env.context.get('default_partner_custom_ids', []))],
        ])

    partner_custom_ids = fields.Many2many(
        'res.partner', 'mail_compose_message_res_partner_rel2',
        'wizard_id2', 'partner_id2', 'Additional Contacts',
        domain=_partner_ids_domain)


    partner_ids = fields.Many2many(
        'res.partner', 'mail_compose_message_res_partner_rel',
        'wizard_id', 'partner_id', 'Additional Contacts',
        compute='get_all_partner_ids')


    @api.depends('partner_custom_ids')
    def get_all_partner_ids(self):
        for rec in self:
            lst = []
            if rec.partner_custom_ids:
                lst.append(self.env.user.partner_id.id)
                for partner in rec.partner_custom_ids:
                    lst.append(partner.id)
            rec.partner_ids = lst

    def _process_recipient_values(self, mail_values_dict):
        # Preprocess res.partners to batch-fetch from db if recipient_ids is present
        # it means they are partners (the only object to fill get_default_recipient this way)
        recipient_pids = [
            recipient_command[1]
            for mail_values in mail_values_dict.values()
            # recipient_ids is a list of x2m command tuples at this point
            for recipient_command in mail_values.get('recipient_ids') or []
            if recipient_command[1]
        ]
        recipient_emails = {
            p.id: p.email
            for p in self.env['res.partner'].browse(set(recipient_pids))
        } if recipient_pids else {}
        recipients_info = {}
        for record_id, mail_values in mail_values_dict.items():
            # add email from email_to; if unrecognized email in email_to keep
            # it as used for further processing
            mail_to = tools.email_split_and_format(mail_values.get('email_to'))
            if not mail_to and mail_values.get('email_to'):
                mail_to.append(mail_values['email_to'])
            # add email from recipients (res.partner)
            mail_to += [
                recipient_emails[recipient_command[1]]
                for recipient_command in mail_values.get('recipient_ids') or []
                if recipient_command[1]
            ]
            # uniquify, keep ordering
            seen = set()
            mail_to = [email for email in mail_to if email not in seen and not seen.add(email)]
            mail_to.append(self.env.user.email)
            recipients_info[record_id] = {
                'mail_to': mail_to,
                'mail_to_normalized': [
                    tools.email_normalize(mail, strict=False)
                    for mail in mail_to
                    if tools.email_normalize(mail, strict=False)
                ]
            }
        return recipients_info




