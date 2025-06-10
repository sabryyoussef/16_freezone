
from odoo import api, fields, models

class Project(models.Model):
    _inherit = 'project.project'

    is_sent = fields.Boolean(copy=False)


    def send_mail_rating(self):
        for rec in self:
            for task in rec.task_ids:
                task.send_mail_rating()
            rec.is_sent = True
