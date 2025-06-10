# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime
import pytz
import math


def get_late_amount(actual_attend, day_start):
    return actual_attend - day_start


def custom_hours_new_working_hours(day_start, leave, start_period):
    # TODO:if Mid day Leave
    if day_start == float(leave.request_hour_from):
        day_start = day_start + float(leave.number_of_hours_display)
    return day_start


def concat_work_periods(period_list):
    start = float('inf')
    end = 0.0
    start_period = None
    for period in period_list:
        if period.hour_from < start:
            start = period.hour_from
            start_period = period
        if period.hour_to > end:
            end = period.hour_to
    return start, end, start_period


def half_day_new_working_hours(day_start, leave, start_period, work_periods):
    # TODO:if Mid day Leave
    if start_period == 'morning' and leave.request_date_from_period == 'am':
        day_start = day_start + leave.number_of_days
    elif start_period == 'afternoon' and leave.request_date_from_period == 'pm':
        day_start = day_start + leave.number_of_days
    return day_start


def _late_reason(late_amount, employee_calendar):
    for reason in employee_calendar.late_deductions:
        late_to = reason.late_to
        if late_to == 0: late_to = float('inf')
        if reason.late_from <= late_amount <= late_to:
            return reason


class LateAttendance(models.Model):
    _inherit = 'hr.attendance'

    @api.model
    def create(self, vals_list):
        attend = super(LateAttendance, self).create(vals_list)
        today = date.today()
        employee_id = attend.employee_id
        emp_tz = pytz.timezone(self.env.user.tz)
        actual_attend_h = attend.check_in.astimezone(emp_tz).hour
        actual_attend_m = attend.check_in.astimezone(emp_tz).minute
        if len(str(actual_attend_m)) < 2:
            actual_attend_m = str(f"0{math.ceil(actual_attend_m * 1.666666666666669)}")
        elif actual_attend_m is 0:
            pass
        else:
            actual_attend_m = math.ceil(actual_attend_m * 1.666666666666669)
        actual_attend = float(f"{actual_attend_h}.{actual_attend_m}")
        emp_leaves_toady = self.env['hr.leave'].search(
            [('employee_id', '=', employee_id.id), ('date_from', '<=', today), ('date_to', '>=', today),
             ('state', 'in', ('validate', 'validate1'))])
        employee_calendar = employee_id.contract_id.resource_calendar_id
        work_periods = employee_calendar.attendance_ids.search(
            [('calendar_id', '=', employee_calendar.id), ('dayofweek', '=', today.weekday())])
        if not employee_id.sudo().regular_check_in:
            if work_periods and employee_id.current_leave_state not in ('validate', 'validate1'):
                if employee_id.current_leave_state == 'confirm':
                    draft_leave = self.env['hr.leave'].search(
                        [('holiday_status_id', '=', employee_id.current_leave_id.id), ('state', '=', 'confirm'),
                         ('employee_id', '=', employee_id.id), ('date_from', '<=', fields.Datetime.now()),
                         ('date_to', '>=', fields.Datetime.now())], limit=1)
                    day_start, day_end, start_period = concat_work_periods(work_periods)
                    if emp_leaves_toady:
                        for leave in emp_leaves_toady:
                            if leave.request_unit_half:
                                day_start = half_day_new_working_hours(day_start, leave, start_period, work_periods)
                            elif leave.request_unit_hours:
                                day_start = custom_hours_new_working_hours(day_start, leave, start_period)
                    day_start += (employee_calendar.late_allowance or 0)
                    if actual_attend > day_start:
                        late_amount = get_late_amount(actual_attend, day_start)
                        late_deduction_reason = _late_reason(late_amount, employee_calendar)
                        deduction_vals = {
                            'employee_id': employee_id.id,
                            'reason': late_deduction_reason.reason_id.id or False,
                            'state': 'Draft',
                            'draft_leave': draft_leave.id,
                            'rate': late_deduction_reason.reason_id.rate,
                            'deduction_date': date.today(),
                        }

                        deduction = self.sudo().env['hr.deductions'].create(deduction_vals)

                else:
                    day_start, day_end, start_period = concat_work_periods(work_periods)
                    if emp_leaves_toady:
                        for leave in emp_leaves_toady:
                            if leave.request_unit_half:
                                day_start = half_day_new_working_hours(day_start, leave, start_period, work_periods)
                            elif leave.request_unit_hours:
                                day_start = custom_hours_new_working_hours(day_start, leave, start_period)
                    day_start += (employee_calendar.late_allowance or 0)
                    if actual_attend > day_start:
                        late_amount = get_late_amount(actual_attend, day_start)
                        late_deduction_reason = _late_reason(late_amount, employee_calendar)
                        deduction_vals = {
                            'employee_id': employee_id.id,
                            'reason': late_deduction_reason.reason_id.id or False,
                            'state': 'Confirmed',
                            'rate': late_deduction_reason.reason_id.rate,
                            'deduction_date': date.today(),
                        }

                        deduction = self.sudo().env['hr.deductions'].create(deduction_vals)

        return attend
