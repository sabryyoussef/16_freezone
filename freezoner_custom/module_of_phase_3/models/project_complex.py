from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class ProjectComplex(models.Model):
    """
    Complex Project Model
    Extends the base project model with advanced features:
    - Project hierarchies (parent-child relationships)
    - Complex dependencies
    - Advanced milestone tracking
    - Resource allocation
    - Risk management
    - Cost tracking
    """
    _inherit = 'project.project'
    _description = 'Complex Project'
    _order = 'sequence, id'

    # Hierarchy Fields
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Order of projects in the list'
    )
    
    parent_id = fields.Many2one(
        'project.project',
        string='Parent Project',
        domain="[('id', '!=', id)]",
        tracking=True,
        help='Parent project in the hierarchy'
    )
    
    child_ids = fields.One2many(
        'project.project',
        'parent_id',
        string='Sub Projects',
        help='Child projects in the hierarchy'
    )
    
    project_level = fields.Integer(
        string='Project Level',
        compute='_compute_project_level',
        store=True,
        help='Level in the project hierarchy'
    )
    
    is_template = fields.Boolean(
        string='Is Template',
        default=False,
        tracking=True,
        help='Indicates if this project is a template'
    )
    
    template_id = fields.Many2one(
        'project.project',
        string='Based on Template',
        domain="[('is_template', '=', True)]",
        tracking=True,
        help='Template this project is based on'
    )

    # Dependency Fields
    dependency_ids = fields.Many2many(
        'project.project',
        'project_dependency_rel',
        'project_id',
        'dependency_id',
        string='Dependencies',
        domain="[('id', '!=', id)]",
        help='Projects this project depends on'
    )
    
    dependent_ids = fields.Many2many(
        'project.project',
        'project_dependency_rel',
        'dependency_id',
        'project_id',
        string='Dependent Projects',
        help='Projects that depend on this project'
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

    # Milestone Fields
    milestone_ids = fields.One2many(
        'project.milestone',
        'project_id',
        string='Milestones',
        help='Project milestones'
    )
    
    milestone_count = fields.Integer(
        string='Milestone Count',
        compute='_compute_milestone_count',
        store=True
    )
    
    next_milestone_id = fields.Many2one(
        'project.milestone',
        string='Next Milestone',
        compute='_compute_next_milestone',
        store=True,
        help='Next upcoming milestone'
    )

    # Resource Fields
    resource_ids = fields.Many2many(
        'res.users',
        'project_resource_rel',
        'project_id',
        'user_id',
        string='Assigned Resources',
        help='Users assigned to this project'
    )
    
    resource_allocation_ids = fields.One2many(
        'project.resource.allocation',
        'project_id',
        string='Resource Allocations',
        help='Detailed resource allocations'
    )
    
    total_resource_hours = fields.Float(
        string='Total Resource Hours',
        compute='_compute_total_resource_hours',
        store=True,
        help='Total hours allocated to this project'
    )

    # Risk Fields
    risk_ids = fields.One2many(
        'project.risk',
        'project_id',
        string='Risks',
        help='Project risks'
    )
    
    risk_count = fields.Integer(
        string='Risk Count',
        compute='_compute_risk_count',
        store=True
    )
    
    risk_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], string='Risk Level',
        compute='_compute_risk_level',
        store=True,
        help='Overall project risk level'
    )

    # Cost Fields
    budget = fields.Monetary(
        string='Budget',
        currency_field='currency_id',
        tracking=True,
        help='Project budget'
    )
    
    actual_cost = fields.Monetary(
        string='Actual Cost',
        currency_field='currency_id',
        compute='_compute_actual_cost',
        store=True,
        help='Actual project cost'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        help='Project currency'
    )
    
    cost_variance = fields.Monetary(
        string='Cost Variance',
        currency_field='currency_id',
        compute='_compute_cost_variance',
        store=True,
        help='Difference between budget and actual cost'
    )

    # Computed Methods
    @api.depends('parent_id', 'parent_id.project_level')
    def _compute_project_level(self):
        for project in self:
            level = 0
            parent = project.parent_id
            while parent:
                level += 1
                parent = parent.parent_id
            project.project_level = level

    @api.depends('milestone_ids')
    def _compute_milestone_count(self):
        for project in self:
            project.milestone_count = len(project.milestone_ids)

    @api.depends('milestone_ids', 'milestone_ids.date')
    def _compute_next_milestone(self):
        for project in self:
            today = fields.Date.today()
            next_milestone = project.milestone_ids.filtered(
                lambda m: m.date >= today
            ).sorted('date')[:1]
            project.next_milestone_id = next_milestone

    @api.depends('resource_allocation_ids', 'resource_allocation_ids.hours')
    def _compute_total_resource_hours(self):
        for project in self:
            project.total_resource_hours = sum(
                project.resource_allocation_ids.mapped('hours')
            )

    @api.depends('risk_ids')
    def _compute_risk_count(self):
        for project in self:
            project.risk_count = len(project.risk_ids)

    @api.depends('risk_ids', 'risk_ids.severity')
    def _compute_risk_level(self):
        for project in self:
            risks = project.risk_ids
            if not risks:
                project.risk_level = 'low'
            elif any(r.severity == 'critical' for r in risks):
                project.risk_level = 'critical'
            elif any(r.severity == 'high' for r in risks):
                project.risk_level = 'high'
            elif any(r.severity == 'medium' for r in risks):
                project.risk_level = 'medium'
            else:
                project.risk_level = 'low'

    @api.depends('resource_allocation_ids', 'resource_allocation_ids.cost')
    def _compute_actual_cost(self):
        for project in self:
            project.actual_cost = sum(
                project.resource_allocation_ids.mapped('cost')
            )

    @api.depends('budget', 'actual_cost')
    def _compute_cost_variance(self):
        for project in self:
            project.cost_variance = project.actual_cost - project.budget

    # Constraint Methods
    @api.constrains('parent_id')
    def _check_parent_id(self):
        for project in self:
            if project.parent_id:
                if project.parent_id == project:
                    raise ValidationError(_('A project cannot be its own parent.'))
                if project.parent_id in project.child_ids:
                    raise ValidationError(_('Circular dependency detected in project hierarchy.'))

    @api.constrains('dependency_ids')
    def _check_dependencies(self):
        for project in self:
            if project in project.dependency_ids:
                raise ValidationError(_('A project cannot depend on itself.'))

    # Action Methods
    def action_view_milestones(self):
        return {
            'name': _('Milestones'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.milestone',
            'view_mode': 'tree,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id}
        }

    def action_view_risks(self):
        return {
            'name': _('Risks'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.risk',
            'view_mode': 'tree,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id}
        }

    def action_view_resources(self):
        return {
            'name': _('Resource Allocations'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.resource.allocation',
            'view_mode': 'tree,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id}
        }

    def action_create_from_template(self):
        self.ensure_one()
        if not self.is_template:
            raise UserError(_('Only template projects can be used to create new projects.'))
        
        return {
            'name': _('Create Project from Template'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.create.from.template',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_template_id': self.id}
        }

    # Model Methods
    @api.model
    def create(self, vals):
        if vals.get('template_id'):
            template = self.browse(vals['template_id'])
            if not template.is_template:
                raise UserError(_('The selected project is not a template.'))
            # Copy relevant fields from template
            vals.update(self._get_template_vals(template))
        return super(ProjectComplex, self).create(vals)

    def _get_template_vals(self, template):
        """Get values to copy from template"""
        return {
            'milestone_ids': [(0, 0, {
                'name': m.name,
                'date': m.date,
                'description': m.description
            }) for m in template.milestone_ids],
            'resource_allocation_ids': [(0, 0, {
                'user_id': r.user_id.id,
                'role_id': r.role_id.id,
                'hours': r.hours
            }) for r in template.resource_allocation_ids],
            'risk_ids': [(0, 0, {
                'name': r.name,
                'description': r.description,
                'severity': r.severity,
                'probability': r.probability
            }) for r in template.risk_ids]
        }

class ProjectMilestone(models.Model):
    """Project Milestone Model"""
    _name = 'project.milestone'
    _description = 'Project Milestone'
    _order = 'date, id'

    name = fields.Char(
        string='Name',
        required=True,
        tracking=True
    )
    
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    date = fields.Date(
        string='Date',
        required=True,
        tracking=True
    )
    
    description = fields.Text(
        string='Description'
    )
    
    is_reached = fields.Boolean(
        string='Reached',
        default=False,
        tracking=True
    )
    
    reached_date = fields.Date(
        string='Reached Date',
        tracking=True
    )

class ProjectRisk(models.Model):
    """Project Risk Model"""
    _name = 'project.risk'
    _description = 'Project Risk'
    _order = 'severity desc, probability desc, id'

    name = fields.Char(
        string='Name',
        required=True,
        tracking=True
    )
    
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    description = fields.Text(
        string='Description',
        tracking=True
    )
    
    severity = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], string='Severity',
        required=True,
        tracking=True
    )
    
    probability = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], string='Probability',
        required=True,
        tracking=True
    )
    
    mitigation_strategy = fields.Text(
        string='Mitigation Strategy',
        tracking=True
    )
    
    is_mitigated = fields.Boolean(
        string='Mitigated',
        default=False,
        tracking=True
    )

class ProjectResourceAllocation(models.Model):
    """Project Resource Allocation Model"""
    _name = 'project.resource.allocation'
    _description = 'Project Resource Allocation'
    _order = 'user_id, role_id'

    project_id = fields.Many2one(
        'project.project',
        string='Project',
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
        related='project_id.currency_id',
        string='Currency',
        store=True
    )

    @api.depends('hours', 'role_id', 'role_id.hourly_rate')
    def _compute_cost(self):
        for allocation in self:
            allocation.cost = allocation.hours * allocation.role_id.hourly_rate

class ProjectRole(models.Model):
    """Project Role Model"""
    _name = 'project.role'
    _description = 'Project Role'
    _order = 'name'

    name = fields.Char(
        string='Name',
        required=True,
        tracking=True
    )
    
    description = fields.Text(
        string='Description'
    )
    
    hourly_rate = fields.Monetary(
        string='Hourly Rate',
        currency_field='currency_id',
        required=True,
        tracking=True
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    
    skill_ids = fields.Many2many(
        'project.skill',
        string='Required Skills'
    ) 