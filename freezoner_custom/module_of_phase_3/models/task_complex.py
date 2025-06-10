from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class TaskComplex(models.Model):
    """
    Complex Task Model
    Extends the base task model with advanced features:
    - Task hierarchies and dependencies
    - Time tracking and estimation
    - Resource allocation
    - Quality control
    - Task templates
    - Advanced reporting
    """
    _inherit = 'project.task'
    _description = 'Complex Task'
    _order = 'sequence, id'

    # Basic Fields
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Order of tasks in the list'
    )
    
    code = fields.Char(
        string='Task Code',
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        help='Unique task identifier'
    )
    
    is_template = fields.Boolean(
        string='Is Template',
        default=False,
        tracking=True,
        help='Indicates if this task is a template'
    )
    
    template_id = fields.Many2one(
        'project.task',
        string='Based on Template',
        domain="[('is_template', '=', True)]",
        tracking=True,
        help='Template this task is based on'
    )

    # Hierarchy Fields
    parent_id = fields.Many2one(
        'project.task',
        string='Parent Task',
        domain="[('id', '!=', id)]",
        tracking=True,
        help='Parent task in the hierarchy'
    )
    
    child_ids = fields.One2many(
        'project.task',
        'parent_id',
        string='Sub Tasks',
        help='Child tasks in the hierarchy'
    )
    
    task_level = fields.Integer(
        string='Task Level',
        compute='_compute_task_level',
        store=True,
        help='Level in the task hierarchy'
    )

    # Dependency Fields
    dependency_ids = fields.Many2many(
        'project.task',
        'task_dependency_rel',
        'task_id',
        'dependency_id',
        string='Dependencies',
        domain="[('id', '!=', id)]",
        help='Tasks this task depends on'
    )
    
    dependent_ids = fields.Many2many(
        'project.task',
        'task_dependency_rel',
        'dependency_id',
        'task_id',
        string='Dependent Tasks',
        help='Tasks that depend on this task'
    )
    
    dependency_type = fields.Selection([
        ('start_to_start', 'Start to Start'),
        ('start_to_finish', 'Start to Finish'),
        ('finish_to_start', 'Finish to Start'),
        ('finish_to_finish', 'Finish to Finish')
    ], string='Dependency Type',
        default='finish_to_start',
        tracking=True,
        help='Type of dependency relationship'
    )

    # Time Tracking Fields
    estimated_hours = fields.Float(
        string='Estimated Hours',
        tracking=True,
        help='Estimated time to complete the task'
    )
    
    effective_hours = fields.Float(
        string='Effective Hours',
        compute='_compute_effective_hours',
        store=True,
        help='Actual time spent on the task'
    )
    
    remaining_hours = fields.Float(
        string='Remaining Hours',
        compute='_compute_remaining_hours',
        store=True,
        help='Remaining time to complete the task'
    )
    
    time_variance = fields.Float(
        string='Time Variance',
        compute='_compute_time_variance',
        store=True,
        help='Difference between estimated and effective hours'
    )

    # Resource Fields
    resource_ids = fields.Many2many(
        'res.users',
        'task_resource_rel',
        'task_id',
        'user_id',
        string='Assigned Resources',
        help='Users assigned to this task'
    )
    
    resource_allocation_ids = fields.One2many(
        'task.resource.allocation',
        'task_id',
        string='Resource Allocations',
        help='Detailed resource allocations'
    )
    
    role_ids = fields.Many2many(
        'project.role',
        string='Required Roles',
        help='Roles required for this task'
    )

    # Quality Fields
    quality_check_ids = fields.One2many(
        'task.quality.check',
        'task_id',
        string='Quality Checks',
        help='Quality control checks for this task'
    )
    
    quality_score = fields.Float(
        string='Quality Score',
        compute='_compute_quality_score',
        store=True,
        help='Overall quality score of the task'
    )
    
    review_required = fields.Boolean(
        string='Review Required',
        default=False,
        tracking=True,
        help='Indicates if this task requires review'
    )
    
    reviewer_id = fields.Many2one(
        'res.users',
        string='Reviewer',
        tracking=True,
        help='User responsible for reviewing the task'
    )

    # Document Fields
    document_ids = fields.Many2many(
        'documents.document',
        string='Related Documents',
        help='Documents associated with this task'
    )
    
    required_document_ids = fields.Many2many(
        'documents.document',
        'task_required_document_rel',
        'task_id',
        'document_id',
        string='Required Documents',
        help='Documents required for this task'
    )

    # Computed Methods
    @api.depends('parent_id', 'parent_id.task_level')
    def _compute_task_level(self):
        for task in self:
            level = 0
            parent = task.parent_id
            while parent:
                level += 1
                parent = parent.parent_id
            task.task_level = level

    @api.depends('timesheet_ids', 'timesheet_ids.unit_amount')
    def _compute_effective_hours(self):
        for task in self:
            task.effective_hours = sum(task.timesheet_ids.mapped('unit_amount'))

    @api.depends('estimated_hours', 'effective_hours')
    def _compute_remaining_hours(self):
        for task in self:
            task.remaining_hours = max(0, task.estimated_hours - task.effective_hours)

    @api.depends('estimated_hours', 'effective_hours')
    def _compute_time_variance(self):
        for task in self:
            task.time_variance = task.effective_hours - task.estimated_hours

    @api.depends('quality_check_ids', 'quality_check_ids.score')
    def _compute_quality_score(self):
        for task in self:
            checks = task.quality_check_ids.filtered(lambda c: c.score is not False)
            task.quality_score = sum(checks.mapped('score')) / len(checks) if checks else 0.0

    # Constraint Methods
    @api.constrains('parent_id')
    def _check_parent_id(self):
        for task in self:
            if task.parent_id:
                if task.parent_id == task:
                    raise ValidationError(_('A task cannot be its own parent.'))
                if task.parent_id in task.child_ids:
                    raise ValidationError(_('Circular dependency detected in task hierarchy.'))

    @api.constrains('dependency_ids')
    def _check_dependencies(self):
        for task in self:
            if task in task.dependency_ids:
                raise ValidationError(_('A task cannot depend on itself.'))

    # Action Methods
    def action_view_quality_checks(self):
        return {
            'name': _('Quality Checks'),
            'type': 'ir.actions.act_window',
            'res_model': 'task.quality.check',
            'view_mode': 'tree,form',
            'domain': [('task_id', '=', self.id)],
            'context': {'default_task_id': self.id}
        }

    def action_view_resources(self):
        return {
            'name': _('Resource Allocations'),
            'type': 'ir.actions.act_window',
            'res_model': 'task.resource.allocation',
            'view_mode': 'tree,form',
            'domain': [('task_id', '=', self.id)],
            'context': {'default_task_id': self.id}
        }

    def action_create_from_template(self):
        self.ensure_one()
        if not self.is_template:
            raise UserError(_('Only template tasks can be used to create new tasks.'))
        
        return {
            'name': _('Create Task from Template'),
            'type': 'ir.actions.act_window',
            'res_model': 'task.create.from.template',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_template_id': self.id}
        }

    # Model Methods
    @api.model
    def create(self, vals):
        if vals.get('code', _('New')) == _('New'):
            vals['code'] = self.env['ir.sequence'].next_by_code('project.task') or _('New')
        
        if vals.get('template_id'):
            template = self.browse(vals['template_id'])
            if not template.is_template:
                raise UserError(_('The selected task is not a template.'))
            # Copy relevant fields from template
            vals.update(self._get_template_vals(template))
        
        return super(TaskComplex, self).create(vals)

    def _get_template_vals(self, template):
        """Get values to copy from template"""
        return {
            'estimated_hours': template.estimated_hours,
            'role_ids': [(6, 0, template.role_ids.ids)],
            'required_document_ids': [(6, 0, template.required_document_ids.ids)],
            'review_required': template.review_required,
            'quality_check_ids': [(0, 0, {
                'name': q.name,
                'description': q.description,
                'check_type': q.check_type,
                'required_score': q.required_score
            }) for q in template.quality_check_ids]
        }

