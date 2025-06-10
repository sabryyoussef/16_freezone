# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime
import pytz
from odoo.exceptions import ValidationError


class HrDeductionsLate(models.Model):
    _inherit = 'hr.deductions'

    draft_leave = fields.Many2one(comodel_name='hr.leave', readonly=1)
    draft_leave_status = fields.Selection(
        selection=[('draft', 'To Submit'), ('cancel', 'Canceled'), ('confirm', 'To Approve'), ('refuse', 'Refused'),
                   ('validate1', 'Second Approval'), ('validate', 'Approved')], related='draft_leave.state')
