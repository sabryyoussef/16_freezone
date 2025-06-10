from odoo import models
from odoo.http import request

class Http(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        result = super(Http, self).session_info()
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        if self.env.user.has_group('base.group_user'):
            company = self.env.company
            result['hr_attendance_geolocation'] = company.hr_attendance_geolocation
            result['hr_attendance_photo'] = company.hr_attendance_photo
            result['hr_attendance_employee_id'] = employee.id
        return result