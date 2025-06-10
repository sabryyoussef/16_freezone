
from odoo import api, fields, models

class Tasks(models.Model):
    _inherit = 'project.task'

    all_milestone_id = fields.Many2one('project.milestone','Milestone')
    checkpoint_ids = fields.One2many('project.task.checkpoint','task_id')

    def action_send_email(self):
        if self.milestone_id and self.milestone_id.mail_template_id:
            template = self.milestone_id.mail_template_id.sudo()
            # Verify task and template details
            print("Template Model:", template.model)
            try:
                template.send_mail(self.id, force_send=True, raise_exception=True)
            except Exception as e:
                # Log specific error
                print("Failed to send email:", str(e))
        else:
            print("Email template not found for milestone:", self.milestone_id)


    @api.onchange('milestone_id','all_milestone_id')
    def _milestone_id(self):
        for task in self:
            if task.all_milestone_id:
                task.milestone_id = task.all_milestone_id.id
                existing_milestone = self.env['project.milestone'].sudo().search([
                    ('project_id', '=', task.project_id.id),
                    ('name', '=', task.name)
                ], limit=1)
                if not existing_milestone:
                    task.sudo().milestone_id.project_id = task.project_id.id
                    task.sudo().milestone_id.task_ids = [task.id]



