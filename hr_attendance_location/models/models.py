from math import radians, sin, cos, sqrt, atan2
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
from datetime import datetime, time, timedelta
import pytz
from collections import defaultdict
from datetime import datetime, timedelta
from operator import itemgetter
from pytz import timezone
from odoo import models, fields, api, exceptions, _
from odoo.tools import format_datetime
from odoo.osv.expression import AND, OR
from odoo.tools.float_utils import float_is_zero
from odoo.exceptions import AccessError
from odoo.tools import format_duration

def get_google_maps_url(latitude, longitude):
    return "https://maps.google.com?q=%s,%s" % (latitude, longitude)

_logger = logging.getLogger(__name__)

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    in_latitude = fields.Float(string="Latitude", digits=(10, 7), readonly=True)
    in_longitude = fields.Float(string="Longitude", digits=(10, 7), readonly=True)
    out_latitude = fields.Float(digits=(10, 7), readonly=True)
    out_longitude = fields.Float(digits=(10, 7), readonly=True)

    @api.model
    def first_check_and_notify_late_employees(self):
        now = datetime.now() + timedelta(2)
        check_time = time(8, 20)  # 8:20 AM
        check_datetime = datetime.combine(now.date(), check_time)
        if now >= check_datetime:
            employees_to_notify = self.env['hr.employee'].search([])  # Get all employees
            late_employees = []

            for employee in employees_to_notify:
                last_attendance = self.search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '>=', datetime.combine(now.date(), time(0, 0))),
                    ('check_in', '<=', check_datetime)
                ], limit=1, order='check_in desc')

                if not last_attendance:
                    late_employees.append(employee)
            # template = self.env.ref('hr_attendance_location.first_email_template_employee_late_checkin')
            # for employee in late_employees:
            #     template.send_mail(employee.id, force_send=True)
        return True

    @api.model
    def second_check_and_notify_late_employees(self):
        now = datetime.now() + timedelta(2)
        check_time = time(9, 20)  # 9:00 AM
        check_datetime = datetime.combine(now.date(), check_time)
        if now >= check_datetime:
            employees_to_notify = self.env['hr.employee'].search([])  # Get all employees
            late_employees = []

            for employee in employees_to_notify:
                last_attendance = self.search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '>=', datetime.combine(now.date(), time(0, 0))),
                    ('check_in', '<=', check_datetime)
                ], limit=1, order='check_in desc')

                if not last_attendance:
                    late_employees.append(employee)
            # template = self.env.ref('hr_attendance_location.second_email_template_employee_late_checkin')
            # for employee in late_employees:
            #     template.send_mail(employee.id, force_send=True)
        return True


    def action_in_attendance_maps(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': get_google_maps_url(self.in_latitude, self.in_longitude),
            'target': 'new'
        }

    def action_out_attendance_maps(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': get_google_maps_url(self.out_latitude, self.out_longitude),
            'target': 'new'
        }

    @api.model
    def create(self, values):
        attendance = super(HrAttendance, self).create(values)
        attendance._check_company_range()
        return attendance

    def write(self, values):
        res = super(HrAttendance, self).write(values)
        self._check_company_range()
        return res

    def _compute_distance(self, lat1, lon1, lat2, lon2):
        # Radius of the earth in kilometers
        R = 6371.0

        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # Calculate the change in coordinates
        dlon = lon2 - lon1
        dlat = lat2 - lat1

        # Apply Haversine formula
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = R * c

        return distance

    def _check_company_range(self):
        company = self.env.company
        company_latitude = company.company_latitude or 0.000000
        company_longitude = company.company_longitude or 0.0000000
        allowed_distance_meters = company.allowed_distance or 1100  # Default allowed distance is 1100 meters

        _logger.info(f'company Latitude: {company_latitude}, company Longitude: {company_longitude}, Allowed Distance: {allowed_distance_meters} meters')

        for attendance in self:
            # if not (attendance.in_latitude and attendance.in_longitude):
            #     raise UserError(_("Oops! It seems we're missing your location information. Could you please allow us to access your location so we can proceed?"))

            # Compute the distance between company and attendance location
            distance_meters = self._compute_distance(
                company_latitude, company_longitude,
                attendance.in_latitude, attendance.in_longitude
            ) * 1000  # Convert kilometers to meters

            if distance_meters > allowed_distance_meters:
                raise UserError(_(
                    "You are outside the allowed range of the company location. "
                    "Please ensure that you are within the company Location. "
                    "The distance exceeds the allowed distance."
                ))
