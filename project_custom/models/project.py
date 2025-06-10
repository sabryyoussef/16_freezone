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


class Project(models.Model):
    _inherit = 'project.project'
    _order = 'state'


    @api.depends('hand_partner_company_type')
    def _get_partners(self):
        print(' hand_partner_company_type   ', self.hand_partner_company_type)
        lst = []
        partners = self.env['res.partner'].sudo().search([('company_type', '=', self.hand_partner_company_type)])
        for p in partners:
            if p.company_type == self.hand_partner_company_type:
                lst.append(p.id)
        self.hand_partner_ids = lst


    initial_company_info = fields.Boolean('Initial Company Formation', default=True,copy=False)
    apply_visa = fields.Boolean('Apply Visa', copy=False)
    proposed_name1 = fields.Char(string="Proposed Name1")
    proposed_name2 = fields.Char(string="Proposed Name2")
    proposed_name3 = fields.Char(string="Proposed Name3")
    full_name = fields.Char(compute='get_full_name', store=True)
    individual_full_name = fields.Char(compute='get_individual_full_name', store=True)
    hand_partner_ids = fields.Many2many('res.partner', string='Contact', compute='_get_partners')
    hand_partner_id = fields.Many2one('res.partner', string='Company Name',
                                      domain="[('id','in', hand_partner_ids), ('company_type','=','company')]")
    hand_legal_type = fields.Selection(string="Legal Entity/Type",
                                       selection=[('fzco', 'FZCO'), ('fze', 'FZE'), ('llc', 'LLC'), ], default=''
                                       , related='hand_partner_id.hand_legal_type', readonly=False)
    hand_legal_type_id = fields.Many2one('hand.legal.type', string='Legal Entity/Type',
                                        related='hand_partner_id.hand_legal_type_id', readonly=False)
    visa_eligibility = fields.Float('Visa Eligibility', related='hand_partner_id.visa_eligibility', readonly=False)
    hand_partner_company_type = fields.Selection(selection=[('person', 'Individual'), ('company', 'Company'), ],
                                                 default='company', string="Contact Type")
    hand_partner_gender = fields.Selection(string="Gender", selection=[('male', 'Male'), ('female', 'Female'), ],
                                           related='hand_partner_id.gender', readonly=False)
    hand_partner_first_name = fields.Char('First Name', readonly=False) # related='hand_partner_id.first_name',
    hand_partner_middle_name = fields.Char('Middle Name', readonly=False) # related='hand_partner_id.middle_name',
    hand_partner_last_name = fields.Char('Last Name', readonly=False) # related='hand_partner_id.last_name',
    hand_partner_nationality_id = fields.Many2one('res.nationality', string='Nationality',
                                                  related='hand_partner_id.nationality_id', readonly=False)
    hand_partner_place_of_birth = fields.Many2one('res.country', string='PLace Of Birth',
                                                  related='hand_partner_id.place_of_birth', readonly=False)
    hand_partner_birthday = fields.Date(string='Birthday', related='hand_partner_id.birthday', readonly=False)
    price_per_share = fields.Float('Price Per Share', related='hand_partner_id.price_per_share', readonly=False)
    total_number_shares = fields.Float('Total Number Of Shares', related='hand_partner_id.total_number_shares',
                                       readonly=False)
    total_share_value = fields.Monetary('Total Share Value', compute='_get_share_value')
    correspondence_email_address = fields.Char('Correspondence Email Address', related='hand_partner_id.email',
                                               readonly=False)
    hand_country_ids = fields.Many2many('res.country', string='Top 5 Countries of Operation',
                                        related='hand_partner_id.hand_country_ids', readonly=False)
    license_authority_id = fields.Many2one('product.attribute.value', string='License Authority',
                                           related='hand_partner_id.license_authority_id', readonly=False)
    license_validity = fields.Selection(string="License Validity", selection=[('1', '1 Year'), ('2', '2 Years'),
                                                                              ('3', '3 Years'), ('4', '4 Years'),
                                                                              ('5', '5 Years'), ('6', '6 Years'),
                                                                              ('7', '7 Years'), ('8', '8 Years'),
                                                                              ('9', '9 Years'), ('10', '10 Years'), ],
                                        related='hand_partner_id.license_validity', readonly=False
                                        )
    all_license_activity_ids = fields.Many2many("license.activity", relation="activity1", column1="activity2",
                                                column2="activity3", string='ALl License Activity',
                                                compute='_onchange_license_activity_ids')
    license_activity_ids = fields.Many2many('license.activity', string='License Activity',
                                            related='hand_partner_id.license_activity_ids',
                                            readonly=False,
                                            domain="[('id', 'in', all_license_activity_ids)]")
    compliance_shareholder_ids = fields.One2many("res.partner.shareholder", 'project_id',
                                                 related='hand_partner_id.compliance_shareholder_ids', readonly=False,
                                                 string="Compliance")
    shareholding_total = fields.Float(compute='get_shareholding_total')
    preferred_mobile_number = fields.Char('Preferred Mobile Number', related='hand_partner_id.mobile', readonly=False)
    channel_plan_id = fields.Many2one('channel.partner.plan',string="Channel Partner Plan", related='hand_partner_id.channel_plan_id', readonly=False)
    mobile_country_id = fields.Many2one('res.country', string="Mobile Country",
                                        related='hand_partner_id.mobile_country_id', readonly=False)
    is_visa_application = fields.Boolean('Is Visa Application', copy=False)
    project_visa_application_ids = fields.One2many('project.visa.application', 'project_id', string='Visa Application',readonly=False)
    is_complete_return_hand = fields.Boolean(string='Handover Complete', copy=False)
    is_confirm_hand = fields.Boolean(string='Handover Confirm', copy=False)
    is_complete_return_compliance = fields.Boolean(string='Compliance Complete', copy=False)
    is_complete_return_compliance = fields.Boolean(string='Compliance Complete', copy=False)
    is_confirm_compliance = fields.Boolean(string='Compliance Confirm', copy=False)
    is_update_hand = fields.Boolean(string='Update Handover', copy=False)
    is_second_complete_hand_check = fields.Integer(string='Second Complete Handover Check', copy=False, default=0)
    is_second_complete_compliance_check = fields.Integer(string='Second Complete Compliance Check', copy=False,
                                                         default=0)
    is_update_compliance = fields.Boolean(string='Update Compliance', copy=False)
    invoice_ids = fields.Many2many('account.move', related='sale_id.invoice_ids', string='Invoices')
    is_complete_hand = fields.Boolean(copy=False)
    is_complete_compliance = fields.Boolean(copy=False)
    is_create_individual_profile = fields.Boolean('Create Individual Profile',copy=False)
    is_update_compliance_check = fields.Boolean(compute="_compute_is_update_compliance_check")
    is_update_hand_check = fields.Boolean(compute="_compute_is_update_hand_check")

    @api.depends('is_complete_return_hand', 'is_complete_hand', 'is_confirm_hand')
    def _compute_is_update_hand_check(self):
        for record in self:
            if (record.is_complete_return_hand and record.is_complete_hand == False and record.is_confirm_hand == False) and (record.is_current_user_project_manager or record.is_current_user_project_admin):
                record.is_update_hand_check = True
            else:
                record.is_update_hand_check = False

    @api.depends('is_complete_return_compliance', 'is_complete_compliance', 'is_confirm_compliance')
    def _compute_is_update_compliance_check(self):
        for record in self:
            if (record.is_complete_return_compliance and record.is_complete_compliance == False and record.is_confirm_compliance == False) and (record.is_current_user_project_manager or record.is_current_user_project_admin):
                record.is_update_compliance_check = True
            else:
                record.is_update_compliance_check = False


    def action_view_sale(self):
        """ Smart button to run action """
        recs = self.mapped('sale_id') or self.mapped('sale_order_id')
        action = self.env.ref('sale.action_quotations_with_onboarding').read()[0]
        if len(recs) > 1:
            action['domain'] = [('id', 'in', recs.ids)]
        elif len(recs) == 1:
            action['views'] = [(
                self.env.ref('sale.view_order_form').id, 'form'
            )]
            action['res_id'] = recs.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
    def action_view_invoices(self):
        """ Smart button to run action """
        recs = self.mapped('invoice_ids')
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        if len(recs) > 1:
            action['domain'] = [('id', 'in', recs.ids)]
        elif len(recs) == 1:
            action['views'] = [(
                self.env.ref('account.view_move_form').id, 'form'
            )]
            action['res_id'] = recs.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def action_return_hand(self):
        return {
            'name': _('Handover Returned'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'return.project.wizard',
            'context': {'default_project_id': self.id, 'default_type': 'hand'},
            'view_id': self.env.ref('freezoner_custom.project_return_form_view').id,
            'target': 'new',
        }
    def action_update_hand(self):
        for rec in self:
            rec.is_complete_return_hand = False
            rec.is_complete_hand = True
            rec.is_second_complete_hand_check = 2
            all_tasks = rec.filtered_task_ids | rec.sub_tasks_ids
            for task in all_tasks:
                selected_line = None  # To store the correct line for execution

                # Priority 1: Check for lines with ALL THREE checkpoints
                for line in task.checkpoint_ids:
                    has_all_three = (
                            any(item.name == 'is_complete_return_hand' for item in line.reached_checkpoint_ids) and
                            any(item.name == 'is_confirm_hand' for item in line.reached_checkpoint_ids) and
                            any(item.name == 'is_update_hand' for item in line.reached_checkpoint_ids)
                    )
                    if has_all_three and rec.is_complete_return_hand and rec.is_confirm_hand and rec.is_update_hand:
                        selected_line = line
                        break  # Highest priority match
                if selected_line:
                    pass  # Skip lower priorities if match found

                # Priority 2: Check for lines with ORIGINAL TWO checkpoints
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_original_two = (
                                any(item.name == 'is_complete_return_hand' for item in line.reached_checkpoint_ids) and
                                any(item.name == 'is_confirm_hand' for item in line.reached_checkpoint_ids)
                        )
                        if has_original_two and rec.is_complete_return_hand and rec.is_confirm_hand:
                            selected_line = line
                            break  # Second priority match
                if selected_line:
                    pass

                # Priority 3: Check for lines with ONLY is_complete_return_hand
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_single = any(item.name == 'is_complete_return_hand' for item in line.reached_checkpoint_ids)
                        if has_single and rec.is_complete_return_hand:
                            selected_line = line
                            break  # Third priority match
                if selected_line:
                    pass

                # Priority 4: Check for lines with ONLY is_update_hand (NEW FIELD)
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_single = any(item.name == 'is_update_hand' for item in line.reached_checkpoint_ids)
                        if has_single and rec.is_update_hand:
                            selected_line = line
                            break  # Fourth priority match
                if selected_line:
                    pass

                # Priority 5: Check for lines with ONLY is_confirm_hand (if needed)
                # if not selected_line:
                #     for line in task.checkpoint_ids:
                #         if any(item.name == 'is_confirm_hand' for item in line.reached_checkpoint_ids):
                #             if rec.is_confirm_hand:
                #                 selected_line = line
                #                 break

                # Apply changes if any valid line found
                if selected_line:
                    task.all_milestone_id = selected_line.milestone_id.id
                    task.milestone_id = selected_line.milestone_id.id
                    task.stage_id = selected_line.stage_id.id

                    if task.partner_id and selected_line.milestone_id.mail_template_id:
                        task.action_send_email()
            rec.message_post(body=_("Handover Updated"))
    def action_complete_hand(self):
        for rec in self:
            rec.is_complete_hand = True
            # rec.is_complete_return_hand = True
            all_tasks = rec.filtered_task_ids | rec.sub_tasks_ids
            for task in all_tasks:
                selected_line = None  # To store the correct line for execution

                # Priority 1: Check for lines with ALL THREE checkpoints
                for line in task.checkpoint_ids:
                    has_all_three = (
                            any(item.name == 'is_complete_return_hand' for item in line.reached_checkpoint_ids) and
                            any(item.name == 'is_confirm_hand' for item in line.reached_checkpoint_ids) and
                            any(item.name == 'is_update_hand' for item in line.reached_checkpoint_ids)
                    )
                    if has_all_three and rec.is_complete_return_hand and rec.is_confirm_hand and rec.is_update_hand:
                        selected_line = line
                        break  # Highest priority match
                if selected_line:
                    pass  # Skip lower priorities if match found

                # Priority 2: Check for lines with ORIGINAL TWO checkpoints
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_original_two = (
                                any(item.name == 'is_complete_return_hand' for item in line.reached_checkpoint_ids) and
                                any(item.name == 'is_confirm_hand' for item in line.reached_checkpoint_ids)
                        )
                        if has_original_two and rec.is_complete_return_hand and rec.is_confirm_hand:
                            selected_line = line
                            break  # Second priority match
                if selected_line:
                    pass

                # Priority 3: Check for lines with ONLY is_complete_return_hand
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_single = any(item.name == 'is_complete_return_hand' for item in line.reached_checkpoint_ids)
                        if has_single and rec.is_complete_return_hand:
                            selected_line = line
                            break  # Third priority match
                if selected_line:
                    pass

                # Priority 4: Check for lines with ONLY is_update_hand (NEW FIELD)
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_single = any(item.name == 'is_update_hand' for item in line.reached_checkpoint_ids)
                        if has_single and rec.is_update_hand:
                            selected_line = line
                            break  # Fourth priority match
                if selected_line:
                    pass

                # Priority 5: Check for lines with ONLY is_confirm_hand (if needed)
                # if not selected_line:
                #     for line in task.checkpoint_ids:
                #         if any(item.name == 'is_confirm_hand' for item in line.reached_checkpoint_ids):
                #             if rec.is_confirm_hand:
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
            rec.message_post(body=_("Handover Completed"))
    def action_repeat_hand(self):
        for rec in self:
            rec.is_confirm_hand = False
            rec.is_complete_hand = False
            rec.is_complete_return_hand = True
            rec.message_post(body=_("Handover Repeated"))
    def action_confirm_hand(self):
        for rec in self:
            rec.is_confirm_hand = True
            all_tasks = rec.filtered_task_ids | rec.sub_tasks_ids
            for task in all_tasks:
                selected_line = None  # To store the correct line for execution

                # Priority 1: Check for lines with ALL THREE checkpoints
                for line in task.checkpoint_ids:
                    has_all_three = (
                            any(item.name == 'is_complete_return_hand' for item in line.reached_checkpoint_ids) and
                            any(item.name == 'is_confirm_hand' for item in line.reached_checkpoint_ids) and
                            any(item.name == 'is_update_hand' for item in line.reached_checkpoint_ids)
                    )
                    if has_all_three and rec.is_complete_return_hand and rec.is_confirm_hand and rec.is_update_hand:
                        selected_line = line
                        break  # Highest priority match
                if selected_line:
                    pass  # Skip lower priorities if match found

                # Priority 2: Check for lines with ORIGINAL TWO checkpoints
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_original_two = (
                                any(item.name == 'is_complete_return_hand' for item in line.reached_checkpoint_ids) and
                                any(item.name == 'is_confirm_hand' for item in line.reached_checkpoint_ids)
                        )
                        if has_original_two and rec.is_complete_return_hand and rec.is_confirm_hand:
                            selected_line = line
                            break  # Second priority match
                if selected_line:
                    pass

                # Priority 3: Check for lines with ONLY is_complete_return_hand
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_single = any(item.name == 'is_complete_return_hand' for item in line.reached_checkpoint_ids)
                        if has_single and rec.is_complete_return_hand:
                            selected_line = line
                            break  # Third priority match
                if selected_line:
                    pass

                # Priority 4: Check for lines with ONLY is_update_hand (NEW FIELD)
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_single = any(item.name == 'is_update_hand' for item in line.reached_checkpoint_ids)
                        if has_single and rec.is_update_hand:
                            selected_line = line
                            break  # Fourth priority match
                if selected_line:
                    pass

                # Priority 5: Check for lines with ONLY is_confirm_hand (if needed)
                # if not selected_line:
                #     for line in task.checkpoint_ids:
                #         if any(item.name == 'is_confirm_hand' for item in line.reached_checkpoint_ids):
                #             if rec.is_confirm_hand:
                #                 selected_line = line
                #                 break

                # Apply changes if any valid line found
                if selected_line:
                    task.all_milestone_id = selected_line.milestone_id.id
                    task.milestone_id = selected_line.milestone_id.id
                    task.stage_id = selected_line.stage_id.id

                    if task.partner_id and selected_line.milestone_id.mail_template_id:
                        task.action_send_email()
            rec.message_post(body=_(" Handover Confirmed "))

    def action_complete_compliance(self):
        for rec in self:
            rec._check_compliance_shareholder_ids()
            rec._check_shareholding()
            rec.is_complete_compliance = True
            all_tasks = rec.filtered_task_ids | rec.sub_tasks_ids
            for task in all_tasks:
                selected_line = None  # To store the correct line for execution

                # Priority 1: Check for lines with ALL THREE compliance checkpoints
                for line in task.checkpoint_ids:
                    has_all_three = (
                            any(item.name == 'is_complete_return_compliance' for item in
                                line.reached_checkpoint_ids) and
                            any(item.name == 'is_confirm_compliance' for item in line.reached_checkpoint_ids) and
                            any(item.name == 'is_update_compliance' for item in line.reached_checkpoint_ids)
                    )
                    if has_all_three and rec.is_complete_return_compliance and rec.is_confirm_compliance and rec.is_update_compliance:
                        selected_line = line
                        break  # Highest priority match
                if selected_line:
                    pass  # Skip lower priorities if match found

                # Priority 2: Check for lines with ORIGINAL TWO compliance checkpoints
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_original_two = (
                                any(item.name == 'is_complete_return_compliance' for item in
                                    line.reached_checkpoint_ids) and
                                any(item.name == 'is_confirm_compliance' for item in line.reached_checkpoint_ids)
                        )
                        if has_original_two and rec.is_complete_return_compliance and rec.is_confirm_compliance:
                            selected_line = line
                            break  # Second priority match
                if selected_line:
                    pass

                # Priority 3: Check for lines with ONLY is_complete_return_compliance
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_single = any(
                            item.name == 'is_complete_return_compliance' for item in line.reached_checkpoint_ids)
                        if has_single and rec.is_complete_return_compliance:
                            selected_line = line
                            break  # Third priority match
                if selected_line:
                    pass

                # Priority 4: Check for lines with ONLY is_update_compliance
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_single = any(item.name == 'is_update_compliance' for item in line.reached_checkpoint_ids)
                        if has_single and rec.is_update_compliance:
                            selected_line = line
                            break  # Fourth priority match
                if selected_line:
                    pass

                # Apply changes if any valid line found
                if selected_line:
                    task.all_milestone_id = selected_line.milestone_id.id
                    task.milestone_id = selected_line.milestone_id.id
                    task.stage_id = selected_line.stage_id.id
                    rec.state = 'c_in_progress'
                    if task.partner_id and selected_line.milestone_id.mail_template_id:
                        task.action_send_email()
            rec.message_post(body=_(" Compliance Completed "))
    def action_confirm_compliance(self):
        for rec in self:
            rec.is_confirm_compliance = True
            all_tasks = rec.filtered_task_ids | rec.sub_tasks_ids
            for task in all_tasks:
                selected_line = None  # To store the correct line for execution

                # Priority 1: Check for lines with ALL THREE compliance checkpoints
                for line in task.checkpoint_ids:
                    has_all_three = (
                            any(item.name == 'is_complete_return_compliance' for item in
                                line.reached_checkpoint_ids) and
                            any(item.name == 'is_confirm_compliance' for item in line.reached_checkpoint_ids) and
                            any(item.name == 'is_update_compliance' for item in line.reached_checkpoint_ids)
                    )
                    if has_all_three and rec.is_complete_return_compliance and rec.is_confirm_compliance and rec.is_update_compliance:
                        selected_line = line
                        break  # Highest priority match
                if selected_line:
                    pass  # Skip lower priorities if match found

                # Priority 2: Check for lines with ORIGINAL TWO compliance checkpoints
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_original_two = (
                                any(item.name == 'is_complete_return_compliance' for item in
                                    line.reached_checkpoint_ids) and
                                any(item.name == 'is_confirm_compliance' for item in line.reached_checkpoint_ids)
                        )
                        if has_original_two and rec.is_complete_return_compliance and rec.is_confirm_compliance:
                            selected_line = line
                            break  # Second priority match
                if selected_line:
                    pass

                # Priority 3: Check for lines with ONLY is_complete_return_compliance
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_single = any(
                            item.name == 'is_complete_return_compliance' for item in line.reached_checkpoint_ids)
                        if has_single and rec.is_complete_return_compliance:
                            selected_line = line
                            break  # Third priority match
                if selected_line:
                    pass

                # Priority 4: Check for lines with ONLY is_update_compliance
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_single = any(item.name == 'is_update_compliance' for item in line.reached_checkpoint_ids)
                        if has_single and rec.is_update_compliance:
                            selected_line = line
                            break  # Fourth priority match
                if selected_line:
                    pass

                # Apply changes if any valid line found
                if selected_line:
                    task.all_milestone_id = selected_line.milestone_id.id
                    task.milestone_id = selected_line.milestone_id.id
                    task.stage_id = selected_line.stage_id.id

                    if task.partner_id and selected_line.milestone_id.mail_template_id:
                        task.action_send_email()
            rec.message_post(body=_(" Compliance Confirmed "))
    def action_return_compliance(self):
        return {
            'name': _('Compliance Returned'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'return.project.wizard',
            'context': {'default_project_id': self.id, 'default_type': 'compliance'},
            'view_id': self.env.ref('freezoner_custom.project_return_form_view').id,
            'target': 'new',
        }
    def action_update_compliance(self):
        for rec in self:
            rec.is_complete_return_compliance = False
            rec.is_complete_compliance = True
            rec.is_second_complete_compliance_check = 2
            rec._check_compliance_shareholder_ids()
            rec._check_shareholding()
            all_tasks = rec.filtered_task_ids | rec.sub_tasks_ids
            for task in all_tasks:
                selected_line = None  # To store the correct line for execution

                # Priority 1: Check for lines with ALL THREE compliance checkpoints
                for line in task.checkpoint_ids:
                    has_all_three = (
                            any(item.name == 'is_complete_return_compliance' for item in
                                line.reached_checkpoint_ids) and
                            any(item.name == 'is_confirm_compliance' for item in line.reached_checkpoint_ids) and
                            any(item.name == 'is_update_compliance' for item in line.reached_checkpoint_ids)
                    )
                    if has_all_three and rec.is_complete_return_compliance and rec.is_confirm_compliance and rec.is_update_compliance:
                        selected_line = line
                        break  # Highest priority match
                if selected_line:
                    pass  # Skip lower priorities if match found

                # Priority 2: Check for lines with ORIGINAL TWO compliance checkpoints
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_original_two = (
                                any(item.name == 'is_complete_return_compliance' for item in
                                    line.reached_checkpoint_ids) and
                                any(item.name == 'is_confirm_compliance' for item in line.reached_checkpoint_ids)
                        )
                        if has_original_two and rec.is_complete_return_compliance and rec.is_confirm_compliance:
                            selected_line = line
                            break  # Second priority match
                if selected_line:
                    pass

                # Priority 3: Check for lines with ONLY is_complete_return_compliance
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_single = any(
                            item.name == 'is_complete_return_compliance' for item in line.reached_checkpoint_ids)
                        if has_single and rec.is_complete_return_compliance:
                            selected_line = line
                            break  # Third priority match
                if selected_line:
                    pass

                # Priority 4: Check for lines with ONLY is_update_compliance
                if not selected_line:
                    for line in task.checkpoint_ids:
                        has_single = any(item.name == 'is_update_compliance' for item in line.reached_checkpoint_ids)
                        if has_single and rec.is_update_compliance:
                            selected_line = line
                            break  # Fourth priority match
                if selected_line:
                    pass

                # Apply changes if any valid line found
                if selected_line:
                    task.all_milestone_id = selected_line.milestone_id.id
                    task.milestone_id = selected_line.milestone_id.id
                    task.stage_id = selected_line.stage_id.id

                    if task.partner_id and selected_line.milestone_id.mail_template_id:
                        task.action_send_email()
            rec.message_post(body=_(" Compliance Updated "))
    def action_repeat_compliance(self):
        for rec in self:
            rec.is_confirm_compliance = False
            rec.is_complete_compliance = False
            rec.is_complete_return_compliance = True
            rec.message_post(body=_("Handover Repeated"))


    @api.onchange('hand_partner_id', 'apply_visa')
    def _onchange_project_visa_application_ids(self):
        for rec in self:
            # Existing logic for adding records
            if rec.hand_partner_id and rec.hand_partner_id.contact_visa_application_ids:
                items = [
                    {'project_id': rec.id, 'partner_id': line.partner_id.id}
                    for line in rec.hand_partner_id.contact_visa_application_ids
                    if line.is_active
                ]
                items = list({(item['project_id'], item['partner_id']): item for item in items}.values())
                partner_ids = [item['partner_id'] for item in items]
                existing_records = self.env['project.visa.application'].sudo().search([
                    ('project_id', '=', rec.id),
                    ('partner_id', 'in', partner_ids)
                ])
                existing_partner_ids = existing_records.mapped('partner_id.id')
                items_to_create = [item for item in items if item['partner_id'] not in existing_partner_ids]
                if items_to_create:
                    self.env['project.visa.application'].sudo().create(items_to_create)

            # Logic for creating a record when apply_visa is True
            if rec.apply_visa and rec.hand_partner_id:
                existing_records = rec.project_visa_application_ids.filtered(
                    lambda v: v.partner_id == rec.hand_partner_id
                )
                if not existing_records:
                    self.env['project.visa.application'].sudo().create({
                        'project_id': rec.id,
                        'partner_id': rec.hand_partner_id.id,
                    })

            # NEW LOGIC: Delete records from One2many field when apply_visa is False
            if not rec.apply_visa and rec.hand_partner_id:
                # Find records in project_visa_application_ids linked to hand_partner_id
                records_to_delete = rec.project_visa_application_ids.filtered(
                    lambda v: v.partner_id == rec.hand_partner_id
                )
                # Unlink (delete) them from the One2many field
                rec.project_visa_application_ids = rec.project_visa_application_ids - records_to_delete

    @api.depends('license_authority_id')
    def _onchange_license_activity_ids(self):
        for rec in self:
            if self.license_authority_id:
                activity = self.env['license.activity'].sudo().search(
                    [('license_authority_id', '=', self.license_authority_id.id)])
                rec.all_license_activity_ids = [(6, 0, activity.ids)]
            else:
                activity = self.env['license.activity'].sudo().search([])
                rec.all_license_activity_ids = [(6, 0, activity.ids)]

    @api.onchange('license_authority_id')
    def _onchange_license_authority_id(self):
        if self.license_authority_id:
            return {
                'domain': {
                    'license_activity_ids': [
                        ('license_authority_id', '=', self.license_authority_id.id)
                    ]
                }
            }
        else:
            return {
                'domain': {
                    'license_activity_ids': []
                }
            }

    @api.depends('proposed_name1', 'proposed_name2', 'proposed_name3', 'initial_company_info')
    def get_full_name(self):
        for rec in self:
            if rec.initial_company_info:
                rec.full_name = " ".join(filter(None, [rec.proposed_name1, rec.proposed_name2, rec.proposed_name3]))
            else:
                rec.full_name = ''

    @api.depends('is_create_individual_profile', 'hand_partner_first_name', 'hand_partner_middle_name', 'hand_partner_last_name')
    def get_individual_full_name(self):
        for rec in self:
            if rec.is_create_individual_profile:
                rec.individual_full_name = " ".join(filter(None, [rec.hand_partner_first_name, rec.hand_partner_middle_name, rec.hand_partner_last_name]))
            else:
                rec.individual_full_name = ''

    @api.depends('compliance_shareholder_ids.shareholding')
    def get_shareholding_total(self):
        for rec in self:
            rec.shareholding_total = sum(line.shareholding for line in rec.compliance_shareholder_ids)

    @api.depends('price_per_share', 'total_number_shares')
    def _get_share_value(self):
        for rec in self:
            rec.total_share_value = rec.price_per_share * rec.total_number_shares

    # @api.constrains('compliance_shareholder_ids', 'hand_partner_id', 'total_number_shares')
    def _check_shareholding(self):
        for rec in self:
            if rec.shareholding_total != rec.total_number_shares:
                raise ValidationError(
                    'Please check shareholding: Total shareholding (%s) must equal total number of shares (%s).'
                    % (rec.shareholding_total, rec.total_number_shares)
                )

    def _add_contact_to_parent_partner(self, contact_id):
        """
        Add the given contact_id to hand_partner_id.parent_partner_ids.
        """
        for record in self:
            if record.hand_partner_id:
                # Ensure parent_partner_ids is updated with the new contact_id
                parent_partners = record.hand_partner_id.parent_partner_ids
                if contact_id not in parent_partners.ids:
                    record.hand_partner_id.write({
                        'parent_partner_ids': [(4, contact_id)]  # Add the contact_id
                    })

    def handle_compliance_updates(self, vals):
        """Handles compliance updates including deletions and changes in hand_contact_id or hand_partner_id."""

        def delete_related_shareholder_data(contact_ids):
            if contact_ids:
                related_records = self.env['shareholder.data'].search([
                    ('project_id', '=', self.id),
                    ('partner_id', 'in', contact_ids)
                ])
                if related_records:
                    related_records.unlink()

        # Handle deletions in `compliance_shareholder_ids`
        if 'compliance_shareholder_ids' in vals:
            for shareholder in vals['compliance_shareholder_ids']:
                operation = shareholder[0]  # Operation type: 0=create, 1=update, 2=delete
                shareholder_id = shareholder[1]

                if operation == 2:  # Delete operation
                    # Find the related `res.partner.shareholder` record
                    deleted_record = self.env['res.partner.shareholder'].browse(shareholder_id)
                    if deleted_record.exists() and deleted_record.contact_id:
                        # Delete related `shareholder.data` records
                        delete_related_shareholder_data([deleted_record.contact_id.id])

    def _create_project_visa_applications(self):
        for rec in self:
            for line in rec.compliance_shareholder_ids.filtered(lambda l: l.apply_visa and l.contact_id):
                # Project Visa Application
                existing_project_visa = self.env['project.visa.application'].sudo().search([
                    ('project_id', '=', rec.id),
                    ('partner_id', '=', line.contact_id.id)
                ], limit=1)
                if not existing_project_visa:
                    self.env['project.visa.application'].sudo().create({
                        'project_id': rec.id,
                        'partner_id': line.contact_id.id,
                    })

                # Contact Visa Application
                existing_contact_visa = self.env['contact.visa.application'].sudo().search([
                    ('parent_id', '=', rec.hand_partner_id.id),
                    ('partner_id', '=', line.contact_id.id)
                ], limit=1)
                if not existing_contact_visa:
                    self.env['contact.visa.application'].sudo().create({
                        'parent_id': rec.hand_partner_id.id,
                        'partner_id': line.contact_id.id,
                    })

    def sync_visa_applications(self):
        ProjectVisa = self.env['project.visa.application'].sudo()
        ContactVisa = self.env['contact.visa.application'].sudo()

        for rec in self:
            # Existing project visa applications for this project
            existing_project_visas = ProjectVisa.search([('project_id', '=', rec.id)])
            existing_project_partners = existing_project_visas.mapped('partner_id')

            for line in rec.compliance_shareholder_ids:
                partner = line.contact_id
                if line.apply_visa:
                    if partner not in existing_project_partners:
                        ProjectVisa.create({
                            'project_id': rec.id,
                            'partner_id': partner.id,
                        })
                else:
                    # If apply_visa is False, remove it if exists
                    visa_to_remove = existing_project_visas.filtered(lambda v: v.partner_id.id == partner.id)
                    if visa_to_remove:
                        visa_to_remove.unlink()

            # Process Contact Visa Applications if hand_partner_id is set
            if rec.hand_partner_id:
                existing_contact_visas = ContactVisa.search([('parent_id', '=', rec.hand_partner_id.id)])
                existing_contact_partners = existing_contact_visas.mapped('partner_id')

                current_partners = rec.compliance_shareholder_ids.filtered(lambda l: l.apply_visa).mapped('contact_id')
                to_add = current_partners - existing_contact_partners
                to_remove = existing_contact_visas.filtered(lambda v: v.partner_id not in current_partners)

                if to_add:
                    ContactVisa.create([{
                        'parent_id': rec.hand_partner_id.id,
                        'partner_id': partner.id,
                    } for partner in to_add])

                if to_remove:
                    to_remove.unlink()

    def write(self, vals):
        if 'compliance_shareholder_ids' in vals:
            self.sync_visa_applications()
        res = super(Project, self).write(vals)
        # Check if the `unlink` operation is explicitly called
        if 'compliance_shareholder_ids' in vals:
            self.sync_visa_applications()
        is_unlink_action = 'compliance_shareholder_ids' in vals and any(
            shareholder[0] == 2 for shareholder in vals['compliance_shareholder_ids']
        )
        if is_unlink_action:
            self.handle_compliance_updates(vals)
        # Validate the shareholding
        # total_shareholding = sum(line.shareholding for line in self.compliance_shareholder_ids)
        # if total_shareholding > 0.0 and total_shareholding != self.total_number_shares:
        #     raise ValidationError(
        #         'Please check shareholding: Total shareholding (%s) must equal total number of shares (%s).'
        #         % (total_shareholding, self.total_number_shares)
        #     )

        print(' valssssssssss ', vals)
        if 'hand_partner_first_name' in vals or 'hand_partner_middle_name' in vals or 'hand_partner_last_name' in vals:
            for rec in self:
                individual_full_name = " ".join(filter(None, [
                    vals.get('hand_partner_first_name', rec.hand_partner_first_name),
                    vals.get('hand_partner_middle_name', rec.hand_partner_middle_name),
                    vals.get('hand_partner_last_name', rec.hand_partner_last_name)
                ]))

                print(' totoooooooo  -------->  ', rec.hand_partner_id, rec.is_create_individual_profile)
                if not rec.hand_partner_id and rec.is_create_individual_profile:
                    # If no partner exists, create a new one with the individual_full_name
                    individual_partner = self.env['res.partner'].sudo().create({
                        'name': individual_full_name,
                        'company_type': 'person',
                    })
                    # Assign the newly created partner to the hand_partner_id
                    vals['hand_partner_id'] = individual_partner.id
                    rec.hand_partner_id = individual_partner.id

                    print(' sofaaaaaaaaa  -------->  ', individual_full_name, individual_partner)


        if 'proposed_name1' in vals or 'proposed_name2' in vals or 'proposed_name3' in vals:
            for rec in self:
                # Manually compute the full name based on the proposed names
                full_name = " ".join(filter(None, [
                    vals.get('proposed_name1', rec.proposed_name1),
                    vals.get('proposed_name2', rec.proposed_name2),
                    vals.get('proposed_name3', rec.proposed_name3)
                ]))
                if not rec.hand_partner_id and rec.initial_company_info:
                    # If no partner exists, create a new one with the full_name
                    partner = self.env['res.partner'].sudo().create({
                        'name': full_name,
                        'company_type': 'company',
                    })
                    # Assign the newly created partner to the hand_partner_id
                    vals['hand_partner_id'] = partner.id
                    rec.hand_partner_id = partner.id

        # if 'compliance_shareholder_ids' in vals or 'is_visa_application' in vals:
        #     self._create_project_visa_applications()
        if 'compliance_shareholder_ids' in vals:
            print(' xxxxxxxxxxxx   ', vals['compliance_shareholder_ids'])

            # self._create_project_visa_applications(vals['compliance_shareholder_ids'])
            for shareholder in vals['compliance_shareholder_ids']:
                operation = shareholder[0]  # Operation type: 0=create, 1=update, 2=delete
                shareholder_vals = shareholder[2]  # The dictionary of field values

                if operation in [0, 1]:  # Create or update operations
                    contact_id = shareholder_vals.get('contact_id')
                    print(' contact_id ', contact_id)
                    if contact_id:
                        self._add_contact_to_parent_partner(contact_id)
                        partner_id = self.env['res.partner'].browse(shareholder_vals.get('partner_id'))
                        contact_name = self.env['res.partner'].browse(shareholder_vals.get('contact_id')).name
                        relationship_ids = shareholder_vals.get('relationship_ids', [])
                        extracted_ids = []
                        if relationship_ids and isinstance(relationship_ids[0], list) and relationship_ids[0][0] == 6:
                            extracted_ids = relationship_ids[0][2]  # Extract the list of IDs

                        # Fetch names of relationships
                        relationship_names = self.env['business.relationships'].browse(extracted_ids).mapped('name')

                        value = (shareholder_vals.get('shareholding') or 0.0) * self.price_per_share
                        self.env['shareholder.data'].sudo().create({
                            'partner_id': contact_id,
                            'contact_id': partner_id.id,
                            'name': contact_name,
                            'position': ', '.join(relationship_names),  # Use names instead of IDs
                            'relationship_ids': relationship_ids,
                            'shares': shareholder_vals.get('shareholding'),
                            'total': value,
                            'project_id': shareholder_vals.get('project_id'),
                        })
                        if 'address_ids' in shareholder_vals:
                            for address in shareholder_vals['address_ids']:
                                operation = address[0]  # Operation type: 0=create, 1=update, 2=delete
                                address_vals = address[2]  # The dictionary of field values

                                if operation in [0, 1]:  # Create or update operations
                                    # Search for an existing address with the same field values
                                    existing_address = self.env['res.partner.address'].sudo().search([
                                        ('partner_id', '=', contact_id),
                                        ('street', '=', address_vals.get('street')),
                                        ('street2', '=', address_vals.get('street2')),
                                        ('zip', '=', address_vals.get('zip')),
                                        ('city', '=', address_vals.get('city')),
                                        ('state_id', '=', address_vals.get('state_id')),
                                        ('country_id', '=', address_vals.get('country_id')),
                                    ], limit=1)

                                    if not existing_address:  # Create only if no match is found
                                        self.env['res.partner.address'].sudo().create({
                                            'partner_id': contact_id,
                                            'type': address_vals.get('type', 'current'),
                                            # Default to 'current' if not provided
                                            'street': address_vals.get('street'),
                                            'street2': address_vals.get('street2'),
                                            'zip': address_vals.get('zip'),
                                            'city': address_vals.get('city'),
                                            'state_id': address_vals.get('state_id'),
                                            'country_id': address_vals.get('country_id'),
                                        })

                        hand_partner_id = shareholder_vals.get(
                            'partner_id')  # Assuming hand_partner_id is passed in vals
                        if hand_partner_id:
                            hand_partner = self.env['res.partner'].browse(hand_partner_id)
                            if hand_partner:
                                hand_partner.write({
                                    'parent_partner_ids': [(4, contact_id)]  # Add contact_id to parent_partner_ids
                                })

        return res

    def _check_compliance_shareholder_ids(self):
        for rec in self:
            if rec.partner_id.id != rec.hand_partner_id.id and rec.compliance_shareholder_ids and not any(
                    line.contact_id.id == rec.partner_id.id for line in rec.compliance_shareholder_ids
            ):
                raise ValidationError(
                    'The project customer must exist in at least one compliance shareholder line.'
                )
