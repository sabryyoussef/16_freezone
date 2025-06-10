from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class WorkflowTemplate(models.Model):
    """
    Workflow Template Model
    Defines reusable workflow templates:
    - Process definitions and steps
    - Workflow rules and conditions
    - User assignments and notifications
    - SLA and deadline management
    """
    _name = 'workflow.template'
    _description = 'Workflow Template'
    _order = 'sequence, name'

    # Basic Fields
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Order of templates in the list'
    )
    
    name = fields.Char(
        string='Name',
        required=True,
        tracking=True
    )
    
    code = fields.Char(
        string='Code',
        required=True,
        tracking=True,
        help='Unique template code'
    )
    
    description = fields.Text(
        string='Description',
        tracking=True
    )
    
    is_active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True
    )
    
    version = fields.Char(
        string='Version',
        default='1.0',
        tracking=True
    )

    # Process Fields
    model_id = fields.Many2one(
        'ir.model',
        string='Model',
        required=True,
        tracking=True,
        help='Model this workflow applies to'
    )
    
    trigger_type = fields.Selection([
        ('manual', 'Manual'),
        ('automatic', 'Automatic'),
        ('scheduled', 'Scheduled'),
        ('conditional', 'Conditional')
    ], string='Trigger Type',
        required=True,
        tracking=True
    )
    
    trigger_condition = fields.Text(
        string='Trigger Condition',
        tracking=True,
        help='Python condition for automatic/conditional triggers'
    )
    
    schedule_cron = fields.Char(
        string='Schedule (Cron)',
        tracking=True,
        help='Cron expression for scheduled triggers'
    )

    # Step Fields
    step_ids = fields.One2many(
        'workflow.step',
        'template_id',
        string='Steps',
        help='Workflow steps'
    )
    
    initial_step_id = fields.Many2one(
        'workflow.step',
        string='Initial Step',
        domain="[('template_id', '=', id)]",
        tracking=True
    )
    
    final_step_ids = fields.Many2many(
        'workflow.step',
        'workflow_template_final_step_rel',
        'template_id',
        'step_id',
        string='Final Steps',
        domain="[('template_id', '=', id)]",
        help='Steps that mark workflow completion'
    )

    # SLA Fields
    sla_ids = fields.One2many(
        'workflow.sla',
        'template_id',
        string='SLAs',
        help='Service level agreements'
    )
    
    default_sla_days = fields.Integer(
        string='Default SLA (Days)',
        default=5,
        tracking=True,
        help='Default number of days for SLA'
    )
    
    escalation_user_ids = fields.Many2many(
        'res.users',
        string='Escalation Users',
        help='Users to notify on SLA breach'
    )

    # Notification Fields
    notify_on_start = fields.Boolean(
        string='Notify on Start',
        default=True,
        tracking=True
    )
    
    notify_on_complete = fields.Boolean(
        string='Notify on Complete',
        default=True,
        tracking=True
    )
    
    notify_on_escalate = fields.Boolean(
        string='Notify on Escalate',
        default=True,
        tracking=True
    )
    
    notification_template_ids = fields.Many2many(
        'mail.template',
        string='Notification Templates',
        help='Email templates for notifications'
    )

    # Constraint Methods
    @api.constrains('step_ids')
    def _check_steps(self):
        for template in self:
            if not template.step_ids:
                raise ValidationError(_('Workflow template must have at least one step.'))
            if not template.initial_step_id:
                raise ValidationError(_('Workflow template must have an initial step.'))
            if not template.final_step_ids:
                raise ValidationError(_('Workflow template must have at least one final step.'))

    @api.constrains('trigger_type', 'trigger_condition', 'schedule_cron')
    def _check_trigger(self):
        for template in self:
            if template.trigger_type == 'conditional' and not template.trigger_condition:
                raise ValidationError(_('Conditional trigger requires a trigger condition.'))
            if template.trigger_type == 'scheduled' and not template.schedule_cron:
                raise ValidationError(_('Scheduled trigger requires a cron expression.'))

    # Action Methods
    def action_view_steps(self):
        return {
            'name': _('Steps'),
            'type': 'ir.actions.act_window',
            'res_model': 'workflow.step',
            'view_mode': 'tree,form',
            'domain': [('template_id', '=', self.id)],
            'context': {'default_template_id': self.id}
        }

    def action_view_instances(self):
        return {
            'name': _('Workflow Instances'),
            'type': 'ir.actions.act_window',
            'res_model': 'workflow.instance',
            'view_mode': 'tree,form',
            'domain': [('template_id', '=', self.id)]
        }

    def action_create_instance(self):
        self.ensure_one()
        return {
            'name': _('Create Workflow Instance'),
            'type': 'ir.actions.act_window',
            'res_model': 'workflow.create.instance',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_template_id': self.id}
        }

