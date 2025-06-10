
from odoo import api, fields, models

class MailComposeMessages(models.TransientModel):
    _inherit = 'mail.compose.message'

    def action_send_mail(self):
        res = super(MailComposeMessages, self).action_send_mail()
        if self.model == 'crm.lead':
            record = self.env['crm.lead'].sudo().search([('id', '=', self.res_id)], limit=1)
            if record:
                record.mail_sent = True
        return res
