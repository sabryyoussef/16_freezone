# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CRMAssignation(models.Model):
    _name = 'crm.lead.assign'

    lead_id = fields.Many2one(comodel_name='crm.lead', required=1)
    partner_id = fields.Many2one(related='lead_id.partner_id', required=1)
    user_id = fields.Many2one(comodel_name='res.users', required=1)

    def assign_and_notify(self):
        for rec in self:
            # Assign
            rec.lead_id.user_id = rec.user_id
            # Notify Both Client And Consultant
            mail_template = self.env.ref('crm_assignation.lead_assign_and_notify_client_mail')
            mail_template.send_mail(rec.id, force_send=True)