from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError

class SignSendRequest(models.TransientModel):
    _inherit = 'sign.send.request'

    def create_request(self):
        template_id = self.template_id.id
        if self.signers_count:
            signers = [{'partner_id': signer.partner_id.id, 'role_id': signer.role_id.id,
                        'mail_sent_order': signer.mail_sent_order} for signer in self.signer_ids]
        else:
            signers = [{'partner_id': self.signer_id.id, 'role_id': self.env.ref('sign.sign_item_role_default').id,
                        'mail_sent_order': self.signer_ids.mail_sent_order}]
        cc_partner_ids = self.cc_partner_ids.ids
        reference = self.filename
        subject = self.subject
        message = self.message
        message_cc = self.message_cc
        attachment_ids = self.attachment_ids
        refusal_allowed = self.refusal_allowed
        sign_request = self.env['sign.request'].create({
            'template_id': template_id,
            'salary_certificate_id': self.template_id.salary_certificate_id.id or False,
            'request_item_ids': [Command.create({
                'partner_id': signer['partner_id'],
                'role_id': signer['role_id'],
                'mail_sent_order': signer['mail_sent_order'],
            }) for signer in signers],
            'reference': reference,
            'subject': subject,
            'message': message,
            'message_cc': message_cc,
            'attachment_ids': [Command.set(attachment_ids.ids)],
            'refusal_allowed': refusal_allowed,
        })
        sign_request.message_subscribe(partner_ids=cc_partner_ids)
        return sign_request

class SignTemplate(models.Model):
    _inherit = 'sign.template'

    salary_certificate_id = fields.Many2one('salary.certificate.master', copy=False)


class Sign(models.Model):
    _inherit = 'sign.request'

    salary_certificate_id = fields.Many2one('salary.certificate.master', copy=False)

    def action_signed(self):
        self.state = 'signed'

    def cancel(self):
        for sign_request in self:
            sign_request.write({'access_token': self._default_access_token(), 'state': 'refused'})
        self.request_item_ids._cancel()

        # cancel activities for signers
        for user in self.request_item_ids.sudo().partner_id.user_ids.filtered(
                lambda u: u.has_group('sign.group_sign_user')):
            self.activity_unlink(['mail.mail_activity_data_todo'], user_id=user.id)

        self.env['sign.log'].sudo().create(
            [{'sign_request_id': sign_request.id, 'action': 'cancel'} for sign_request in self])
        if self.salary_certificate_id:
            print('  ddddddddddddd ', self.salary_certificate_id.id)
            self.salary_certificate_id.action_cancel()

    def write(self, values):
        res = super(Sign, self).write(values)
        if 'state' in values and values['state'] == 'signed':
            self.salary_certificate_id.sudo().action_approve()
        return res
