
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AssigneesUsers(models.TransientModel):
    _name = 'project.task.assignees'
    _description = 'Task Assignees Wizard'

    user_ids = fields.Many2many('res.users', string="Assignees")
    task_id = fields.Many2one("project.task", string="Task")

    def submit(self):
        for task in self.mapped('task_id'):
            # Update users for the main task
            task.user_ids = self.user_ids.ids
            # Update users for all child tasks
            task.child_ids.write({'user_ids': [(6, 0, self.user_ids.ids)]})
