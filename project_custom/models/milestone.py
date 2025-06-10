
from odoo import api, fields, models

class ProjectMilestone(models.Model):
    _inherit = 'project.milestone'

    mail_template_id = fields.Many2one('mail.template')
