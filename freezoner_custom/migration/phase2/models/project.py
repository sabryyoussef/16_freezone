from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

PAYMENT_STATE_SELECTION = [
    ('not_paid', 'Not Paid'),
    ('paid_visa', 'Paid Visa'),
    ('paid_bank', 'Paid Bank'),
    ('partial', 'Partially Paid'),
]

class Project(models.Model):
    """
    Project Model Extension
    Extends the base project model with additional fields and functionality
    for enhanced project management
    """
    _inherit = 'project.project'
    _order = 'state'

    # Project Fields
    project_field_ids = fields.One2many(
        'project.partner.fields',
        'project_id',
        string='Project Partner Fields',
        copy=False
    )
    
    sale_id = fields.Many2one(
        'sale.order',
        string='Sales Order',
        tracking=True,
        help='Related sales order'
    )
    
    is_project_template = fields.Boolean(
        string='Is Template',
        copy=False,
        tracking=True,
        default=False,
        help='Indicates if this project is a template'
    )
    
    state = fields.Selection([
        ('a_template', 'Template'),
        ('b_new', 'New Projects'),
        ('c_in_progress', 'In Progress'),
        ('d_done', 'Done'),
        ('on_hold', 'On Hold'),
        ('e_cancel', 'Cancelled'),
    ], string="Status",
        default='b_new',
        tracking=True,
        copy=False,
        readonly=True,
        group_expand='_expand_states',
        compute="_compute_project_state",
        store=True,
        help='Current status of the project'
    )

    # Document Relations
    required_documents_ids = fields.One2many(
        'documents.document',
        'required_project_id',
        string='Required Documents'
    )
    
    deliverable_documents_ids = fields.One2many(
        'documents.document',
        'deliverable_project_id',
        string='Deliverable Documents'
    )
    
    document_ids = fields.One2many(
        'documents.document',
        'project_id',
        string='Project Documents'
    )
    
    document_type_ids = fields.One2many(
        'task.document.lines',
        'project_id',
        string='Document Types'
    )
    
    document_required_type_ids = fields.One2many(
        'task.document.required.lines',
        'project_id',
        string='Required Document Types'
    )
    
    document_request_ids = fields.One2many(
        'documents.request_wizard',
        'project_id',
        string='Document Requests'
    )

    # Partner Relations
    project_partner_ids = fields.Many2many(
        'res.partner',
        relation='project_partner_rel',
        column1='project_id',
        column2='partner_id',
        string='Project Partners',
        compute='_compute_project_partners',
        store=True
    )
    
    partner_ids = fields.Many2many(
        'res.partner',
        string='All Customers',
        compute='_compute_partner_ids',
        store=True
    )

    # Task Relations
    filtered_task_ids = fields.Many2many(
        'project.task',
        string='Tasks',
        compute='_compute_filtered_task_ids',
        store=True
    )
    
    sub_tasks_ids = fields.Many2many(
        'project.task',
        relation='project_subtask_rel',
        column1='project_id',
        column2='task_id',
        string='Sub Tasks',
        compute='_compute_sub_tasks_ids',
        store=True
    )
    
    subtasks_count = fields.Integer(
        string='Sub Tasks Count',
        compute='_compute_subtasks_count',
        store=True
    )

    # Product Relations
    product_ids = fields.Many2many(
        'product.product',
        string='Products'
    )
    
    project_product_ids = fields.One2many(
        'project.project.products',
        'project_id',
        string='Project Products'
    )

    # Payment Fields
    payment_state = fields.Selection(
        selection=PAYMENT_STATE_SELECTION,
        string='Payment Status',
        compute='_compute_payment_state',
        store=True
    )
    
    sale_payment_status = fields.Char(
        string='Sale Payment Status',
        compute='_compute_payment_status',
        store=True
    )
    
    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        compute='_compute_invoice_id',
        store=True
    )

    # Date Fields
    today_date = fields.Datetime(
        string='Today',
        compute='_compute_today_date'
    )
    
    date_start = fields.Date(
        string='Start Date',
        compute='_compute_date_start',
        store=True
    )

    # Document Status Fields
    is_complete_return_required = fields.Boolean(
        string='Required Document Complete',
        copy=False
    )
    
    is_confirm_required = fields.Boolean(
        string='Required Document Confirm',
        copy=False
    )
    
    is_complete_return_deliverable = fields.Boolean(
        string='Deliverable Document Complete',
        copy=False
    )
    
    is_confirm_deliverable = fields.Boolean(
        string='Deliverable Document Confirm',
        copy=False
    )
    
    is_complete_return_partner_fields = fields.Boolean(
        string='Partner Fields Complete',
        copy=False
    )
    
    is_confirm_partner_fields = fields.Boolean(
        string='Partner Fields Confirm',
        copy=False
    )

    # Update Status Fields
    is_second_complete_partner_fields_check = fields.Integer(
        string='Second Complete Partner Fields Check',
        copy=False,
        default=0
    )
    
    is_update_partner_fields = fields.Boolean(
        string='Update Partner Fields',
        copy=False
    )
    
    is_second_complete_deliverable_check = fields.Integer(
        string='Second Complete Deliverable Check',
        copy=False,
        default=0
    )
    
    is_update_deliverable = fields.Boolean(
        string='Update Deliverable',
        copy=False
    )
    
    is_second_complete_required_check = fields.Integer(
        string='Second Complete Required Check',
        copy=False,
        default=0
    )
    
    is_update_required = fields.Boolean(
        string='Update Required',
        copy=False
    )

    # Completion Status Fields
    is_complete_return_hand = fields.Boolean(
        string='Handover Complete',
        copy=False
    )
    
    is_complete_deliverable = fields.Boolean(
        string='Complete Deliverable',
        copy=False
    )
    
    is_complete_required = fields.Boolean(
        string='Complete Required',
        copy=False
    )
    
    is_complete_partner_fields = fields.Boolean(
        string='Complete Partner Fields',
        copy=False
    )

    # User Permission Fields
    is_check_current_user = fields.Boolean(
        compute='_compute_is_check_current_user'
    )
    
    is_current_user_project_manager = fields.Boolean(
        compute='_compute_is_current_user_project_manager'
    )
    
    is_current_user_project_admin = fields.Boolean(
        compute='_compute_is_current_user_project_admin'
    )
    
    is_current_user_project_task_assignee = fields.Boolean(
        compute='_compute_is_current_user_project_task_assignee'
    )

    # Update Check Fields
    is_update_required_check = fields.Boolean(
        compute='_compute_is_update_required_check'
    )
    
    is_update_deliverable_check = fields.Boolean(
        compute='_compute_is_update_deliverable_check'
    )
    
    is_update_partner_fields_check = fields.Boolean(
        compute='_compute_is_update_partner_fields_check'
    )

    # Computed Methods
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
                        continue
                    else:
                        project.state = 'b_new'
                else:
                    project.state = 'b_new'

    @api.model
    def _expand_states(self, states, domain, order):
        return ['a_template', 'b_new', 'c_in_progress', 'd_done', 'on_hold', 'e_cancel']

    @api.depends('compliance_shareholder_ids', 'partner_id')
    def _compute_project_partners(self):
        for rec in self:
            partners = rec.compliance_shareholder_ids.mapped('contact_id')
            if rec.partner_id:
                partners += rec.partner_id
            rec.project_partner_ids = partners

    @api.depends('project_partner_ids')
    def _compute_partner_ids(self):
        for rec in self:
            rec.partner_ids = rec.project_partner_ids

    @api.depends('task_ids')
    def _compute_filtered_task_ids(self):
        for rec in self:
            rec.filtered_task_ids = rec.task_ids.filtered(lambda t: not t.parent_id)

    @api.depends('task_ids')
    def _compute_sub_tasks_ids(self):
        for rec in self:
            rec.sub_tasks_ids = rec.task_ids.filtered(lambda t: t.parent_id)

    @api.depends('sub_tasks_ids')
    def _compute_subtasks_count(self):
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
                rec.sale_payment_status = False

    @api.depends('create_date')
    def _compute_date_start(self):
        for rec in self:
            rec.date_start = rec.create_date.date() if rec.create_date else False

    @api.depends('invoice_id')
    def _compute_payment_state(self):
        for rec in self:
            if not rec.invoice_id:
                rec.payment_state = 'not_paid'
            elif rec.invoice_id.payment_state == 'paid':
                if rec.invoice_id.payment_method == 'visa':
                    rec.payment_state = 'paid_visa'
                else:
                    rec.payment_state = 'paid_bank'
            elif rec.invoice_id.payment_state == 'partial':
                rec.payment_state = 'partial'
            else:
                rec.payment_state = 'not_paid'

    def _compute_today_date(self):
        for rec in self:
            rec.today_date = fields.Datetime.now()

    @api.depends('sale_order_id')
    def _compute_invoice_id(self):
        for rec in self:
            if rec.sale_order_id:
                rec.invoice_id = rec.sale_order_id.invoice_ids.filtered(lambda inv: inv.state == 'posted')[:1]
            else:
                rec.invoice_id = False

    # User Permission Methods
    @api.depends_context('uid')
    def _compute_is_current_user_project_task_assignee(self):
        current_user_id = self.env.uid
        for rec in self:
            rec.is_current_user_project_task_assignee = any(
                current_user_id in task.user_ids.ids for task in rec.filtered_task_ids
            )

    @api.depends_context('uid')
    def _compute_is_current_user_project_manager(self):
        for rec in self:
            rec.is_current_user_project_manager = (self.env.user.id == rec.user_id.id)

    @api.depends_context('uid')
    def _compute_is_current_user_project_admin(self):
        is_admin = self.env.user.has_group('project.group_project_manager')
        for rec in self:
            rec.is_current_user_project_admin = is_admin

    @api.depends_context('uid')
    def _compute_is_check_current_user(self):
        is_admin = self.env.user.has_group('project.group_project_manager')
        for rec in self:
            rec.is_check_current_user = is_admin or (self.env.user.id != rec.user_id.id)

    # Update Check Methods
    @api.depends('is_complete_return_partner_fields', 'is_complete_partner_fields', 'is_confirm_partner_fields')
    def _compute_is_update_partner_fields_check(self):
        for rec in self:
            rec.is_update_partner_fields_check = (
                rec.is_complete_return_partner_fields and 
                not rec.is_complete_partner_fields and 
                not rec.is_confirm_partner_fields and
                (rec.is_current_user_project_task_assignee or rec.is_current_user_project_admin)
            )

    @api.depends('is_complete_return_deliverable', 'is_complete_deliverable', 'is_confirm_deliverable')
    def _compute_is_update_deliverable_check(self):
        for rec in self:
            rec.is_update_deliverable_check = (
                rec.is_complete_return_deliverable and 
                not rec.is_complete_deliverable and 
                not rec.is_confirm_deliverable and
                (rec.is_current_user_project_task_assignee or rec.is_current_user_project_admin)
            )

    @api.depends('is_complete_return_required', 'is_complete_required', 'is_confirm_required')
    def _compute_is_update_required_check(self):
        for rec in self:
            rec.is_update_required_check = (
                rec.is_complete_return_required and 
                not rec.is_complete_required and 
                not rec.is_confirm_required and
                (rec.is_current_user_project_manager or rec.is_current_user_project_admin)
            )

    # Action Methods
    def action_request_required_documents(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Required Documents',
            'view_mode': 'form',
            'res_model': 'required.documents.wizard',
            'target': 'new',
            'context': {'default_project_id': self.id},
        }

    def action_view_tasks(self):
        return {
            'name': _('Tasks'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'view_mode': 'tree,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'create': True}
        }

    def action_view_subtasks(self):
        return {
            'name': _('Sub Tasks'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.sub_tasks_ids.ids)],
            'context': {'create': False}
        }

    def action_view_document(self):
        return {
            'name': _('Documents'),
            'type': 'ir.actions.act_window',
            'res_model': 'documents.document',
            'view_mode': 'tree,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'create': True}
        }

    # State Change Methods
    def action_in_progress(self):
        self.ensure_one()
        if self.state == 'b_new':
            self.write({'state': 'c_in_progress'})
            self.message_post(body=_('Project moved to In Progress'))
        return True

    def action_done(self):
        self.ensure_one()
        if self.state in ['b_new', 'c_in_progress']:
            self.write({'state': 'd_done'})
            self.message_post(body=_('Project marked as Done'))
        return True

    def action_onhold(self):
        self.ensure_one()
        if self.state not in ['d_done', 'e_cancel']:
            self.write({'state': 'on_hold'})
            self.message_post(body=_('Project put On Hold'))
        return True

    def action_cancel(self):
        self.ensure_one()
        if self.state != 'e_cancel':
            self.write({'state': 'e_cancel'})
            self.message_post(body=_('Project Cancelled'))
        return True

    def action_new(self):
        self.ensure_one()
        if self.state in ['on_hold', 'e_cancel']:
            self.write({'state': 'b_new'})
            self.message_post(body=_('Project reset to New'))
        return True

    def action_template(self):
        self.ensure_one()
        self.write({'is_project_template': True, 'state': 'a_template'})
        self.message_post(body=_('Project converted to Template'))
        return True

    # Document Management Methods
    def action_confirm_partner_fields(self):
        self.ensure_one()
        self.write({'is_confirm_partner_fields': True})
        self._process_partner_fields_checkpoints()
        return True

    def action_return_partner_fields(self):
        self.ensure_one()
        self.write({
            'is_complete_return_partner_fields': False,
            'is_confirm_partner_fields': False,
            'is_update_partner_fields': False
        })
        return True

    def action_update_partner_fields(self):
        self.ensure_one()
        self.write({'is_update_partner_fields': True})
        self._process_partner_fields_checkpoints()
        return True

    def action_complete_partner_fields(self):
        self.ensure_one()
        self.write({'is_complete_partner_fields': True})
        self._process_partner_fields_checkpoints()
        return True

    def _process_partner_fields_checkpoints(self):
        """Process checkpoints for partner fields"""
        self.ensure_one()
        all_tasks = self.filtered_task_ids | self.sub_tasks_ids
        for task in all_tasks:
            for line in task.checkpoint_ids:
                if any(item.name in [
                    'is_complete_return_partner_fields',
                    'is_confirm_partner_fields',
                    'is_update_partner_fields'
                ] for item in line.reached_checkpoint_ids):
                    if self._check_partner_fields_conditions(line):
                        line.action_reach_checkpoint()

    def _check_partner_fields_conditions(self, line):
        """Check if conditions are met for partner fields checkpoint"""
        self.ensure_one()
        conditions = {
            'is_complete_return_partner_fields': self.is_complete_return_partner_fields,
            'is_confirm_partner_fields': self.is_confirm_partner_fields,
            'is_update_partner_fields': self.is_update_partner_fields
        }
        return all(conditions.get(item.name, False) for item in line.reached_checkpoint_ids)

    # Model Methods
    @api.model
    def create(self, vals):
        if vals.get('is_project_template'):
            vals['state'] = 'a_template'
        return super(Project, self).create(vals)

    def write(self, vals):
        if vals.get('is_project_template'):
            vals['state'] = 'a_template'
        return super(Project, self).write(vals)

class StageTask(models.Model):
    """Task Stage Model Extension"""
    _inherit = 'project.task.type'

    is_done = fields.Boolean(
        string='Done Stage',
        help='Indicates if this stage represents a completed task'
    ) 