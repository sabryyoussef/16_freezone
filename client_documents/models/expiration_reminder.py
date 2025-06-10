# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime


class ExpirationReminder(models.Model):
    _inherit = 'res.partner.document'

    def check_for_expiration(self):
        documents = self.search([('expiration_reminder', '=', True), ('expiration_reminder_sent', '=', False)])
        today = datetime.datetime.now()
        thirty_days_from_today = today + datetime.timedelta(days=90)
        expired_documents = [document for document in documents if
                             document.expiration_date < thirty_days_from_today.date()]
        for document in expired_documents:
            mail_template = self.env.ref('client_documents.expired_document_reminder_mail')
            mail_template.send_mail(document.id, force_send=True)
            document.write({'expiration_reminder_sent': True})
