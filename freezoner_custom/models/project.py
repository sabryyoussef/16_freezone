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
import re

PAYMENT_STATE_SELECTION = [
    ('not_paid', 'Not Paid'),
    ('paid_visa', 'Paid Visa'),
    ('paid_bank', 'Paid Bank'),
    ('partial', 'Partially Paid'),
]


class Project(models.Model):
    _inherit = 'project.project'
    _order = 'state'

    project_field_ids = fields.One2many("project.res.partner.fields", 'project_id')
    sale_id = fields.Many2one('sale.order')
    is_project_template = fields.Boolean(copy=False, tracking=True, default=False)
    state = fields.Selection([
        ('a_template', 'Template'),
        ('b_new', 'New Projects'),
        ('c_in_progress', 'In Progress'),
        ('d_done', 'Done'),
        ('on_hold', 'On Hold'),
        ('e_cancel', 'Cancelled'),
    ], string="Status", default='b_new', tracking=True, copy=False, readonly=True,
        group_expand='_expand_states', compute="_compute_project_state", store=True)

    @api.depends('filtered_task_ids.stage_id', 'is_project_template')
    def _compute_project_state(self):
        for project in self:
            if project.is_project_template:
                project.state = 'a_template'
            else:
                tasks = project.filtered_task_ids
                if tasks:
                    if any(task.stage_id.name == 'In Progress' for task in tasks):
                        project.state = 'c_in_progress'
                    elif all(task.stage_id.name == 'Done' for task in tasks):
                        project.state = 'd_done'
                    elif project.state in ['on_hold', 'e_cancel']:
                        continue  # Do not override manually set states
                    else:
                        project.state = 'b_new'
                else:
                    project.state = 'b_new'  # Default when no tasks exist

    @api.model
    def _expand_states(self, states, domain, order):
        return ['a_template', 'b_new', 'c_in_progress', 'd_done', 'on_hold', 'e_cancel']

    project_partner_ids = fields.Many2many("res.partner", relation="project_partner_id4", column1="project_partner_id5",
                                           column2="project_partner_id6", string="Partners",
                                           compute='get_project_partners')
    required_documents_ids = fields.One2many('documents.document', 'required_project_id', string='Required Documents',
                                             )
    deliverable_documents_ids = fields.One2many(
        'documents.document', 'deliverable_project_id',
        string='Deliverable Documents'
    )
    payment_state = fields.Selection(selection=PAYMENT_STATE_SELECTION, string='Payment Status',
                                     compute='get_payment_state')
    sale_payment_status = fields.Char(string="Sale Payment Status", compute='_compute_payment_status')
    invoice_id = fields.Many2one('account.move', compute='get_invoice_id')
    today_date = fields.Datetime(compute='get_today_date')
    date_start = fields.Date(string='Start Date', compute='get_date_start', store=True)
    user_id = fields.Many2one('res.users', string='Project Manager',
                              store=True, tracking=True)
    document_ids = fields.One2many('documents.document', 'project_id')
    document_type_ids = fields.One2many('task.document.lines', 'project_id', readonly=False)
    document_required_type_ids = fields.One2many('task.document.required.lines', 'project_id', readonly=False)
    product_ids = fields.Many2many('product.product', string='Products', readonly=False)
    project_product_ids = fields.One2many('project.project.products', 'project_id', string='Project Products')
    document_count = fields.Integer(compute='get_document_ids_count')
    filtered_task_ids = fields.Many2many('project.task', string='Tasks', compute='get_filtered_task_ids', )
    partner_ids = fields.Many2many('res.partner', string='ALl Customers', compute='get_partner_ids')
    sub_tasks_ids = fields.Many2many("project.task", relation="subtask_1", column1="subtask_2",
                                     column2="subtask_3", compute='_compute_sub_tasks_ids', string="Sub Tasks")
    subtasks_count = fields.Integer(compute='get_subtasks_ids_count')

    is_complete_return_required = fields.Boolean(string='Required Document Complete', copy=False)
    is_confirm_required = fields.Boolean(string='Required Document Confirm', copy=False)
    is_complete_return_deliverable = fields.Boolean(string='Deliverable Document Complete', copy=False)
    is_confirm_deliverable = fields.Boolean(string='Deliverable Document Confirm', copy=False)
    is_complete_return_partner_fields = fields.Boolean(string='Partner Fields Complete', copy=False)
    is_confirm_partner_fields = fields.Boolean(string='Partner Fields Confirm', copy=False)
    is_second_complete_partner_fields_check = fields.Integer(string='Second Complete Partner Fields Check', copy=False,
                                                             default=0)
    is_update_partner_fields = fields.Boolean(string='Update Partner Fields', copy=False)
    is_second_complete_deliverable_check = fields.Integer(string='Second Complete Deliverable Check', copy=False,
                                                          default=0)
    is_update_deliverable = fields.Boolean(string='Update Deliverable', copy=False)
    is_second_complete_required_check = fields.Integer(string='Second Complete Required Check', copy=False, default=0)
    is_update_required = fields.Boolean(string='Update Required', copy=False)
    is_complete_return_hand = fields.Boolean(string='Handover Complete', copy=False)
    is_check_current_user = fields.Boolean(compute="_compute_is_check_current_user")
    is_current_user_project_manager = fields.Boolean(compute="_compute_is_current_user_project_manager")
    is_current_user_project_admin = fields.Boolean(compute="_compute_is_current_user_project_admin")
    is_current_user_project_task_assignee = fields.Boolean(compute="_compute_is_current_user_project_task_assignee")
    is_complete_deliverable = fields.Boolean(copy=False)
    is_complete_required = fields.Boolean(copy=False)
    is_complete_partner_fields = fields.Boolean(copy=False)
    is_update_required_check = fields.Boolean(compute="_compute_is_update_required_check")
    is_update_deliverable_check = fields.Boolean(compute="_compute_is_update_deliverable_check")
    is_update_partner_fields_check = fields.Boolean(compute="_compute_is_update_partner_fields_check")

    @api.depends('is_complete_return_partner_fields', 'is_complete_partner_fields', 'is_confirm_partner_fields')
    def _compute_is_update_partner_fields_check(self):
        for record in self:
            if (
                    record.is_complete_return_partner_fields and record.is_complete_partner_fields == False and record.is_confirm_partner_fields == False) and (
                    record.is_current_user_project_task_assignee or record.is_current_user_project_admin):
                record.is_update_partner_fields_check = True
            else:
                record.is_update_partner_fields_check = False
    @api.depends('is_complete_return_deliverable', 'is_complete_deliverable', 'is_confirm_deliverable')
    def _compute_is_update_deliverable_check(self):
        for record in self:
            if (
                    record.is_complete_return_deliverable and record.is_complete_deliverable == False and record.is_confirm_deliverable == False) and (
                    record.is_current_user_project_task_assignee or record.is_current_user_project_admin):
                record.is_update_deliverable_check = True
            else:
                record.is_update_deliverable_check = False
    @api.depends('is_complete_return_required', 'is_complete_required', 'is_confirm_required')
    def _compute_is_update_required_check(self):
        for record in self:
            if (
                    record.is_complete_return_required and record.is_complete_required == False and record.is_confirm_deliverable == False) and (
                    record.is_current_user_project_manager or record.is_current_user_project_admin):
                record.is_update_required_check = True
            else:
                record.is_update_required_check = False


    @api.depends_context('uid')
    def _compute_is_current_user_project_task_assignee(self):
        current_user_id = self.env.uid
        for record in self:
            record.is_current_user_project_task_assignee = any(
                current_user_id in task.user_ids.ids for task in record.filtered_task_ids
            )

    @api.depends_context('uid')
    def _compute_is_current_user_project_manager(self):
        for record in self:
            record.is_current_user_project_manager = (self.env.user.id == record.user_id.id)

    @api.depends_context('uid')
    def _compute_is_current_user_project_admin(self):
        is_admin = self.env.user.has_group('project.group_project_manager')
        for record in self:
            record.is_current_user_project_admin = is_admin

    @api.depends_context('uid')
    def _compute_is_check_current_user(self):
        is_admin = self.env.user.has_group('project.group_project_manager')
        for record in self:
            record.is_check_current_user = is_admin or (self.env.user.id != record.user_id.id)

    def get_project_partners(self):
        for rec in self:
            partners = rec.compliance_shareholder_ids.mapped('contact_id.id')
            rec.project_partner_ids = [(6, 0, [rec.partner_id.id, rec.hand_partner_id.id] + partners)]

    def action_request_required_documents(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Required Documents',
            'view_mode': 'form',
            'res_model': 'required.documents.wizard',
            'target': 'new',
            'context': {'default_project_id': self.id},
        }

    def action_confirm_partner_fields(self):
        for rec in self:
            rec.is_confirm_partner_fields = True
            all_tasks = rec.filtered_task_ids | rec.sub_tasks_ids
            for task in all_tasks:
                selected_line = None  # To store the correct line for execution

                # Priority 1: Check for lines with ALL THREE partner_fields checkpoints
                for line in task.checkpoint_ids:
                    has_all_three = (
                            any(item.name == 'is_complete_return_partner_fields' for item in
                                line.reached_checkpoint_ids) and
                            any(item.name == 'is_confirm_partner_fields' for item in line.reached_checkpoint_ids) and
                            any(item.name == 'is_update_partner_fields' for item in line.reached_checkpoint_ids)
                    )
                    if has_all_three and rec.is_complete_return_partner_fields and rec.is_confirm_partner_fields and rec.is_update_partner_fields:
                        selected_line = line
                        break  # Highest priority match
                if selected_line:
                    pass  # Skip lower priorities if match found

                # Priority 2: Check for lines with ORIGINAL TWO partner_fields checkpoints
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_original_two = (
                                any(item.name == 'is_complete_return_partner_fields' for item in
                                    line.reached_checkpoint_ids) and
                                any(item.name == 'is_confirm_partner_fields' for item in line.reached_checkpoint_ids)
                        )
                        if has_original_two and rec.is_complete_return_partner_fields and rec.is_confirm_partner_fields:
                            selected_line = line
                            break  # Second priority match
                if selected_line:
                    pass

                # Priority 3: Check for lines with ONLY is_complete_return_partner_fields
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_single = any(
                            item.name == 'is_complete_return_partner_fields' for item in line.reached_checkpoint_ids)
                        if has_single and rec.is_complete_return_partner_fields:
                            selected_line = line
                            break  # Third priority match
                if selected_line:
                    pass

                # Priority 4: Check for lines with ONLY is_update_partner_fields
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_single = any(
                            item.name == 'is_update_partner_fields' for item in line.reached_checkpoint_ids)
                        if has_single and rec.is_update_partner_fields:
                            selected_line = line
                            break  # Fourth priority match
                if selected_line:
                    pass

                # Priority 5: Check for lines with ONLY is_confirm_partner_fields (if needed)
                # if not selected_line:
                #     for line in task.checkpoint_ids:
                #         if any(item.name == 'is_confirm_partner_fields' for item in line.reached_checkpoint_ids):
                #             if rec.is_confirm_partner_fields:
                #                 selected_line = line
                #                 break

                # Apply changes if any valid line found
                if selected_line:
                    task.all_milestone_id = selected_line.milestone_id.id
                    task.milestone_id = selected_line.milestone_id.id
                    task.stage_id = selected_line.stage_id.id

                    if task.partner_id and selected_line.milestone_id.mail_template_id:
                        task.action_send_email()
            rec.message_post(body=_(" Partner Fields Confirmed "))
    def action_return_partner_fields(self):
        return {
            'name': _('Return Partner Fields'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'return.project.wizard',
            'context': {'default_project_id': self.id, 'default_type': 'partner_fields'},
            'view_id': self.env.ref('freezoner_custom.project_return_form_view').id,
            'target': 'new',
        }
    def action_update_partner_fields(self):
        for rec in self:
            rec.is_complete_return_partner_fields = False
            rec.is_complete_partner_fields = True
            rec.is_second_complete_partner_fields_check = 2
            all_tasks = rec.filtered_task_ids | rec.sub_tasks_ids
            for task in all_tasks:
                selected_line = None  # To store the correct line for execution

                # Priority 1: Check for lines with ALL THREE partner_fields checkpoints
                for line in task.checkpoint_ids:
                    has_all_three = (
                            any(item.name == 'is_complete_return_partner_fields' for item in
                                line.reached_checkpoint_ids) and
                            any(item.name == 'is_confirm_partner_fields' for item in line.reached_checkpoint_ids) and
                            any(item.name == 'is_update_partner_fields' for item in line.reached_checkpoint_ids)
                    )
                    if has_all_three and rec.is_complete_return_partner_fields and rec.is_confirm_partner_fields and rec.is_update_partner_fields:
                        selected_line = line
                        break  # Highest priority match
                if selected_line:
                    pass  # Skip lower priorities if match found

                # Priority 2: Check for lines with ORIGINAL TWO partner_fields checkpoints
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_original_two = (
                                any(item.name == 'is_complete_return_partner_fields' for item in
                                    line.reached_checkpoint_ids) and
                                any(item.name == 'is_confirm_partner_fields' for item in line.reached_checkpoint_ids)
                        )
                        if has_original_two and rec.is_complete_return_partner_fields and rec.is_confirm_partner_fields:
                            selected_line = line
                            break  # Second priority match
                if selected_line:
                    pass

                # Priority 3: Check for lines with ONLY is_complete_return_partner_fields
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_single = any(
                            item.name == 'is_complete_return_partner_fields' for item in line.reached_checkpoint_ids)
                        if has_single and rec.is_complete_return_partner_fields:
                            selected_line = line
                            break  # Third priority match
                if selected_line:
                    pass

                # Priority 4: Check for lines with ONLY is_update_partner_fields
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_single = any(
                            item.name == 'is_update_partner_fields' for item in line.reached_checkpoint_ids)
                        if has_single and rec.is_update_partner_fields:
                            selected_line = line
                            break  # Fourth priority match
                if selected_line:
                    pass

                # Priority 5: Check for lines with ONLY is_confirm_partner_fields (if needed)
                # if not selected_line:
                #     for line in task.checkpoint_ids:
                #         if any(item.name == 'is_confirm_partner_fields' for item in line.reached_checkpoint_ids):
                #             if rec.is_confirm_partner_fields:
                #                 selected_line = line
                #                 break

                # Apply changes if any valid line found
                if selected_line:
                    task.all_milestone_id = selected_line.milestone_id.id
                    task.milestone_id = selected_line.milestone_id.id
                    task.stage_id = selected_line.stage_id.id

                    if task.partner_id and selected_line.milestone_id.mail_template_id:
                        task.action_send_email()
            rec.message_post(body=_(" Partner Fields Updated "))
    def action_complete_partner_fields(self):
        for rec in self:
            rec.is_complete_partner_fields = True
            all_tasks = rec.filtered_task_ids | rec.sub_tasks_ids
            for task in all_tasks:
                selected_line = None  # To store the correct line for execution

                # Priority 1: Check for lines with ALL THREE partner_fields checkpoints
                for line in task.checkpoint_ids:
                    has_all_three = (
                            any(item.name == 'is_complete_return_partner_fields' for item in
                                line.reached_checkpoint_ids) and
                            any(item.name == 'is_confirm_partner_fields' for item in line.reached_checkpoint_ids) and
                            any(item.name == 'is_update_partner_fields' for item in line.reached_checkpoint_ids)
                    )
                    if has_all_three and rec.is_complete_return_partner_fields and rec.is_confirm_partner_fields and rec.is_update_partner_fields:
                        selected_line = line
                        break  # Highest priority match
                if selected_line:
                    pass  # Skip lower priorities if match found

                # Priority 2: Check for lines with ORIGINAL TWO partner_fields checkpoints
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_original_two = (
                                any(item.name == 'is_complete_return_partner_fields' for item in
                                    line.reached_checkpoint_ids) and
                                any(item.name == 'is_confirm_partner_fields' for item in line.reached_checkpoint_ids)
                        )
                        if has_original_two and rec.is_complete_return_partner_fields and rec.is_confirm_partner_fields:
                            selected_line = line
                            break  # Second priority match
                if selected_line:
                    pass

                # Priority 3: Check for lines with ONLY is_complete_return_partner_fields
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_single = any(
                            item.name == 'is_complete_return_partner_fields' for item in line.reached_checkpoint_ids)
                        if has_single and rec.is_complete_return_partner_fields:
                            selected_line = line
                            break  # Third priority match
                if selected_line:
                    pass

                # Priority 4: Check for lines with ONLY is_update_partner_fields
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_single = any(
                            item.name == 'is_update_partner_fields' for item in line.reached_checkpoint_ids)
                        if has_single and rec.is_update_partner_fields:
                            selected_line = line
                            break  # Fourth priority match
                if selected_line:
                    pass

                # Priority 5: Check for lines with ONLY is_confirm_partner_fields (if needed)
                # if not selected_line:
                #     for line in task.checkpoint_ids:
                #         if any(item.name == 'is_confirm_partner_fields' for item in line.reached_checkpoint_ids):
                #             if rec.is_confirm_partner_fields:
                #                 selected_line = line
                #                 break

                # Apply changes if any valid line found
                if selected_line:
                    task.all_milestone_id = selected_line.milestone_id.id
                    task.milestone_id = selected_line.milestone_id.id
                    task.stage_id = selected_line.stage_id.id
                    rec.state = 'c_in_progress'
                    if task.partner_id and selected_line.milestone_id.mail_template_id:
                        task.action_send_email()
            rec.message_post(body=_(" Partner Fields Completed "))
    def action_repeat_partner_fields(self):
        for rec in self:
            rec.is_confirm_partner_fields = False
            rec.is_complete_partner_fields = False
            rec.is_complete_return_partner_fields = True
            rec.message_post(body=_("Partner Fields Repeated"))


    def action_complete_required(self):
        for rec in self:
            rec.is_complete_required = True
            # rec.is_complete_return_required = True
            all_tasks = rec.filtered_task_ids | rec.sub_tasks_ids
            for task in all_tasks:
                selected_line = None  # To store the correct line for execution

                # Priority 1: Check for lines with ALL THREE required checkpoints
                for line in task.checkpoint_ids:
                    has_all_three = (
                            any(item.name == 'is_complete_return_required' for item in line.reached_checkpoint_ids) and
                            any(item.name == 'is_confirm_required' for item in line.reached_checkpoint_ids) and
                            any(item.name == 'is_update_required' for item in line.reached_checkpoint_ids)
                    )
                    if has_all_three and rec.is_complete_return_required and rec.is_confirm_required and rec.is_update_required:
                        selected_line = line
                        break  # Highest priority match
                if selected_line:
                    pass  # Skip lower priorities if match found

                # Priority 2: Check for lines with ORIGINAL TWO required checkpoints
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_original_two = (
                                any(item.name == 'is_complete_return_required' for item in
                                    line.reached_checkpoint_ids) and
                                any(item.name == 'is_confirm_required' for item in line.reached_checkpoint_ids)
                        )
                        if has_original_two and rec.is_complete_return_required and rec.is_confirm_required:
                            selected_line = line
                            break  # Second priority match
                if selected_line:
                    pass

                # Priority 3: Check for lines with ONLY is_complete_return_required
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_single = any(
                            item.name == 'is_complete_return_required' for item in line.reached_checkpoint_ids)
                        if has_single and rec.is_complete_return_required:
                            selected_line = line
                            break  # Third priority match
                if selected_line:
                    pass

                # Priority 4: Check for lines with ONLY is_update_required
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_single = any(item.name == 'is_update_required' for item in line.reached_checkpoint_ids)
                        if has_single and rec.is_update_required:
                            selected_line = line
                            break  # Fourth priority match
                if selected_line:
                    pass

                # Priority 5: Check for lines with ONLY is_confirm_required (if needed)
                # if not selected_line:
                #     for line in task.checkpoint_ids:
                #         if any(item.name == 'is_confirm_required' for item in line.reached_checkpoint_ids):
                #             if rec.is_confirm_required:
                #                 selected_line = line
                #                 break

                # Apply changes if any valid line found
                if selected_line:
                    task.all_milestone_id = selected_line.milestone_id.id
                    task.milestone_id = selected_line.milestone_id.id
                    task.stage_id = selected_line.stage_id.id
                    rec.state = 'c_in_progress'
                    if task.partner_id and selected_line.milestone_id.mail_template_id:
                        task.action_send_email()
            rec.message_post(body=_(" Required Document Completed "))
    def action_confirm_required(self):
        for rec in self:
            rec.is_confirm_required = True
            all_tasks = rec.filtered_task_ids | rec.sub_tasks_ids
            for task in all_tasks:
                selected_line = None  # To store the correct line for execution

                # Priority 1: Check for lines with ALL THREE required checkpoints
                for line in task.checkpoint_ids:
                    has_all_three = (
                            any(item.name == 'is_complete_return_required' for item in line.reached_checkpoint_ids) and
                            any(item.name == 'is_confirm_required' for item in line.reached_checkpoint_ids) and
                            any(item.name == 'is_update_required' for item in line.reached_checkpoint_ids)
                    )
                    if has_all_three and rec.is_complete_return_required and rec.is_confirm_required and rec.is_update_required:
                        selected_line = line
                        break  # Highest priority match
                if selected_line:
                    pass  # Skip lower priorities if match found

                # Priority 2: Check for lines with ORIGINAL TWO required checkpoints
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_original_two = (
                                any(item.name == 'is_complete_return_required' for item in
                                    line.reached_checkpoint_ids) and
                                any(item.name == 'is_confirm_required' for item in line.reached_checkpoint_ids)
                        )
                        if has_original_two and rec.is_complete_return_required and rec.is_confirm_required:
                            selected_line = line
                            break  # Second priority match
                if selected_line:
                    pass

                # Priority 3: Check for lines with ONLY is_complete_return_required
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_single = any(
                            item.name == 'is_complete_return_required' for item in line.reached_checkpoint_ids)
                        if has_single and rec.is_complete_return_required:
                            selected_line = line
                            break  # Third priority match
                if selected_line:
                    pass

                # Priority 4: Check for lines with ONLY is_update_required
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_single = any(item.name == 'is_update_required' for item in line.reached_checkpoint_ids)
                        if has_single and rec.is_update_required:
                            selected_line = line
                            break  # Fourth priority match
                if selected_line:
                    pass

                # Priority 5: Check for lines with ONLY is_confirm_required (if needed)
                # if not selected_line:
                #     for line in task.checkpoint_ids:
                #         if any(item.name == 'is_confirm_required' for item in line.reached_checkpoint_ids):
                #             if rec.is_confirm_required:
                #                 selected_line = line
                #                 break

                # Apply changes if any valid line found
                if selected_line:
                    task.all_milestone_id = selected_line.milestone_id.id
                    task.milestone_id = selected_line.milestone_id.id
                    task.stage_id = selected_line.stage_id.id

                    if task.partner_id and selected_line.milestone_id.mail_template_id:
                        task.action_send_email()
            rec.message_post(body=_(" Required Document Confirmed "))
    def action_return_required(self):
        return {
            'name': _('Required Fields'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'return.project.wizard',
            'context': {'default_project_id': self.id, 'default_type': 'required'},
            'view_id': self.env.ref('freezoner_custom.project_return_form_view').id,
            'target': 'new',
        }
    def action_update_required(self):
        for rec in self:
            rec.is_complete_return_required = False
            rec.is_complete_required = True
            rec.is_second_complete_required_check = 2
            all_tasks = rec.filtered_task_ids | rec.sub_tasks_ids
            for task in all_tasks:
                selected_line = None  # To store the correct line for execution

                # Priority 1: Check for lines with ALL THREE required checkpoints
                for line in task.checkpoint_ids:
                    has_all_three = (
                            any(item.name == 'is_complete_return_required' for item in line.reached_checkpoint_ids) and
                            any(item.name == 'is_confirm_required' for item in line.reached_checkpoint_ids) and
                            any(item.name == 'is_update_required' for item in line.reached_checkpoint_ids)
                    )
                    if has_all_three and rec.is_complete_return_required and rec.is_confirm_required and rec.is_update_required:
                        selected_line = line
                        break  # Highest priority match
                if selected_line:
                    pass  # Skip lower priorities if match found

                # Priority 2: Check for lines with ORIGINAL TWO required checkpoints
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_original_two = (
                                any(item.name == 'is_complete_return_required' for item in
                                    line.reached_checkpoint_ids) and
                                any(item.name == 'is_confirm_required' for item in line.reached_checkpoint_ids)
                        )
                        if has_original_two and rec.is_complete_return_required and rec.is_confirm_required:
                            selected_line = line
                            break  # Second priority match
                if selected_line:
                    pass

                # Priority 3: Check for lines with ONLY is_complete_return_required
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_single = any(
                            item.name == 'is_complete_return_required' for item in line.reached_checkpoint_ids)
                        if has_single and rec.is_complete_return_required:
                            selected_line = line
                            break  # Third priority match
                if selected_line:
                    pass

                # Priority 4: Check for lines with ONLY is_update_required
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_single = any(item.name == 'is_update_required' for item in line.reached_checkpoint_ids)
                        if has_single and rec.is_update_required:
                            selected_line = line
                            break  # Fourth priority match
                if selected_line:
                    pass

                # Priority 5: Check for lines with ONLY is_confirm_required (if needed)
                # if not selected_line:
                #     for line in task.checkpoint_ids:
                #         if any(item.name == 'is_confirm_required' for item in line.reached_checkpoint_ids):
                #             if rec.is_confirm_required:
                #                 selected_line = line
                #                 break

                # Apply changes if any valid line found
                if selected_line:
                    task.all_milestone_id = selected_line.milestone_id.id
                    task.milestone_id = selected_line.milestone_id.id
                    task.stage_id = selected_line.stage_id.id

                    if task.partner_id and selected_line.milestone_id.mail_template_id:
                        task.action_send_email()
            rec.message_post(body=_(" Required Document Updated "))
    def action_repeat_required(self):
        for rec in self:
            rec.is_confirm_required = False
            rec.is_complete_required = False
            rec.is_complete_return_required = True
            rec.message_post(body=_("Required Documents Fields Repeated"))


    def action_complete_deliverable(self):
        for rec in self:
            rec.is_complete_deliverable = True
            # rec.is_complete_return_deliverable = True
            all_tasks = rec.filtered_task_ids | rec.sub_tasks_ids
            for task in all_tasks:
                selected_line = None  # To store the correct line for execution

                # Priority 1: Check for lines with ALL THREE deliverable checkpoints
                for line in task.checkpoint_ids:
                    has_all_three = (
                            any(item.name == 'is_complete_return_deliverable' for item in
                                line.reached_checkpoint_ids) and
                            any(item.name == 'is_confirm_deliverable' for item in line.reached_checkpoint_ids) and
                            any(item.name == 'is_update_deliverable' for item in line.reached_checkpoint_ids)
                    )
                    if has_all_three and rec.is_complete_return_deliverable and rec.is_confirm_deliverable and rec.is_update_deliverable:
                        selected_line = line
                        break  # Highest priority match
                if selected_line:
                    pass  # Skip lower priorities if match found

                # Priority 2: Check for lines with ORIGINAL TWO deliverable checkpoints
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_original_two = (
                                any(item.name == 'is_complete_return_deliverable' for item in
                                    line.reached_checkpoint_ids) and
                                any(item.name == 'is_confirm_deliverable' for item in line.reached_checkpoint_ids)
                        )
                        if has_original_two and rec.is_complete_return_deliverable and rec.is_confirm_deliverable:
                            selected_line = line
                            break  # Second priority match
                if selected_line:
                    pass

                # Priority 3: Check for lines with ONLY is_complete_return_deliverable
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_single = any(
                            item.name == 'is_complete_return_deliverable' for item in line.reached_checkpoint_ids)
                        if has_single and rec.is_complete_return_deliverable:
                            selected_line = line
                            break  # Third priority match
                if selected_line:
                    pass

                # Priority 4: Check for lines with ONLY is_update_deliverable
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_single = any(item.name == 'is_update_deliverable' for item in line.reached_checkpoint_ids)
                        if has_single and rec.is_update_deliverable:
                            selected_line = line
                            break  # Fourth priority match
                if selected_line:
                    pass

                # Priority 5: Check for lines with ONLY is_confirm_deliverable (if needed)
                # if not selected_line:
                #     for line in task.checkpoint_ids:
                #         if any(item.name == 'is_confirm_deliverable' for item in line.reached_checkpoint_ids):
                #             if rec.is_confirm_deliverable:
                #                 selected_line = line
                #                 break

                # Apply changes if any valid line found
                if selected_line:
                    task.all_milestone_id = selected_line.milestone_id.id
                    task.milestone_id = selected_line.milestone_id.id
                    task.stage_id = selected_line.stage_id.id
                    rec.state = 'c_in_progress'
                    if task.partner_id and selected_line.milestone_id.mail_template_id:
                        task.action_send_email()
            rec.message_post(body=_(" Deliverable Document Completed "))
    def action_confirm_deliverable(self):
        for rec in self:
            rec.is_confirm_deliverable = True
            all_tasks = rec.filtered_task_ids | rec.sub_tasks_ids
            for task in all_tasks:
                selected_line = None  # To store the correct line for execution

                # Priority 1: Check for lines with ALL THREE deliverable checkpoints
                for line in task.checkpoint_ids:
                    has_all_three = (
                            any(item.name == 'is_complete_return_deliverable' for item in
                                line.reached_checkpoint_ids) and
                            any(item.name == 'is_confirm_deliverable' for item in line.reached_checkpoint_ids) and
                            any(item.name == 'is_update_deliverable' for item in line.reached_checkpoint_ids)
                    )
                    if has_all_three and rec.is_complete_return_deliverable and rec.is_confirm_deliverable and rec.is_update_deliverable:
                        selected_line = line
                        break  # Highest priority match
                if selected_line:
                    pass  # Skip lower priorities if match found

                # Priority 2: Check for lines with ORIGINAL TWO deliverable checkpoints
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_original_two = (
                                any(item.name == 'is_complete_return_deliverable' for item in
                                    line.reached_checkpoint_ids) and
                                any(item.name == 'is_confirm_deliverable' for item in line.reached_checkpoint_ids)
                        )
                        if has_original_two and rec.is_complete_return_deliverable and rec.is_confirm_deliverable:
                            selected_line = line
                            break  # Second priority match
                if selected_line:
                    pass

                # Priority 3: Check for lines with ONLY is_complete_return_deliverable
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_single = any(
                            item.name == 'is_complete_return_deliverable' for item in line.reached_checkpoint_ids)
                        if has_single and rec.is_complete_return_deliverable:
                            selected_line = line
                            break  # Third priority match
                if selected_line:
                    pass

                # Priority 4: Check for lines with ONLY is_update_deliverable
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_single = any(item.name == 'is_update_deliverable' for item in line.reached_checkpoint_ids)
                        if has_single and rec.is_update_deliverable:
                            selected_line = line
                            break  # Fourth priority match
                if selected_line:
                    pass

                # Priority 5: Check for lines with ONLY is_confirm_deliverable (if needed)
                # if not selected_line:
                #     for line in task.checkpoint_ids:
                #         if any(item.name == 'is_confirm_deliverable' for item in line.reached_checkpoint_ids):
                #             if rec.is_confirm_deliverable:
                #                 selected_line = line
                #                 break

                # Apply changes if any valid line found
                if selected_line:
                    task.all_milestone_id = selected_line.milestone_id.id
                    task.milestone_id = selected_line.milestone_id.id
                    task.stage_id = selected_line.stage_id.id

                    if task.partner_id and selected_line.milestone_id.mail_template_id:
                        task.action_send_email()
            rec.message_post(body=_(" Deliverable Document Confirmed "))
    def action_return_deliverable(self):
        return {
            'name': _('Deliverable Fields'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'return.project.wizard',
            'context': {'default_project_id': self.id, 'default_type': 'deliverable'},
            'view_id': self.env.ref('freezoner_custom.project_return_form_view').id,
            'target': 'new',
        }
    def action_update_deliverable(self):
        for rec in self:
            rec.is_complete_return_deliverable = False
            rec.is_complete_deliverable = True
            rec.is_second_complete_deliverable_check = 2
            all_tasks = rec.filtered_task_ids | rec.sub_tasks_ids
            for task in all_tasks:
                selected_line = None  # To store the correct line for execution

                # Priority 1: Check for lines with ALL THREE deliverable checkpoints
                for line in task.checkpoint_ids:
                    has_all_three = (
                            any(item.name == 'is_complete_return_deliverable' for item in
                                line.reached_checkpoint_ids) and
                            any(item.name == 'is_confirm_deliverable' for item in line.reached_checkpoint_ids) and
                            any(item.name == 'is_update_deliverable' for item in line.reached_checkpoint_ids)
                    )
                    if has_all_three and rec.is_complete_return_deliverable and rec.is_confirm_deliverable and rec.is_update_deliverable:
                        selected_line = line
                        break  # Highest priority match
                if selected_line:
                    pass  # Skip lower priorities if match found

                # Priority 2: Check for lines with ORIGINAL TWO deliverable checkpoints
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_original_two = (
                                any(item.name == 'is_complete_return_deliverable' for item in
                                    line.reached_checkpoint_ids) and
                                any(item.name == 'is_confirm_deliverable' for item in line.reached_checkpoint_ids)
                        )
                        if has_original_two and rec.is_complete_return_deliverable and rec.is_confirm_deliverable:
                            selected_line = line
                            break  # Second priority match
                if selected_line:
                    pass

                # Priority 3: Check for lines with ONLY is_complete_return_deliverable
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_single = any(
                            item.name == 'is_complete_return_deliverable' for item in line.reached_checkpoint_ids)
                        if has_single and rec.is_complete_return_deliverable:
                            selected_line = line
                            break  # Third priority match
                if selected_line:
                    pass

                # Priority 4: Check for lines with ONLY is_update_deliverable
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_single = any(item.name == 'is_update_deliverable' for item in line.reached_checkpoint_ids)
                        if has_single and rec.is_update_deliverable:
                            selected_line = line
                            break  # Fourth priority match
                if selected_line:
                    pass

                # Priority 5: Check for lines with ONLY is_confirm_deliverable (if needed)
                # if not selected_line:
                #     for line in task.checkpoint_ids:
                #         if any(item.name == 'is_confirm_deliverable' for item in line.reached_checkpoint_ids):
                #             if rec.is_confirm_deliverable:
                #                 selected_line = line
                #                 break

                # Apply changes if any valid line found
                if selected_line:
                    task.all_milestone_id = selected_line.milestone_id.id
                    task.milestone_id = selected_line.milestone_id.id
                    task.stage_id = selected_line.stage_id.id

                    if task.partner_id and selected_line.milestone_id.mail_template_id:
                        task.action_send_email()
            rec.message_post(body=_(" Deliverable Document Updated "))
    def action_repeat_deliverable(self):
        for rec in self:
            rec.is_confirm_deliverable = False
            rec.is_complete_deliverable = False
            rec.is_complete_return_deliverable = True
            rec.message_post(body=_("Deliverable Documents Fields Repeated"))


    @api.depends('task_ids')
    def _compute_sub_tasks_ids(self):
        for rec in self:
            rec.sub_tasks_ids = [(6, 0, [task.id for task in rec.task_ids if task.parent_id])]

    def action_view_subtasks(self):
        recs = self.mapped('sub_tasks_ids')
        action = self.env.ref('freezoner_custom.all_tasks_action').read()[0]
        # Get the kanban and tree view IDs
        list_view = self.env.ref('freezoner_custom.project_subtask_tree').id
        form_view = self.env.ref('project.view_task_form2').id
        # Configure views to show kanban first and tree as an option
        action['views'] = [
            (list_view, 'list'),
            (form_view, 'form')
        ]
        action['view_mode'] = 'tree,form'
        if recs:
            action['domain'] = [('id', 'in', recs.ids)]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.depends('sub_tasks_ids')
    def get_subtasks_ids_count(self):
        for rec in self:
            rec.subtasks_count = len(rec.sub_tasks_ids)

    @api.depends('sale_id', 'sale_order_id')
    def _compute_payment_status(self):
        for rec in self:
            if rec.sale_id:
                rec.sale_payment_status = rec.sale_id.payment_status
            elif rec.sale_order_id:
                rec.sale_payment_status = rec.sale_order_id.payment_status
            else:
                rec.sale_payment_status = ''

    def action_update_current_value(self):
        for rec in self:
            for line in rec.project_field_ids:
                # Handle many2one field type
                if line.field_id.ttype == 'many2one':
                    # Modify regex to handle cases like res.country.state(1403,)
                    match = re.search(r'\((\d+),?\)', str(line.current_value))
                    print('Regex Match for many2one:', match)

                    if match:
                        record = self.env[line.field_id.relation].sudo().browse(int(match.group(1)))
                        print('record name ', record.name)
                        line.current_value = record.name if record else ''
                    else:
                        # Handle case where no match is found
                        print('No match found for many2one')

                # Handle many2many field type
                # elif line.field_id.ttype == 'many2many':
                #     # Debug: Print the values being processed for many2many
                #     print('Processing many2many values:', line.current_value)
                #
                #     ids = [re.search(r'\((\d+),?\)', str(l)) for l in line.current_value]
                #     print('Extracted Matches for many2many:', ids)
                #
                #     # Filter out any None values from the list
                #     ids = [match.group(1) for match in ids if match]
                #
                #     # Use browse to fetch records and get their names
                #     records = self.env[line.field_id.relation].sudo().browse([int(id) for id in ids])
                #     line.current_value = ', '.join(records.mapped('name')) if records else ''
                #
                #     # Debug: Print the result for many2many
                #     print('Updated current_value for many2many:', line.current_value)

    def get_partner_ids(self):
        for rec in self:
            if rec.compliance_shareholder_ids:
                partners = {
                    partner_id
                    for partner in rec.compliance_shareholder_ids
                    for partner_id in (partner.partner_id.id, partner.contact_id.id)
                    if partner_id
                }
            else:
                partners = set()
            rec.partner_ids = list(partners)

    def get_filtered_task_ids(self):
        for rec in self:
            task_ids = rec.task_ids.filtered(lambda t: not t.parent_id).ids
            project_task_ids = self.env['project.task'].sudo().search([
                ('project_id', '=', rec.id),
                ('parent_id', '=', False)
            ]).ids
            rec.filtered_task_ids = list(set(task_ids + project_task_ids))  # Remove duplicates

    @api.onchange('task_ids')
    def onchange_products(self):
        for rec in self:
            rec.product_ids = [(6, 0, [task.sale_line_id.product_id.id for task in rec.task_ids if
                                       task.sale_line_id and task.sale_line_id.product_id])]

    @api.onchange('product_ids')
    def onchange_document_type_ids(self):
        for rec in self:
            document_lines = []
            for product in rec.product_ids:
                for doc in product.document_type_ids:
                    document_lines.append({
                        'project_id': rec.id,
                        'document_id': doc.document_id.id,
                        'is_required': doc.is_required,
                    })
            if document_lines:
                self.env['task.document.lines'].sudo().create(document_lines)

    @api.onchange('product_ids')
    def onchange_document_required_type_ids(self):
        for rec in self:
            document_lines = []
            for product in rec.product_ids:
                for doc in product.document_required_type_ids:
                    document_lines.append({
                        'project_id': rec.id,
                        'document_id': doc.document_id.id,
                        'is_required': doc.is_required,
                    })
            if document_lines:
                self.env['task.document.required.lines'].sudo().create(document_lines)

    @api.depends('document_ids')
    def get_document_ids_count(self):
        for rec in self:
            rec.document_count = len(rec.document_ids)

    def create_documents(self):
        for rec in self:
            for line in rec.document_type_ids:
                if not line.issue_date and line.document:
                    raise ValidationError(_('PLease add issue date in  \'%s\'.') % (line.name,))
                if line.is_moved == False and line.issue_date:
                    vals = {
                        'name': str(line.name),
                        'folder_id': 15,
                        'project_id': line.project_id.id,
                        'type_id': line.document_id.id,
                        'partner_id': line.partner_id.id,
                        'issue_date': line.issue_date or False,
                        'expiration_date': line.expiration_date or False,
                        'datas': line.document,
                        'thumbnail': line.document,
                    }
                    self.sudo().env['documents.document'].sudo().create(vals)
                    line.is_moved = True
            for line in rec.document_required_type_ids:
                if not line.issue_date and line.document:
                    raise ValidationError(_('PLease add issue date in  \'%s\'.') % (line.name,))
                if line.is_moved == False and line.issue_date:
                    if line.is_moved == False and line.issue_date:
                        vals = {
                            'name': str(line.name),
                            'folder_id': 15,
                            'project_id': line.project_id.id,
                            'type_id': line.document_id.id,
                            'partner_id': line.partner_id.id,
                            'issue_date': line.issue_date or False,
                            'expiration_date': line.expiration_date or False,
                            'datas': line.document,
                            'thumbnail': line.document,
                        }
                        doc = self.sudo().env['documents.document'].sudo().create(vals)
                        line.is_moved = True

    def action_view_document(self):
        """ Smart button to open kanban view with tree view as an option """
        document_ids = self.mapped('document_ids') | self.mapped('required_documents_ids') | self.mapped(
            'deliverable_documents_ids')
        recs = self.env['documents.document'].browse(document_ids.ids)
        action = self.env.ref('documents.document_action').read()[0]
        # Get the kanban and tree view IDs
        kanban_view = self.env.ref('documents.document_view_kanban').id
        tree_view = self.env.ref('documents.documents_view_list').id
        form_view = self.env.ref('documents.document_view_form').id
        # Configure views to show kanban first and tree as an option
        action['views'] = [
            (kanban_view, 'kanban'),
            (tree_view, 'tree'),
            (form_view, 'form')
        ]
        action['view_mode'] = 'kanban,tree,form'
        if recs:
            action['domain'] = [('id', 'in', recs.ids)]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        print(' actionnnnnnnnnnnn   ', action)
        return action

    @api.model
    def create(self, values):
        res = super(Project, self).create(values)
        for rec in res:
            email_values = {
                'subject': 'Project Created',
                'body_html': (
                    f'<strong> Project Created </strong> <br/>'
                    f'<p> {rec.name}</p>'
                ),
                'email_from': rec.company_id.email,
                'email_to': rec.user_id.partner_id.email,
            }
            mail = self.env['mail.mail'].create(email_values)
            mail.send()
        return res

    def action_done_project(self):
        for rec in self:
            rec.state = 'd_done'

    def action_update_old_data(self):
        projects = self.env['project.project'].sudo().search([])
        for rec in projects:
            # rec.date_start = rec.create_date.date()
            # project_user_id = rec.create_uid.id
            # self.env.cr.execute("UPDATE project_project set user_id = '%s' WHERE id=%s" % (
            #     project_user_id, rec.id))
            if rec.sale_line_id:
                # product_name = rec.sale_line_id.product_id.name
                # date_ref = "{:02d}{:02d}".format(rec.create_date.year % 100, rec.create_date.month)
                # project_name = f"{rec.sale_line_id.order_id.name} - {date_ref} - {product_name}"
                rec.name = rec.sale_line_id.order_id.create_uid.id

                # print(' project_name  ------>  ', project_name)
                # self.env.cr.execute("UPDATE project_project SET name = COALESCE(name, %s::jsonb) WHERE id = %s",
                #                     ('"sevo"', rec.id))

    def update_required_document(self):
        for rec in self:
            existing_docs = rec.document_ids.filtered(
                lambda doc: any(
                    required.document_id.id == doc.type_id.id and required.partner_id.id == doc.partner_id.id
                    for required in rec.document_required_type_ids
                )
            )

            for required in rec.document_required_type_ids:
                matching_doc = existing_docs.filtered(
                    lambda
                        doc: required.document_id.id == doc.type_id.id and required.partner_id.id == doc.partner_id.id
                )

                if matching_doc:
                    matching_doc.required_project_id = rec.id
                else:
                    self.env['documents.document'].sudo().create({
                        'required_project_id': rec.id,
                        'folder_id': rec.documents_folder_id.id,
                        'partner_id': required.partner_id.id,
                        'type_id': required.document_id.id,
                        'name': f"{required.document_id.name} - {required.partner_id.name}",
                        'issue_date': required.issue_date,
                        'expiration_date': required.expiration_date,
                    })

    def update_deliverable_document(self):
        for rec in self:
            existing_docs = rec.document_ids.filtered(
                lambda doc: any(
                    deliverable.document_id.id == doc.type_id.id and deliverable.partner_id.id == doc.partner_id.id
                    for deliverable in rec.document_type_ids
                )
            )

            for deliverable in rec.document_type_ids:
                matching_doc = existing_docs.filtered(
                    lambda
                        doc: deliverable.document_id.id == doc.type_id.id and deliverable.partner_id.id == doc.partner_id.id
                )

                if matching_doc:
                    matching_doc.deliverable_project_id = rec.id
                else:
                    self.env['documents.document'].sudo().create({
                        'deliverable_project_id': rec.id,
                        'folder_id': rec.documents_folder_id.id,
                        'partner_id': deliverable.partner_id.id,
                        'type_id': deliverable.document_id.id,
                        'name': f"{deliverable.document_id.name} - {deliverable.partner_id.name}",
                        'issue_date': deliverable.issue_date,
                        'expiration_date': deliverable.expiration_date,
                    })

    @api.depends('create_date')
    def get_date_start(self):
        for rec in self:
            rec.date_start = rec.create_date.date()

    @api.depends('invoice_id')
    def get_payment_state(self):
        for rec in self:
            if rec.invoice_id:
                print(' rec.invoice_id.amount_residual ', rec.invoice_id.amount_residual)
                print(' rec.invoice_id.amount_total ', rec.invoice_id.amount_total)
                if rec.invoice_id.amount_residual == rec.invoice_id.amount_total:
                    rec.payment_state = 'not_paid'
                elif rec.invoice_id.amount_residual != rec.invoice_id.amount_total and rec.invoice_id.amount_residual > 0.0:
                    rec.payment_state = 'partial'
                elif rec.invoice_id.amount_residual == 0.0 and rec.invoice_id.payment_method == 'visa':
                    rec.payment_state = 'paid_visa'
                elif rec.invoice_id.amount_residual == 0.0 and rec.invoice_id.payment_method == 'bank':
                    rec.payment_state = 'paid_bank'
            else:
                rec.payment_state = 'not_paid'

    def get_today_date(self):
        self.today_date = fields.Datetime.now()

    # @api.onchange('documents_ids')
    # def onchange_required_documents(self):
    #     for project in self:
    #         required_docs = project.document_ids.filtered(lambda d: d.is_required_document)
    #         existing_docs = project.required_documents_ids
    #         # Add required documents if not already in document_ids
    #         missing_docs = required_docs - existing_docs
    #         print(' sevoooooooooooo ')
    #         print('  missing_docs  ', missing_docs, required_docs, existing_docs)
    #         if missing_docs:
    #             project.write({'required_documents_ids': [(4, doc.id) for doc in missing_docs]})

    # def write(self, vals):
    #     res = super(Project, self).write(vals)
    #     if self.project_exception_id.state != 'approved' and self.state != 'a_template':
    #         if self.today_date and self.create_date:
    #             today_date = self.today_date
    #             create_date = self.create_date
    #             if today_date.date() != create_date.date():
    #                 if not self.invoice_id:
    #                     raise ValidationError(_('Invoice not paid'))
    #                 if self.payment_state == 'not_paid':
    #                     raise ValidationError(_('Invoice not paid'))
    #             elif today_date.date() == create_date.date() and (today_date - create_date).total_seconds() > 60:
    #                 if not self.invoice_id:
    #                     raise ValidationError(_('Invoice not paid'))
    #                 if self.payment_state == 'not_paid':
    #                     raise ValidationError(_('Invoice not paid'))
    #     return res

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

    def action_view_tasks(self):
        if self.env.user.has_group('project.group_project_manager'):
            action = self.env['ir.actions.act_window'].with_context({'active_id': self.id})._for_xml_id(
                'project.act_project_project_2_project_task_all')
            action['display_name'] = _("%(name)s", name=self.name)
            context = action['context'].replace('active_id', str(self.id))
            context = ast.literal_eval(context)
            context.update({
                'create': self.active,
                'active_test': self.active
            })
            action['context'] = context
            return action
        if self.env.user.has_group('project.group_project_user'):
            action = self.env['ir.actions.act_window'].with_context({'active_id': self.id})._for_xml_id(
                'freezoner_custom.act_project_project_3_project_task_all')
            action['display_name'] = _("%(name)s", name=self.name)
            context = action['context'].replace('active_id', str(self.id))
            context = ast.literal_eval(context)
            context.update({
                'create': self.active,
                'active_test': self.active
            })
            action['context'] = context
            return action

    def action_in_progress(self):
        for rec in self:
            salesperson_check = False
            task_exist = False
            check_tasks = False
            for task in self.task_ids:
                if task.name in ['Documents To Be Collected', 'Collecting Required Documents']:
                    task_exist = True
                    break
            for task1 in self.task_ids:
                for usr in task1.user_ids:
                    if usr.employee_id.is_salesperson_task == False:
                        salesperson_check = True
                        break
            for task in self.task_ids:
                if task.name in ['Documents To Be Collected', 'Collecting Required Documents']:
                    if task.stage_id.is_done == False:
                        check_tasks = True
                        break
            if rec.state == 'b_new' and task_exist == False:
                raise UserError(
                    " This Task ( Documents To Be Collected or  Collecting Required Documents) , Not Exist !!! ")
            if rec.state == 'b_new' and salesperson_check == True:
                raise UserError(" Please Check Salesperson Assigned To Tasks That Related On This Project ")
            if rec.state == 'b_new' and check_tasks == True:
                raise UserError(" Please Close Task Assignation And Stage ")
            else:
                rec.state = 'c_in_progress'

    def action_done(self):
        for rec in self:
            check_tasks = False
            for task in self.task_ids:
                if task.stage_id.is_done == False:
                    check_tasks = True
                    break
            if rec.state == 'c_in_progress' and check_tasks == True:
                raise UserError(" Please Close All Tasks ")
            else:
                rec.state = 'd_done'

    def action_onhold(self):
        for rec in self:
            rec.is_project_template = False
            rec.state = 'on_hold'

    def action_template(self):
        for rec in self:
            rec.is_project_template = True
            rec.state = 'a_template'

    def action_cancel(self):
        for rec in self:
            rec.is_project_template = False
            rec.state = 'e_cancel'

    def action_new(self):
        for rec in self:
            rec.is_project_template = False
            rec.state = 'b_new'

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if 'state' in groupby:
            orderby = 'state ASC' + (orderby and (',' + orderby) or '')

        return super(Project, self).read_group(domain, fields, groupby, offset=0, limit=limit, orderby=orderby,
                                               lazy=lazy)


class StageTask(models.Model):
    _inherit = 'project.task.type'

    is_done = fields.Boolean('Done Stage')
