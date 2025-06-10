
from odoo import api, fields, models

class Partner(models.Model):
    _inherit = 'res.partner'

    survey_task_id = fields.Many2one('project.task')
