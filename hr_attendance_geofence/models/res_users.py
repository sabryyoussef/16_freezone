from odoo import api, fields, models, modules, _

class ResUsers(models.Model):    
    _inherit = 'hr.employee'
    
    attendance_geolocation = fields.Boolean(string="Attendances Geolocation", default=False)

    #
    # @property
    # def SELF_READABLE_FIELDS(self):
    #     return super().SELF_READABLE_FIELDS + ['attendance_geolocation']
    #
    # @property
    # def SELF_WRITEABLE_FIELDS(self):
    #     return super().SELF_WRITEABLE_FIELDS + ['attendance_geolocation']
    #

class Users(models.Model):
    _inherit = 'res.users'



    @api.model
    def action_get_attendance_geofence(self):
        if self.env.user:
            return self.env['ir.actions.act_window']._for_xml_id('hr_attendance_geofence.action_simple_attendance_geolocation')
    #
    # def attendance_geolocation_reload(self):
    #     return {
    #         "type": "ir.actions.client",
    #         "tag": "reload_context"
    #     }