
from odoo import api, fields, models

class Task(models.Model):
    _inherit = 'project.task'

    is_sent = fields.Boolean()
    is_done = fields.Boolean(related='stage_id.is_done')

    @api.model
    def get_email_to(self):
        who_to_notify = [self.partner_id.email]
        return who_to_notify

    def send_mail_rating(self):
        self.partner_id.survey_task_id = self.id
        template_id = self.env.ref('bwa_survey.rating_project_custom_template')
        self.env['mail.template'].browse(template_id.id).send_mail(self.id, force_send=True)
        self.env.cr.execute("UPDATE project_task set is_sent = '%s' WHERE id=%s" % (
            True, self.id))
