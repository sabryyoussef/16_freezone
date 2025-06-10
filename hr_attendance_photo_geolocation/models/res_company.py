from odoo import fields, models, api

class ResCompany(models.Model):
    _inherit = 'res.company'
    
    hr_attendance_geolocation = fields.Boolean(string="Geolocation", default=False)
    hr_attendance_photo = fields.Boolean(string="Photo", default=False)