class TaskQualityCheck(models.Model):
    """Task Quality Check Model"""
    _name = 'task.quality.check'
    _description = 'Task Quality Check'
    _order = 'sequence, id'

    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    name = fields.Char(
        string='Name',
        required=True,
        tracking=True
    )
    
    task_id = fields.Many2one(
        'project.task',
        string='Task',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    description = fields.Text(
        string='Description',
        tracking=True
    )
    
    check_type = fields.Selection([
        ('manual', 'Manual Check'),
        ('automated', 'Automated Check'),
        ('review', 'Review')
    ], string='Check Type',
        required=True,
        tracking=True
    )
    
    required_score = fields.Float(
        string='Required Score',
        tracking=True,
        help='Minimum score required to pass the check'
    )
    
    score = fields.Float(
        string='Score',
        tracking=True,
        help='Actual score achieved'
    )
    
    is_passed = fields.Boolean(
        string='Passed',
        compute='_compute_is_passed',
        store=True
    )
    
    notes = fields.Text(
        string='Notes',
        tracking=True
    )

    @api.depends('score', 'required_score')
    def _compute_is_passed(self):
        for check in self:
            check.is_passed = check.score >= check.required_score if check.score is not False else False

class TaskResourceAllocation(models.Model):
    """Task Resource Allocation Model"""
    _name = 'task.resource.allocation'
    _description = 'Task Resource Allocation'
    _order = 'user_id, role_id'

    task_id = fields.Many2one(
        'project.task',
        string='Task',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        tracking=True
    )
    
    role_id = fields.Many2one(
        'project.role',
        string='Role',
        required=True,
        tracking=True
    )
    
    hours = fields.Float(
        string='Allocated Hours',
        required=True,
        tracking=True
    )
    
    cost = fields.Monetary(
        string='Cost',
        currency_field='currency_id',
        compute='_compute_cost',
        store=True
    )
    
    currency_id = fields.Many2one(
        related='task_id.project_id.currency_id',
        string='Currency',
        store=True
    )

    @api.depends('hours', 'role_id', 'role_id.hourly_rate')
    def _compute_cost(self):
        for allocation in self:
            allocation.cost = allocation.hours * allocation.role_id.hourly_rate 