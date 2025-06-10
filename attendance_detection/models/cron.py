# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime
import pytz
from odoo.exceptions import ValidationError


class HrDeductionsCron(models.Model):
    _inherit = 'hr.deductions'

    def _is_on_leave(self, employee):
        is_on_leave = False
        leaves = self.env['hr.leave'].search(
            [('employee_id', '=', employee.id), ('request_date_from', '<=', date.today()),
             ('request_date_to', '>=', date.today()),
             ('state', '=', 'validate')])
        if leaves:
            is_on_leave = True
        return is_on_leave

    def working_day(self, employee):
        employee_calendar = employee.contract_id.resource_calendar_id
        working_day = employee_calendar.attendance_ids.search(
            [('calendar_id', '=', employee_calendar.id), ('dayofweek', '=', date.today().weekday())])
        if len(working_day) > 0:
            return True
        return False

    def _did_attend(self, employee):
        attended = False
        today_beg = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        attendance = self.env['hr.attendance'].search_count(
            [('employee_id', '=', employee.id), ('check_in', '>', today_beg)])
        working_day = self.working_day(employee)
        if attendance > 0 or not working_day:
            attended = True
        return attended

    def _absence_check(self):
        # TODO: Check Non Working Days
        for employee in self.env['hr.employee'].search([]):
            no_show_reason = self.env.ref('attendance_payroll_deductions.no_show_deduction_reason')
            if (not employee.regular_check_in) and (not self._is_on_leave(employee)) and (
                    not self._did_attend(employee)):
                deduction_vals = {
                    'employee_id': employee.id,
                    'reason': no_show_reason.id,
                    'state': 'Confirmed',
                    'rate': no_show_reason.rate,
                }

                deduction = self.sudo().env['hr.deductions'].create(deduction_vals)

        for deduction in self.search([('state', '=', 'Draft')]):
            if deduction.draft_leave_status in ('validate1', 'validate'):
                deduction.cancel()
            else:
                deduction.confirm()
