# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

from odoo import fields, models


class PartnerStatement(models.TransientModel):
    _name = 'partner.statement.wizard'
    _description = 'Partner Statement'

    from_date = fields.Date(string="From Date", required=True)
    to_date = fields.Date(string="To Date", required=True)
    partner_ids = fields.Many2many('res.partner', string='Partner')

    def print_pdf(self):
        partners = self.partner_ids or self.env['res.partner'].search([])
        data = {'from_date': self.from_date, 'to_date': self.to_date, 'partner_ids': partners.ids}
        return self.env.ref('partner_statement_knk.partner_statement_pdf').with_context(data).report_action(self, data=data)

    def send_pdf(self):
        template = self.env.ref('partner_statement_knk.email_template_edi_statement', False)
        partners = self.partner_ids or self.env['res.partner'].search([])
        for rec in partners:
            template.with_context(lang=rec.lang, from_date=self.from_date, to_date=self.to_date, partner_ids=partners.ids).send_mail(rec.id, force_send=True, raise_exception=True)
