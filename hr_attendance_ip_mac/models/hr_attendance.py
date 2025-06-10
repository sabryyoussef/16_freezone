
from odoo import fields, models

class HrAttendances(models.Model):
    """Inherits HR Attendance model"""
    _inherit = 'hr.attendance'

    checkin_ip_address = fields.Char(string='Check In IP Address', store=True)
    checkin_mac_address = fields.Char(string='Check In Mac Address', store=True)
    checkout_ip_address = fields.Char(string='Check Out IP Address', store=True)
    checkout_mac_address = fields.Char(string='Check Out Mac Address', store=True)

