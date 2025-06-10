from odoo import api, models, _

class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def attendance_manual(self, next_action, entered_pin=None, location=False, geofence_ids=False):
        context = dict(self.env.context, attendance_geolocation=location, attendance_geofence=geofence_ids)
        res = super(HrEmployee, self.with_context(**context)).attendance_manual(next_action, entered_pin)
        return res

    def _attendance_action_change(self):
        res = super()._attendance_action_change()
        geolocation = self.env.context.get('attendance_geolocation', False)
        geofence = self.env.context.get('attendance_geofence', False)
        if geolocation:            
            if self.attendance_state == 'checked_in':
                vals = {
                    'check_in_latitude': geolocation[0],
                    'check_in_longitude': geolocation[1],
                }
                res.write(vals)
            else:
                vals = {
                    'check_out_latitude': geolocation[0],
                    'check_out_longitude': geolocation[1],
                }
                res.write(vals)
        if geofence:
            if self.attendance_state == 'checked_in':
                vals = {
                    'check_in_geofence_ids': geofence,
                }
                res.write(vals)
            else:
                vals = {
                    'check_out_geofence_ids': geofence,
                }
                res.write(vals)
        return res