import werkzeug
from odoo import fields, models, api
from odoo.addons import decimal_precision as dp

GEOLOCATION = dp.get_precision("Gelocation")

class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    check_in_latitude = fields.Float("Check-in Latitude", digits=GEOLOCATION, readonly=True)
    check_in_longitude = fields.Float("Check-in Longitude", digits=GEOLOCATION, readonly=True)
    check_in_geofence_ids = fields.Many2many('hr.attendance.geofence', 'check_in_geofence_attendance_rel', 'attendance_id', 'geofence_id', string='Geofences')
    check_out_latitude = fields.Float("Check-out Latitude", digits=GEOLOCATION, readonly=True)
    check_out_longitude = fields.Float("Check-out Longitude", digits=GEOLOCATION, readonly=True)
    check_out_geofence_ids = fields.Many2many('hr.attendance.geofence', 'check_out_geofence_attendance_rel', 'attendance_id', 'geofence_id', string='Geofences')