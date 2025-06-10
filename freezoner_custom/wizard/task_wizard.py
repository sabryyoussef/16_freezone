
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class TaskWizard(models.TransientModel):
    _name = 'task.wizard'

    current_id = fields.Many2one('project.task.type',string='Current Stage')
    project_id = fields.Many2one('project.project',string='Current Stage')
    stage_id = fields.Many2one('project.task.type',string='Move To Stage',
                               domain="[('project_ids', '=', project_id)]",
                                required=True)
    task_id = fields.Many2one("project.task",string="Task")

    def submit(self):
        for rec in self:
            task = rec.task_id
            stage_name = rec.stage_id.name
            if (task.name in ['Upload Corporate Documents And Rename All Files',
                              'Uploading Deliverables'] and stage_name == 'Done') or \
                    (task.name in ['Documents To Be Collected',
                                   'Collecting Required Documents'] and stage_name == 'Done'):

                for line in task.document_type_ids if task.name in ['Upload Corporate Documents And Rename All Files',
                                                                    'Uploading Deliverables'] else task.document_required_type_ids:
                    if line.is_required and not line.attachment_ids:
                        raise ValidationError(
                            f'Please Add Attachment In Required Lines In {"Deliverable" if task.name in ["Upload Corporate Documents And Rename All Files", "Uploading Deliverables"] else "Required"} Document Page')
                task.stage_id = rec.stage_id.id
            else:
                task.stage_id = rec.stage_id.id
            task.project_id.state = 'c_in_progress'
            check = True
            if stage_name == 'Done':
                if stage_name == 'Done':
                    if task.name == 'Account Opened':
                        print(' task name   ', task.name)
                        template = self.env.ref('freezoner_custom.freezoner_account_opened_mail_template')
                        self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)
                    if task.name == 'Bank Evaluation Ongoing':
                        template = self.env.ref('freezoner_custom.freezoner_bank_evaluation_ongoing_mail_template')
                        self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)
                    if task.name == 'Document Completion and Review':
                        template = self.env.ref('freezoner_custom.freezoner_document_completion_ongoing_mail_template')
                        self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)
                    if task.name == 'Bank Application Submitted':
                        template = self.env.ref('freezoner_custom.freezoner_bank_submitted_mail_template')
                        self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)
                for l in task.project_id.task_ids:
                    if l.id != task.id:
                        print('Task:', l.name, 'Stage:', l.stage_id.name)
                        if l.stage_id.name != 'Done':
                            check = False
                            break  # exit the loop as soon as an undone task is found
                if check:
                    task.project_id.state = 'd_done'


