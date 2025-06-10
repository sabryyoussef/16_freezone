from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class ProjectException(models.Model):
    """
    Project Exception Model
    Handles exceptions and error tracking for projects
    """
    _name = 'project.exception'
    _description = 'Project Exception'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Exception Name',
        required=True,
        tracking=True,
        help='Name of the exception'
    )
    
    code = fields.Char(
        string='Exception Code',
        required=True,
        tracking=True,
        help='Unique code for the exception'
    )
    
    description = fields.Text(
        string='Description',
        tracking=True,
        help='Detailed description of the exception'
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('resolved', 'Resolved'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    severity = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], string='Severity', default='medium', tracking=True)
    
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        tracking=True,
        help='Related project'
    )
    
    task_id = fields.Many2one(
        'project.task',
        string='Task',
        tracking=True,
        help='Related task'
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='Assigned To',
        default=lambda self: self.env.user,
        tracking=True
    )
    
    resolution_notes = fields.Text(
        string='Resolution Notes',
        tracking=True,
        help='Notes about how the exception was resolved'
    )
    
    resolved_date = fields.Datetime(
        string='Resolved Date',
        tracking=True
    )
    
    resolved_by = fields.Many2one(
        'res.users',
        string='Resolved By',
        tracking=True
    )

    @api.constrains('code')
    def _check_code_unique(self):
        for record in self:
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_('Exception code must be unique!'))

    def action_set_active(self):
        self.ensure_one()
        if self.state == 'draft':
            self.write({'state': 'active'})
        return True

    def action_resolve(self):
        self.ensure_one()
        if self.state in ['draft', 'active']:
            self.write({
                'state': 'resolved',
                'resolved_date': fields.Datetime.now(),
                'resolved_by': self.env.user.id
            })
        return True

    def action_cancel(self):
        self.ensure_one()
        if self.state != 'cancelled':
            self.write({'state': 'cancelled'})
        return True

    def action_reset_to_draft(self):
        self.ensure_one()
        if self.state in ['cancelled', 'resolved']:
            self.write({
                'state': 'draft',
                'resolved_date': False,
                'resolved_by': False,
                'resolution_notes': False
            })
        return True

    @api.model
    def create(self, vals):
        if not vals.get('code'):
            vals['code'] = self.env['ir.sequence'].next_by_code('project.exception') or '/'
        return super(ProjectException, self).create(vals)

    def write(self, vals):
        if 'state' in vals and vals['state'] == 'resolved':
            if not vals.get('resolved_date'):
                vals['resolved_date'] = fields.Datetime.now()
            if not vals.get('resolved_by'):
                vals['resolved_by'] = self.env.user.id
        return super(ProjectException, self).write(vals)

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.code} - {record.name}"
            result.append((record.id, name))
        return result 