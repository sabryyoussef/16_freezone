from odoo import models
from odoo.http import request

class Http(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        user = self.env.user
        result = super(Http, self).session_info()
        if self.env.user.has_group('base.group_user'):
            result['attendance_geolocation'] = user.employee_id.attendance_geolocation
        return result