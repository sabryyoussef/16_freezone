# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime, time


class ClientBirthday(models.Model):
    _inherit = 'res.partner'

    birthday = fields.Date()
    birth_month = fields.Integer(compute="_compute_birth_month_day", store=True)
    birth_day = fields.Integer(compute="_compute_birth_month_day", store=True)

    @api.depends('birthday')
    def _compute_birth_month_day(self):
        for rec in self:
            if rec.birthday:
                rec.birth_month = rec.birthday.month
                rec.birth_day = rec.birthday.day

    def _check_birthday(self):
        month = date.today().month
        day = date.today().day
        birthday_partners = self.search([('birth_day', '=', day), ('birth_month', '=', month)])
        for partner in birthday_partners:
            mail_template = self.env.ref('client_birthday.client_birthday_mail')
            mail_template.send_mail(partner.id, force_send=True)
