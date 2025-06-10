# -*- coding: utf-8 -*-

import ast
import base64
import re

from odoo import _, api, fields, models, tools, Command
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import email_re

class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    task_id = fields.Many2one('project.task')

    # def action_send_mail(self):
    #     """ Used for action button that do not accept arguments. """
    #     self._action_send_mail(auto_commit=False)
    #     self.task_id.is_sent = True
    #     return {'type': 'ir.actions.act_window_close'}

class ProjectStageUpdate(models.Model):
    _inherit = 'project.task.type'

    closing = fields.Boolean(default=False)


class ProjectTaskUpdate(models.Model):
    _inherit = 'project.task'

    closing = fields.Boolean(related='stage_id.closing')
    is_sent = fields.Boolean("Is Sent")

    def update_client(self):
        """ Opens a wizard to compose an email, with relevant mail template loaded by default """
        self.ensure_one()
        mail_template = self.env.ref('task_update.client_task_update_mail')
        print(mail_template)
        ctx = {
            'default_model': 'project.task',
            'default_res_id': self.id,
            'default_use_template': bool(mail_template),
            'default_template_id': mail_template.id if mail_template else None,
            'default_composition_mode': 'comment',
            'force_email': True,
            'default_task_id': self.id,
            # 'model_description': self.with_context(lang=self.partner_id),
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }
