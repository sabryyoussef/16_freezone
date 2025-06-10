from odoo import api, models, _


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def attendance_manual(self, next_action, entered_pin=None, location=False, photo_img64=False):
        res = super(HrEmployee,
                    self.with_context(attendance_geolocation=location, attendance_photo=photo_img64)).attendance_manual(
            next_action, entered_pin=entered_pin)
        return res

    def _attendance_action_change(self):
        res = super()._attendance_action_change()
        geolocation = self.env.context.get('attendance_geolocation', False)
        photo = self.env.context.get('attendance_photo', False)

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

        if photo:
            if self.attendance_state == 'checked_in':
                res.write({
                    'check_in_photo': photo[0],
                })
            else:
                res.write({
                    'check_out_photo': photo[0],
                })

        return res
