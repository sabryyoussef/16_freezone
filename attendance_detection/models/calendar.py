# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime
import pytz
from odoo.exceptions import ValidationError


class LateReasonsDeductions(models.Model):
    _name = 'late.deduction'

    late_from = fields.Float(required=1)
    late_to = fields.Float(required=1)
    reason_id = fields.Many2one('hr.deductions.reasons', required=1)
    calendar_id = fields.Many2one(comodel_name='resource.calendar', required=1)


class LateAllowanceCalendar(models.Model):
    _inherit = 'resource.calendar'

    late_allowance = fields.Float(string="Allowed Late in Hour")

    @api.onchange('late_allowance')
    def _onchange_late_allowance(self):
        for rec in self:
            if rec.late_allowance < 0:
                raise ValidationError("Late Allowance Cannot Be Less Than 0")

    late_deductions = fields.One2many(comodel_name='late.deduction', inverse_name='calendar_id')
