from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    hr_attendance_geolocation = fields.Boolean(related="company_id.hr_attendance_geolocation", string="Geolocation", readonly=False)
    hr_attendance_photo = fields.Boolean(related="company_id.hr_attendance_photo", string="Photo", readonly=False)
    