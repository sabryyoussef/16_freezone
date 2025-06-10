
from odoo import api, fields, models

class Project(models.Model):
    _inherit = 'project.project'

    is_approval_request = fields.Boolean()
