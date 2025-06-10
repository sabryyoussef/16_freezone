
from odoo import api, fields, models
from odoo.exceptions import ValidationError,UserError
import ast
import json
from pytz import UTC
from collections import defaultdict
from datetime import timedelta, datetime, time
from random import randint

from odoo import api, Command, fields, models, tools, SUPERUSER_ID, _, _lt
from odoo.addons.rating.models import rating_data
from odoo.addons.web_editor.controllers.main import handle_history_divergence
from odoo.exceptions import UserError, ValidationError, AccessError


PAYMENT_STATE_SELECTION = [
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('reversed', 'Reversed'),
        ('invoicing_legacy', 'Invoicing App Legacy'),
]

class Task(models.Model):
    _inherit = 'project.task'

    is_done = fields.Boolean(related='stage_id.is_done')
    is_subtask = fields.Boolean(copy=False)

    @api.model
    def _task_message_auto_subscribe_notify(self, users_per_task):
        # Utility method to send assignation notification upon writing/creation.
        template_id = self.env['ir.model.data']._xmlid_to_res_id('project.project_message_user_assigned',
                                                                 raise_if_not_found=False)
        if not template_id:
            return
        task_model_description = self.env['ir.model']._get(self._name).display_name
        for task, users in users_per_task.items():
            if not users:
                continue
            values = {
                'object': task,
                'model_description': task_model_description,
                'access_link': task._notify_get_action_link('view'),
            }
            for user in users:
                values.update(assignee_name=user.sudo().name)
                if task.is_subtask == False:
                    assignation_msg = self.env['ir.qweb']._render('project.project_message_user_assigned', values,
                                                                  minimal_qcontext=True)
                    assignation_msg = self.env['mail.render.mixin']._replace_local_links(assignation_msg)
                    task.message_notify(
                        subject=_('You have been assigned to %s', task.display_name),
                        body=assignation_msg,
                        partner_ids=user.partner_id.ids,
                        record_name=task.display_name,
                        email_layout_xmlid='mail.mail_notification_layout',
                        model_description=task_model_description,
                        mail_auto_delete=False,
                    )

    def action_done(self):
        for rec in self:
            rec.stage_id = 28
            if rec.child_ids:
                rec.child_ids.action_done()

    def _get_default_stage_id(self):
        """ Gives default stage_id """
        project_id = self.env.context.get('default_project_id')
        if not project_id:
            return False
        return self.stage_find(project_id, [('fold', '=', False)])

    today_date = fields.Datetime(compute='get_today_date')
    document_ids = fields.Many2many('res.partner.document', compute='get_document_ids')
    task_document_ids = fields.One2many('res.partner.document','task_id')
    document_count = fields.Integer(compute='get_document_count', strint='View Documents')
    payment_state = fields.Selection(selection=PAYMENT_STATE_SELECTION, string='Payment Status',
                                     related='invoice_id.payment_state')
    invoice_id = fields.Many2one('account.move', compute='get_invoice_id')
    document_type_ids = fields.One2many('task.document.lines', 'task_id')
    document_required_type_ids = fields.One2many('task.document.required.lines', 'task_id')
    document_required_readonly_type_ids = fields.One2many('task.document.required.lines', 'task_id',
                                                          compute='get_document_required_readonly_type_ids')
    document_required_type_processing_ids = fields.One2many('task.document.required.lines', 'task_id')
    stage_id = fields.Many2one('project.task.type', string='Stage', compute='_compute_stage_id',
                               store=True, readonly=True, ondelete='restrict', tracking=True, index=True,
                               default=_get_default_stage_id, group_expand='_read_group_stage_ids',
                               domain="[('project_ids', '=', project_id)]", copy=False,
                               task_dependency_tracking=True)

    @api.depends('project_id','child_ids.stage_id','stage_id')
    def _compute_stage_id(self):
        for task in self:
            if task.project_id:
                if task.project_id not in task.stage_id.project_ids:
                    task.stage_id = task.stage_find(task.project_id.id, [('fold', '=', False)])
                    print(' childdddddddddddd ', task.child_ids)
                if task.child_ids:
                    if any(task1.stage_id.name == 'In Progress' for task1 in task.child_ids):
                        task.stage_id = 65
                    elif all(task2.stage_id.name == 'Done' for task2 in task.child_ids):
                        task.stage_id = 28
                    elif all(task2.stage_id.name == 'New' for task2 in task.child_ids):
                        task.stage_id = 243
            else:
                task.stage_id = False

    def next_stage(self):
        for rec in self:
            current_stage = rec.stage_id
            stages = self.env['project.task.type'].sudo().search([('project_ids', '=', rec.project_id.id)])
            if current_stage.fold:
                raise ValidationError(_('Stage is folded!'))
            # Find the next stage with a sequence greater than the current stage
            next_stage = stages.sorted(key=lambda s: s.sequence).filtered(lambda s: s.sequence > current_stage.sequence)
            if next_stage:
                # Get the first stage if there are multiple stages
                rec.write({'stage_id': next_stage[0].id})
            else:
                raise ValidationError(_('There is no next stage based on sequence!'))

    def previous_stage(self):
        for rec in self:
            current_stage = rec.stage_id
            stages = self.env['project.task.type'].sudo().search([('project_ids', '=', rec.project_id.id)])
            if current_stage.sequence == 1:
                raise ValidationError(_('Stage is first!'))
            # Find the next stage with a sequence greater than the current stage
            previous_stage = stages.sorted(key=lambda s: s.sequence).filtered(lambda s: s.sequence < current_stage.sequence)
            if previous_stage:
                # Get the first stage if there are multiple stages
                rec.write({'stage_id': previous_stage[0].id})
            else:
                raise ValidationError(_('There is no previous stage based on sequence!'))

    def add_partners_to_lines(self):
        tasks = self.env['project.task'].sudo().search([])
        for rec in tasks:
            if rec.document_required_type_ids:
                for line in rec.document_required_type_ids:
                    line.partner_id = rec.partner_id.id

    def action_assignees(self):
        return {
            'name': _('Assignees Users'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'project.task.assignees',
            'context': {'default_task_id': self.id},
            'view_id': self.env.ref('freezoner_custom.project_task_assignees_form_view').id,
            'target': 'new',
        }

    def action_view_project(self):
        self.ensure_one()
        if not self.project_id:
            return False
        return {
            'name': self.project_id.name,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'project.project',
            'res_id': self.project_id.id,
            'target': 'current',  # Opens in the same tab
            'view_id': self.env.ref('project.edit_project').id,
        }

    def fitch_all_documents(self):
        for rec in self:
            all_related_tasks = self.env['project.task'].sudo().search([
                ('partner_id', '=', rec.partner_id.id),
            ])
            documents_map = {}
            documents = self.env['res.partner.document'].sudo().search([('partner_id', '=', rec.partner_id.id)])
            for doc in documents:
                documents_map[doc.type_id.id] = {
                    'attachment_ids': [(6, 0, doc.attachment_ids.ids)],
                    'issue_date': doc.issue_date,
                    'expiration_date': doc.expiration_date,
                }
            for task in all_related_tasks:
                for line in task.document_required_type_ids:
                    doc_info = documents_map.get(line.document_id.id)
                    if doc_info:
                        line.write(doc_info)
                for line2 in task.document_type_ids:
                    doc_info2 = documents_map.get(line2.document_id.id)
                    if doc_info2:
                        line2.write(doc_info2)

    def get_document_count(self):
        for rec in self:
            documents = self.env['res.partner.document'].sudo().search([('project_id', '=', rec.project_id.id)])
            documents += self.env['res.partner.document'].sudo().search([('task_ids', 'in', rec.id)])
            for l in self.document_required_type_ids:
                documents += self.env['res.partner.document'].sudo().search(
                    [('partner_id', '=', self.partner_id.id), ('type_id', '=', l.document_id.id),
                     ('issue_date', '=', l.issue_date)])
            for ll in self.document_type_ids:
                documents += self.env['res.partner.document'].sudo().search(
                    [('partner_id', '=', self.partner_id.id), ('type_id', '=', ll.document_id.id),
                     ('issue_date', '=', ll.issue_date)])
            rec.document_count = len(documents)

    @api.depends('partner_id')
    def get_document_ids(self):
        for rec in self:
            rec.document_ids = self.env['res.partner.document'].sudo().search(
                [('partner_id', '=', rec.partner_id.id)]).ids

    def action_view_document(self):
        """ Smart button to run action """
        documents = self.env['res.partner.document'].sudo().search([('project_id','=',self.project_id.id)])
        documents += self.env['res.partner.document'].sudo().search([('task_ids','in',self.id)])
        for l in self.document_required_type_ids:
            documents += self.env['res.partner.document'].sudo().search([('partner_id','=', self.partner_id.id),('type_id','=', l.document_id.id),('issue_date','=', l.issue_date)])
        for ll in self.document_type_ids:
            documents += self.env['res.partner.document'].sudo().search([('partner_id','=', self.partner_id.id),('type_id','=', ll.document_id.id),('issue_date','=', ll.issue_date)])
        recs = documents
        action = self.env.ref('client_documents.contacts_documents_action').read()[0]
        if len(recs) > 1:
            action['domain'] = [('id', 'in', recs.ids)]
        elif len(recs) == 1:
            action['views'] = [(
                self.env.ref('client_documents.client_documents_form_views').id, 'form'
            )]
            action['res_id'] = recs.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def get_today_date(self):
        self.today_date = fields.Datetime.now()

    def open_mail(self):
        return {
            'res_model': 'mail.compose.message',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            # 'context': {'default_crm_id': rec.id},
            'view_id': self.env.ref("mail.email_compose_message_wizard_form").id,
            'target': 'new'
        }

    @api.depends('sale_order_id')
    def get_invoice_id(self):
        for rec in self:
            if rec.sale_order_id:
                inv1 = self.env['account.move'].sudo().search(
                    [('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),
                     ('sale_id', '=', rec.sale_order_id.id)], limit=1).id
                inv2 = self.env['account.move'].sudo().search(
                    [('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),
                     ('invoice_origin', '=', rec.sale_order_id.name)], limit=1).id
                rec.invoice_id = inv1 or inv2 or False
            else:
                rec.invoice_id = False

    # def write(self, vals):
    #     res = super(Task, self).write(vals)
    #     for rec in self:
    #         if rec.id > 1000:
    #             if self.project_id.project_exception_id.state != 'approved' and self.project_id.state != 'a_template':
    #                 if rec.today_date.date() != rec.create_date.date():
    #                     if not rec.invoice_id:
    #                         raise ValidationError(_(' Invoice not paid'))
    #                     if rec.payment_state == 'not_paid':
    #                         raise ValidationError(_(' Invoice not paid'))
    #                 if rec.today_date.date() == rec.create_date.date() and (rec.today_date.minute - rec.create_date.minute) > 1:
    #                     if not rec.invoice_id:
    #                         raise ValidationError(_(' Invoice not paid'))
    #                     if rec.payment_state == 'not_paid':
    #                         raise ValidationError(_(' Invoice not paid'))
    #     return res


    def get_document_required_readonly_type_ids(self):
        for rec in self:
            task = rec.project_id.task_ids.filtered(lambda t: t.name == 'Collecting Required Documents')
            if task:
                rec.document_required_readonly_type_ids = task.document_required_type_ids
            else:
                rec.document_required_readonly_type_ids = False

    def move_stage(self):
        for rec in self:
            return {
                'res_model': 'task.wizard',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
                'context': {'default_task_id': rec.id,'default_project_id': rec.project_id.id,'default_current_id': rec.stage_id.id},
                'view_id': self.env.ref("freezoner_custom.task_wizard_form_view").id,
                'target': 'new'
            }

    def action_view_task(self):
        recs = self.mapped('id')
        action = self.env.ref('project.action_view_all_task').read()[0]
        if len(recs) > 1:
            action['domain'] = [('id', 'in', recs)]
        elif len(recs) == 1:
            action['views'] = [(self.env.ref('project.view_task_form2').id, 'form')]
            action['res_id'] = recs[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def action_next_stage(self):
        for rec in self:
            return {
                'res_model': 'task.next.wizard',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
                'context': {'default_task_id': rec.id},
                'view_id': self.env.ref("freezoner_custom.task_next_wizard_form_view").id,
                'target': 'new'
            }

    def create_documents(self):
        for rec in self:
            if rec.name in ['Documents To Be Collected','Collecting Required Documents','Upload Corporate Documents And Rename All Files','Uploading Deliverables']:
                for line in rec.document_required_type_ids:
                    line._message_log(
                        body=" ( " + str(line.document_id.name) + ' By : ' + str(rec.write_uid.name),
                        subject=_('Document'), message_type='comment',
                    )
                    email_values = {
                        'subject': 'Document Created',
                        'body_html': (
                            f'<strong> Document Created </strong> <br/>'
                            f'<p> {line.document_id.name}</p>'
                        ),
                        'email_from': rec.company_id.email,
                        'email_to': rec.message_partner_ids.mapped('email'),
                    }
                    mail = self.env['mail.mail'].create(email_values)
                    mail.send()
            for line in rec.document_type_ids:
                if line.is_moved == False and line.issue_date:
                    documents = self.env['res.partner.document'].sudo().search(
                        [('partner_id', '=', self.partner_id.id), ('issue_date', '=', line.issue_date),
                         ('type_id', '=', line.document_id.id)], limit=1)
                    if not documents:
                        list_attachment = []
                        for att in line.attachment_ids:
                            list_attachment.append(att.id)
                        vals = {
                            'name': str(line.name),
                            'task_id': line.task_id.id,
                            'type_id': line.document_id.id,
                            'partner_id': rec.partner_id.id,
                            'issue_date': line.issue_date or False,
                            'expiration_date': line.expiration_date or False,
                            'attachment_ids': list_attachment,
                        }
                        self.sudo().env['res.partner.document'].sudo().create(vals)
                        line.is_moved = True
            for line in rec.document_required_type_ids:
                if line.is_moved == False and line.issue_date and line.is_ready == True:
                    documents = self.env['res.partner.document'].sudo().search(
                        [('partner_id', '=', self.partner_id.id), ('issue_date', '=', line.issue_date),
                         ('type_id', '=', line.document_id.id)], limit=1)
                    if not documents:
                        list_attachment = []
                        for att in line.attachment_ids:
                            list_attachment.append(att.id)
                        vals = {
                            'name': line.name,
                            'task_id': line.task_id.id,
                            'type_id': line.document_id.id,
                            'partner_id': rec.partner_id.id,
                            'issue_date': line.issue_date or False,
                            'expiration_date': line.expiration_date or False,
                            'attachment_ids': list_attachment,
                        }
                        self.sudo().env['res.partner.document'].sudo().create(vals)
                        line.is_moved = True
                    self.stage_id = 65

class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    def _get_default_project_ids(self):
        return self.env['project.project'].search([('active','=',True)]).ids

    project_ids = fields.Many2many('project.project', 'project_task_type_rel', 'type_id', 'project_id',
                                   string='Projects',
                                   default=lambda self: self._get_default_project_ids(),
                                   compute='get_project_ids',store=True,
                                   help="Projects in which this stage is present. If you follow a similar workflow in several projects,"
                                        " you can share this stage among them and get consolidated information this way.")

    def get_project_ids(self):
        self.project_ids = self.env['project.project'].search([('active','=',True)]).ids