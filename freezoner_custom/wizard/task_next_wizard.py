
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class TaskNextWizard(models.TransientModel):
    _name = 'task.next.wizard'

    comment = fields.Text(string="Comment")
    task_id = fields.Many2one("project.task",string="Task")

    def submit(self):
        for rec in self:
            task = rec.task_id
            if task:
                # Fetching the old and new stages
                old_stage_name = task.stage_id.name
                task.next_stage()
                new_stage_name = task.stage_id.name

                # Constructing the message body
                task_link = f'<a href="#id={task.id}&model=project.task">{task.name}</a>'
                message_body = (
                    f"Stage changed for task {task_link}<br>"
                    f"<b>{old_stage_name} > {new_stage_name}</b> (Stage)<br>"
                    f"Comment:<br>{rec.comment or 'No comment provided.'}"
                )

                # Notify only the current user
                task.project_id._message_log(
                    body=message_body,
                    subject=_('Task Stage Changed'), message_type='comment',
                )



