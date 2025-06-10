from odoo import models
from odoo.http import request
from getmac import get_mac_address

class HrEmployee(models.AbstractModel):
    _inherit = 'hr.employee'

    def _get_client_ip(self):
        """Get the client IP address, accounting for proxies."""
        return request.httprequest.environ.get('HTTP_X_FORWARDED_FOR') or request.httprequest.remote_addr

    def _get_mac_address(self):
        """Try to get the MAC address — will only return server's MAC, not client's."""
        try:
            mac = get_mac_address()
            return mac if mac else False
        except Exception:
            return False

    def _attendance_action_change(self):
        attendance = super()._attendance_action_change()
        if attendance:
            ip_address = self._get_client_ip()
            mac_address = self._get_mac_address()
            vals = {}
            if self.attendance_state == 'checked_in':
                vals['checkin_ip_address'] = ip_address
                vals['checkin_mac_address'] = mac_address
            else:
                vals['checkout_ip_address'] = ip_address
                vals['checkout_mac_address'] = mac_address
            attendance.write(vals)
        return attendance
