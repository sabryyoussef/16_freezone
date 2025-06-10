from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
from collections import defaultdict

class Task(models.Model):
    _inherit = 'project.task'

    # Basic Fields
    is_done = fields.Boolean(related='stage_id.is_done', store=True)
    is_subtask = fields.Boolean(copy=False)
    today_date = fields.Datetime(compute='_compute_today_date', store=True)
    
    # Document Fields
    document_ids = fields.Many2many(
        'res.partner.document',
        compute='_compute_document_ids',
        store=True
    )
    task_document_ids = fields.One2many(
        'res.partner.document',
        'task_id',
        string='Task Documents'
    )
    document_count = fields.Integer(
        compute='_compute_document_count',
        string='Document Count',
        store=True
    )
    document_type_ids = fields.One2many(
        'task.document.lines',
        'task_id',
        string='Document Types'
    )
    document_required_type_ids = fields.One2many(
        'task.document.required.lines',
        'task_id',
        string='Required Documents'
    )
    document_required_readonly_type_ids = fields.One2many(
        'task.document.required.lines',
        'task_id',
        compute='_compute_document_required_readonly_type_ids',
        string='Required Documents (Readonly)'
    )
    document_required_type_processing_ids = fields.One2many(
        'task.document.required.lines',
        'task_id',
        string='Processing Documents'
    )

    # Payment Fields
    payment_state = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('reversed', 'Reversed'),
        ('invoicing_legacy', 'Invoicing App Legacy'),
    ], string='Payment Status',
        related='invoice_id.payment_state',
        store=True
    )
    invoice_id = fields.Many2one(
        'account.move',
        compute='_compute_invoice_id',
        store=True
    )

    # Stage Management
    stage_id = fields.Many2one(
        'project.task.type',
        string='Stage',
        compute='_compute_stage_id',
        store=True,
        readonly=True,
        ondelete='restrict',
        tracking=True,
        index=True,
        default=lambda self: self._get_default_stage_id(),
        group_expand='_read_group_stage_ids',
        domain="[('project_ids', '=', project_id)]",
        copy=False
    )

    # Computed Methods
    @api.depends('create_date')
    def _compute_today_date(self):
        for task in self:
            task.today_date = fields.Datetime.now()

    @api.depends('partner_id')
    def _compute_document_ids(self):
        for task in self:
            task.document_ids = self.env['res.partner.document'].sudo().search([
                ('partner_id', '=', task.partner_id.id)
            ]).ids

    def _compute_document_count(self):
        for task in self:
            documents = self.env['res.partner.document'].sudo().search([
                '|',
                ('project_id', '=', task.project_id.id),
                ('task_ids', 'in', task.id)
            ])
            
            # Add documents from required types
            for line in task.document_required_type_ids:
                documents += self.env['res.partner.document'].sudo().search([
                    ('partner_id', '=', task.partner_id.id),
                    ('type_id', '=', line.document_id.id),
                    ('issue_date', '=', line.issue_date)
                ])
            
            # Add documents from document types
            for line in task.document_type_ids:
                documents += self.env['res.partner.document'].sudo().search([
                    ('partner_id', '=', task.partner_id.id),
                    ('type_id', '=', line.document_id.id),
                    ('issue_date', '=', line.issue_date)
                ])
            
            task.document_count = len(documents)

    @api.depends('sale_order_id')
    def _compute_invoice_id(self):
        for task in self:
            task.invoice_id = task.sale_order_id.invoice_ids.filtered(
                lambda inv: inv.state != 'cancel'
            )[:1]

    @api.depends('project_id', 'child_ids.stage_id', 'stage_id')
    def _compute_stage_id(self):
        for task in self:
            if task.project_id:
                if task.project_id not in task.stage_id.project_ids:
                    task.stage_id = task.stage_find(task.project_id.id, [('fold', '=', False)])
                
                if task.child_ids:
                    if any(child.stage_id.name == 'In Progress' for child in task.child_ids):
                        task.stage_id = self.env.ref('freezoner_custom.stage_in_progress').id
                    elif all(child.stage_id.name == 'Done' for child in task.child_ids):
                        task.stage_id = self.env.ref('freezoner_custom.stage_done').id
                    elif all(child.stage_id.name == 'New' for child in task.child_ids):
                        task.stage_id = self.env.ref('freezoner_custom.stage_new').id
            else:
                task.stage_id = False

    def _compute_document_required_readonly_type_ids(self):
        for task in self:
            task.document_required_readonly_type_ids = task.document_required_type_ids

    # Action Methods
    def action_done(self):
        for task in self:
            task.stage_id = self.env.ref('freezoner_custom.stage_done').id
            if task.child_ids:
                task.child_ids.action_done()

    def next_stage(self):
        for task in self:
            current_stage = task.stage_id
            stages = self.env['project.task.type'].sudo().search([
                ('project_ids', '=', task.project_id.id)
            ])
            
            if current_stage.fold:
                raise ValidationError(_('Stage is folded!'))
            
            next_stage = stages.sorted(key=lambda s: s.sequence).filtered(
                lambda s: s.sequence > current_stage.sequence
            )
            
            if next_stage:
                task.write({'stage_id': next_stage[0].id})
            else:
                raise ValidationError(_('There is no next stage based on sequence!'))

    def previous_stage(self):
        for task in self:
            current_stage = task.stage_id
            stages = self.env['project.task.type'].sudo().search([
                ('project_ids', '=', task.project_id.id)
            ])
            
            if current_stage.sequence == 1:
                raise ValidationError(_('Stage is first!'))
            
            previous_stage = stages.sorted(key=lambda s: s.sequence).filtered(
                lambda s: s.sequence < current_stage.sequence
            )
            
            if previous_stage:
                task.write({'stage_id': previous_stage[0].id})
            else:
                raise ValidationError(_('There is no previous stage based on sequence!'))

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
            'target': 'current',
            'view_id': self.env.ref('project.edit_project').id,
        }

    def action_view_document(self):
        self.ensure_one()
        documents = self.env['res.partner.document'].sudo().search([
            '|',
            ('project_id', '=', self.project_id.id),
            ('task_ids', 'in', self.id)
        ])
        
        # Add documents from required types
        for line in self.document_required_type_ids:
            documents += self.env['res.partner.document'].sudo().search([
                ('partner_id', '=', self.partner_id.id),
                ('type_id', '=', line.document_id.id),
                ('issue_date', '=', line.issue_date)
            ])
        
        # Add documents from document types
        for line in self.document_type_ids:
            documents += self.env['res.partner.document'].sudo().search([
                ('partner_id', '=', self.partner_id.id),
                ('type_id', '=', line.document_id.id),
                ('issue_date', '=', line.issue_date)
            ])
        
        action = self.env.ref('client_documents.contacts_documents_action').read()[0]
        if len(documents) > 1:
            action['domain'] = [('id', 'in', documents.ids)]
        elif len(documents) == 1:
            action['views'] = [(
                self.env.ref('client_documents.client_documents_form_views').id,
                'form'
            )]
            action['res_id'] = documents.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def open_mail(self):
        return {
            'res_model': 'mail.compose.message',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env.ref('mail.email_compose_message_wizard_form').id,
            'target': 'new'
        }

    # Helper Methods
    def _get_default_stage_id(self):
        project_id = self.env.context.get('default_project_id')
        if not project_id:
            return False
        return self.stage_find(project_id, [('fold', '=', False)])

    def _read_group_stage_ids(self, stages, domain, order):
        project_id = self.env.context.get('default_project_id')
        if project_id:
            return stages.filtered(lambda s: project_id in s.project_ids)
        return stages

    # CRUD Methods
    @api.model_create_multi
    def create(self, vals_list):
        # Create records in batch
        return super().create(vals_list)

    def write(self, vals):
        # Write records in batch
        return super().write(vals)

class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    def _get_default_project_ids(self):
        return self.env['project.project'].search([('active', '=', True)]).ids

    project_ids = fields.Many2many(
        'project.project',
        'project_task_type_rel',
        'type_id',
        'project_id',
        string='Projects',
        default=_get_default_project_ids
    ) 