class WorkflowStep(models.Model):
    """Workflow Step Model"""
    _name = 'workflow.step'
    _description = 'Workflow Step'
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
    
    template_id = fields.Many2one(
        'workflow.template',
        string='Template',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    description = fields.Text(
        string='Description',
        tracking=True
    )
    
    step_type = fields.Selection([
        ('task', 'Task'),
        ('approval', 'Approval'),
        ('notification', 'Notification'),
        ('automated', 'Automated'),
        ('gateway', 'Gateway')
    ], string='Step Type',
        required=True,
        tracking=True
    )
    
    gateway_type = fields.Selection([
        ('exclusive', 'Exclusive'),
        ('parallel', 'Parallel'),
        ('inclusive', 'Inclusive')
    ], string='Gateway Type',
        tracking=True
    )
    
    condition = fields.Text(
        string='Condition',
        tracking=True,
        help='Python condition for gateway branching'
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='Assigned User',
        tracking=True
    )
    
    group_id = fields.Many2one(
        'res.groups',
        string='Assigned Group',
        tracking=True
    )
    
    role_id = fields.Many2one(
        'res.partner.role',
        string='Required Role',
        tracking=True
    )
    
    action = fields.Text(
        string='Action',
        tracking=True,
        help='Python code for automated steps'
    )
    
    next_step_ids = fields.Many2many(
        'workflow.step',
        'workflow_step_next_rel',
        'step_id',
        'next_id',
        string='Next Steps',
        domain="[('template_id', '=', template_id)]"
    )
    
    previous_step_ids = fields.Many2many(
        'workflow.step',
        'workflow_step_next_rel',
        'next_id',
        'step_id',
        string='Previous Steps',
        domain="[('template_id', '=', template_id)]"
    )
    
    sla_days = fields.Integer(
        string='SLA (Days)',
        tracking=True,
        help='Number of days for this step'
    )
    
    is_required = fields.Boolean(
        string='Required',
        default=True,
        tracking=True
    )
    
    is_parallel = fields.Boolean(
        string='Parallel',
        default=False,
        tracking=True,
        help='Allow parallel execution with other steps'
    )

class WorkflowInstance(models.Model):
    """Workflow Instance Model"""
    _name = 'workflow.instance'
    _description = 'Workflow Instance'
    _order = 'create_date desc, id'

    name = fields.Char(
        string='Name',
        required=True,
        tracking=True
    )
    
    template_id = fields.Many2one(
        'workflow.template',
        string='Template',
        required=True,
        ondelete='restrict',
        index=True
    )
    
    res_model = fields.Char(
        string='Model',
        related='template_id.model_id.model',
        store=True
    )
    
    res_id = fields.Integer(
        string='Record ID',
        required=True,
        index=True
    )
    
    record_name = fields.Char(
        string='Record',
        compute='_compute_record_name',
        store=True
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('error', 'Error')
    ], string='Status',
        default='draft',
        tracking=True
    )
    
    current_step_ids = fields.Many2many(
        'workflow.step',
        string='Current Steps',
        help='Currently active steps'
    )
    
    step_history_ids = fields.One2many(
        'workflow.step.history',
        'instance_id',
        string='Step History',
        help='History of step transitions'
    )
    
    start_date = fields.Datetime(
        string='Start Date',
        tracking=True
    )
    
    end_date = fields.Datetime(
        string='End Date',
        tracking=True
    )
    
    duration = fields.Float(
        string='Duration (Days)',
        compute='_compute_duration',
        store=True
    )
    
    sla_breach_ids = fields.One2many(
        'workflow.sla.breach',
        'instance_id',
        string='SLA Breaches',
        help='SLA breach records'
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='Created By',
        default=lambda self: self.env.user,
        tracking=True
    )
    
    notes = fields.Text(
        string='Notes',
        tracking=True
    )

    # Computed Methods
    @api.depends('res_model', 'res_id')
    def _compute_record_name(self):
        for instance in self:
            if instance.res_model and instance.res_id:
                record = self.env[instance.res_model].browse(instance.res_id)
                instance.record_name = record.name_get()[0][1] if record else False
            else:
                instance.record_name = False

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        for instance in self:
            if instance.start_date and instance.end_date:
                delta = instance.end_date - instance.start_date
                instance.duration = delta.total_seconds() / (24 * 3600)
            else:
                instance.duration = 0.0

    # Action Methods
    def action_start(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Only draft workflows can be started.'))
        
        self.write({
            'state': 'running',
            'start_date': fields.Datetime.now(),
            'current_step_ids': [(6, 0, [self.template_id.initial_step_id.id])]
        })
        
        # Create initial step history
        self.env['workflow.step.history'].create({
            'instance_id': self.id,
            'step_id': self.template_id.initial_step_id.id,
            'state': 'started',
            'date': fields.Datetime.now()
        })
        
        # Send notifications
        if self.template_id.notify_on_start:
            self._send_notifications('start')

    def action_complete_step(self, step_id, result='approved'):
        self.ensure_one()
        step = self.env['workflow.step'].browse(step_id)
        if step not in self.current_step_ids:
            raise UserError(_('Step is not in current steps.'))
        
        # Record step completion
        self.env['workflow.step.history'].create({
            'instance_id': self.id,
            'step_id': step.id,
            'state': 'completed',
            'result': result,
            'date': fields.Datetime.now()
        })
        
        # Remove from current steps
        self.current_step_ids = [(3, step.id)]
        
        # Add next steps
        next_steps = step.next_step_ids
        if next_steps:
            self.current_step_ids = [(4, step.id) for step in next_steps]
            
            # Create step history for new steps
            for next_step in next_steps:
                self.env['workflow.step.history'].create({
                    'instance_id': self.id,
                    'step_id': next_step.id,
                    'state': 'started',
                    'date': fields.Datetime.now()
                })
        else:
            # No next steps, workflow is complete
            self.action_complete()

    def action_complete(self):
        self.ensure_one()
        if not self.current_step_ids:
            self.write({
                'state': 'completed',
                'end_date': fields.Datetime.now()
            })
            
            # Send notifications
            if self.template_id.notify_on_complete:
                self._send_notifications('complete')

    def action_cancel(self):
        self.ensure_one()
        if self.state not in ['draft', 'running']:
            raise UserError(_('Only draft or running workflows can be cancelled.'))
        
        self.write({
            'state': 'cancelled',
            'end_date': fields.Datetime.now()
        })

    def _send_notifications(self, notification_type):
        """Send notifications based on template settings"""
        self.ensure_one()
        if not self.template_id.notification_template_ids:
            return
        
        for template in self.template_id.notification_template_ids:
            template.with_context(
                workflow_instance=self,
                notification_type=notification_type
            ).send_mail(self.id, force_send=True)

class WorkflowStepHistory(models.Model):
    """Workflow Step History Model"""
    _name = 'workflow.step.history'
    _description = 'Workflow Step History'
    _order = 'date desc, id'

    instance_id = fields.Many2one(
        'workflow.instance',
        string='Instance',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    step_id = fields.Many2one(
        'workflow.step',
        string='Step',
        required=True,
        ondelete='restrict',
        index=True
    )
    
    state = fields.Selection([
        ('started', 'Started'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('error', 'Error')
    ], string='Status',
        required=True,
        tracking=True
    )
    
    result = fields.Selection([
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('skipped', 'Skipped')
    ], string='Result',
        tracking=True
    )
    
    date = fields.Datetime(
        string='Date',
        required=True,
        tracking=True
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='User',
        default=lambda self: self.env.user,
        tracking=True
    )
    
    notes = fields.Text(
        string='Notes',
        tracking=True
    )

class WorkflowSLA(models.Model):
    """Workflow SLA Model"""
    _name = 'workflow.sla'
    _description = 'Workflow SLA'
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
    
    template_id = fields.Many2one(
        'workflow.template',
        string='Template',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    step_id = fields.Many2one(
        'workflow.step',
        string='Step',
        domain="[('template_id', '=', template_id)]",
        tracking=True
    )
    
    days = fields.Integer(
        string='Days',
        required=True,
        tracking=True
    )
    
    warning_days = fields.Integer(
        string='Warning Days',
        tracking=True,
        help='Days before SLA breach to send warning'
    )
    
    is_active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True
    )

class WorkflowSLABreach(models.Model):
    """Workflow SLA Breach Model"""
    _name = 'workflow.sla.breach'
    _description = 'Workflow SLA Breach'
    _order = 'date desc, id'

    name = fields.Char(
        string='Name',
        required=True,
        tracking=True
    )
    
    instance_id = fields.Many2one(
        'workflow.instance',
        string='Instance',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    sla_id = fields.Many2one(
        'workflow.sla',
        string='SLA',
        required=True,
        ondelete='restrict',
        index=True
    )
    
    step_id = fields.Many2one(
        'workflow.step',
        string='Step',
        required=True,
        ondelete='restrict',
        index=True
    )
    
    date = fields.Datetime(
        string='Breach Date',
        required=True,
        tracking=True
    )
    
    breach_type = fields.Selection([
        ('warning', 'Warning'),
        ('breach', 'Breach')
    ], string='Breach Type',
        required=True,
        tracking=True
    )
    
    is_resolved = fields.Boolean(
        string='Resolved',
        default=False,
        tracking=True
    )
    
    resolution_date = fields.Datetime(
        string='Resolution Date',
        tracking=True
    )
    
    resolution_notes = fields.Text(
        string='Resolution Notes',
        tracking=True
    ) 