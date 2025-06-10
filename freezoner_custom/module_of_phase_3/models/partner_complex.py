from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class PartnerComplex(models.Model):
    """
    Complex Partner Model
    Extends the base partner model with advanced features:
    - Partner hierarchies and relationships
    - Advanced contact management
    - Partner roles and responsibilities
    - Partner compliance and certifications
    - Partner performance tracking
    - Partner communication history
    """
    _inherit = 'res.partner'
    _description = 'Complex Partner'
    _order = 'sequence, name'

    # Basic Fields
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Order of partners in the list'
    )
    
    code = fields.Char(
        string='Partner Code',
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        help='Unique partner identifier'
    )
    
    is_template = fields.Boolean(
        string='Is Template',
        default=False,
        tracking=True,
        help='Indicates if this partner is a template'
    )
    
    template_id = fields.Many2one(
        'res.partner',
        string='Based on Template',
        domain="[('is_template', '=', True)]",
        tracking=True,
        help='Template this partner is based on'
    )

    # Hierarchy Fields
    parent_id = fields.Many2one(
        'res.partner',
        string='Parent Company',
        domain="[('id', '!=', id), ('is_company', '=', True)]",
        tracking=True,
        help='Parent company in the hierarchy'
    )
    
    child_ids = fields.One2many(
        'res.partner',
        'parent_id',
        string='Child Companies',
        help='Child companies in the hierarchy'
    )
    
    partner_level = fields.Integer(
        string='Partner Level',
        compute='_compute_partner_level',
        store=True,
        help='Level in the partner hierarchy'
    )
    
    is_company = fields.Boolean(
        string='Is a Company',
        default=True,
        tracking=True,
        help='Indicates if this partner is a company'
    )

    # Contact Fields
    contact_ids = fields.One2many(
        'partner.contact',
        'partner_id',
        string='Contacts',
        help='Detailed contact information'
    )
    
    primary_contact_id = fields.Many2one(
        'partner.contact',
        string='Primary Contact',
        domain="[('partner_id', '=', id)]",
        tracking=True,
        help='Primary contact person'
    )
    
    contact_count = fields.Integer(
        string='Contact Count',
        compute='_compute_contact_count',
        store=True
    )

    # Role Fields
    role_ids = fields.Many2many(
        'partner.role',
        string='Partner Roles',
        help='Roles assigned to this partner'
    )
    
    responsibility_ids = fields.One2many(
        'partner.responsibility',
        'partner_id',
        string='Responsibilities',
        help='Partner responsibilities'
    )
    
    is_active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help='Indicates if the partner is active'
    )

    # Compliance Fields
    compliance_ids = fields.One2many(
        'partner.compliance',
        'partner_id',
        string='Compliance Records',
        help='Partner compliance records'
    )
    
    certification_ids = fields.One2many(
        'partner.certification',
        'partner_id',
        string='Certifications',
        help='Partner certifications'
    )
    
    risk_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], string='Risk Level',
        compute='_compute_risk_level',
        store=True,
        help='Overall partner risk level'
    )

    # Performance Fields
    performance_ids = fields.One2many(
        'partner.performance',
        'partner_id',
        string='Performance Records',
        help='Partner performance records'
    )
    
    performance_score = fields.Float(
        string='Performance Score',
        compute='_compute_performance_score',
        store=True,
        help='Overall partner performance score'
    )
    
    last_evaluation_date = fields.Date(
        string='Last Evaluation',
        compute='_compute_last_evaluation_date',
        store=True,
        help='Date of last performance evaluation'
    )

    # Communication Fields
    communication_ids = fields.One2many(
        'partner.communication',
        'partner_id',
        string='Communication History',
        help='Partner communication history'
    )
    
    preferred_communication_method = fields.Selection([
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('mail', 'Mail'),
        ('in_person', 'In Person')
    ], string='Preferred Communication Method',
        tracking=True,
        help='Preferred method of communication'
    )
    
    communication_frequency = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually')
    ], string='Communication Frequency',
        tracking=True,
        help='Expected communication frequency'
    )

    # Computed Methods
    @api.depends('parent_id', 'parent_id.partner_level')
    def _compute_partner_level(self):
        for partner in self:
            level = 0
            parent = partner.parent_id
            while parent:
                level += 1
                parent = parent.parent_id
            partner.partner_level = level

    @api.depends('contact_ids')
    def _compute_contact_count(self):
        for partner in self:
            partner.contact_count = len(partner.contact_ids)

    @api.depends('compliance_ids', 'compliance_ids.risk_level')
    def _compute_risk_level(self):
        for partner in self:
            compliances = partner.compliance_ids
            if not compliances:
                partner.risk_level = 'low'
            elif any(c.risk_level == 'critical' for c in compliances):
                partner.risk_level = 'critical'
            elif any(c.risk_level == 'high' for c in compliances):
                partner.risk_level = 'high'
            elif any(c.risk_level == 'medium' for c in compliances):
                partner.risk_level = 'medium'
            else:
                partner.risk_level = 'low'

    @api.depends('performance_ids', 'performance_ids.score')
    def _compute_performance_score(self):
        for partner in self:
            performances = partner.performance_ids.filtered(lambda p: p.score is not False)
            partner.performance_score = sum(performances.mapped('score')) / len(performances) if performances else 0.0

    @api.depends('performance_ids', 'performance_ids.date')
    def _compute_last_evaluation_date(self):
        for partner in self:
            last_eval = partner.performance_ids.sorted('date', reverse=True)[:1]
            partner.last_evaluation_date = last_eval.date if last_eval else False

    # Constraint Methods
    @api.constrains('parent_id')
    def _check_parent_id(self):
        for partner in self:
            if partner.parent_id:
                if partner.parent_id == partner:
                    raise ValidationError(_('A partner cannot be its own parent.'))
                if partner.parent_id in partner.child_ids:
                    raise ValidationError(_('Circular dependency detected in partner hierarchy.'))

    # Action Methods
    def action_view_contacts(self):
        return {
            'name': _('Contacts'),
            'type': 'ir.actions.act_window',
            'res_model': 'partner.contact',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id}
        }

    def action_view_compliance(self):
        return {
            'name': _('Compliance Records'),
            'type': 'ir.actions.act_window',
            'res_model': 'partner.compliance',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id}
        }

    def action_view_performance(self):
        return {
            'name': _('Performance Records'),
            'type': 'ir.actions.act_window',
            'res_model': 'partner.performance',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id}
        }

    def action_view_communication(self):
        return {
            'name': _('Communication History'),
            'type': 'ir.actions.act_window',
            'res_model': 'partner.communication',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id}
        }

    def action_create_from_template(self):
        self.ensure_one()
        if not self.is_template:
            raise UserError(_('Only template partners can be used to create new partners.'))
        
        return {
            'name': _('Create Partner from Template'),
            'type': 'ir.actions.act_window',
            'res_model': 'partner.create.from.template',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_template_id': self.id}
        }

    # Model Methods
    @api.model
    def create(self, vals):
        if vals.get('code', _('New')) == _('New'):
            vals['code'] = self.env['ir.sequence'].next_by_code('res.partner') or _('New')
        
        if vals.get('template_id'):
            template = self.browse(vals['template_id'])
            if not template.is_template:
                raise UserError(_('The selected partner is not a template.'))
            # Copy relevant fields from template
            vals.update(self._get_template_vals(template))
        
        return super(PartnerComplex, self).create(vals)

    def _get_template_vals(self, template):
        """Get values to copy from template"""
        return {
            'role_ids': [(6, 0, template.role_ids.ids)],
            'preferred_communication_method': template.preferred_communication_method,
            'communication_frequency': template.communication_frequency,
            'responsibility_ids': [(0, 0, {
                'name': r.name,
                'description': r.description,
                'role_id': r.role_id.id
            }) for r in template.responsibility_ids]
        }

class PartnerContact(models.Model):
    """Partner Contact Model"""
    _name = 'partner.contact'
    _description = 'Partner Contact'
    _order = 'sequence, name'

    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    name = fields.Char(
        string='Name',
        required=True,
        tracking=True
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    job_title = fields.Char(
        string='Job Title',
        tracking=True
    )
    
    email = fields.Char(
        string='Email',
        tracking=True
    )
    
    phone = fields.Char(
        string='Phone',
        tracking=True
    )
    
    mobile = fields.Char(
        string='Mobile',
        tracking=True
    )
    
    is_primary = fields.Boolean(
        string='Primary Contact',
        default=False,
        tracking=True
    )
    
    role_ids = fields.Many2many(
        'partner.role',
        string='Roles',
        help='Roles of this contact'
    )
    
    notes = fields.Text(
        string='Notes',
        tracking=True
    )

class PartnerRole(models.Model):
    """Partner Role Model"""
    _name = 'partner.role'
    _description = 'Partner Role'
    _order = 'sequence, name'

    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    name = fields.Char(
        string='Name',
        required=True,
        tracking=True
    )
    
    code = fields.Char(
        string='Code',
        tracking=True,
        help='Role code for reference'
    )
    
    description = fields.Text(
        string='Description'
    )
    
    is_active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True
    )

class PartnerResponsibility(models.Model):
    """Partner Responsibility Model"""
    _name = 'partner.responsibility'
    _description = 'Partner Responsibility'
    _order = 'sequence, name'

    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    name = fields.Char(
        string='Name',
        required=True,
        tracking=True
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    role_id = fields.Many2one(
        'partner.role',
        string='Role',
        required=True,
        tracking=True
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

class PartnerCompliance(models.Model):
    """Partner Compliance Model"""
    _name = 'partner.compliance'
    _description = 'Partner Compliance'
    _order = 'date desc, id'

    name = fields.Char(
        string='Name',
        required=True,
        tracking=True
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    date = fields.Date(
        string='Date',
        required=True,
        tracking=True
    )
    
    category = fields.Selection([
        ('legal', 'Legal'),
        ('regulatory', 'Regulatory'),
        ('industry', 'Industry'),
        ('internal', 'Internal'),
        ('other', 'Other')
    ], string='Category',
        required=True,
        tracking=True
    )
    
    risk_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], string='Risk Level',
        required=True,
        tracking=True
    )
    
    status = fields.Selection([
        ('pending', 'Pending'),
        ('compliant', 'Compliant'),
        ('non_compliant', 'Non-Compliant'),
        ('expired', 'Expired')
    ], string='Status',
        required=True,
        tracking=True
    )
    
    expiry_date = fields.Date(
        string='Expiry Date',
        tracking=True
    )
    
    notes = fields.Text(
        string='Notes',
        tracking=True
    )

class PartnerCertification(models.Model):
    """Partner Certification Model"""
    _name = 'partner.certification'
    _description = 'Partner Certification'
    _order = 'date desc, id'

    name = fields.Char(
        string='Name',
        required=True,
        tracking=True
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    date = fields.Date(
        string='Certification Date',
        required=True,
        tracking=True
    )
    
    expiry_date = fields.Date(
        string='Expiry Date',
        tracking=True
    )
    
    issuer = fields.Char(
        string='Issuer',
        required=True,
        tracking=True
    )
    
    certificate_number = fields.Char(
        string='Certificate Number',
        tracking=True
    )
    
    attachment_id = fields.Many2one(
        'ir.attachment',
        string='Certificate',
        tracking=True
    )
    
    notes = fields.Text(
        string='Notes',
        tracking=True
    )

class PartnerPerformance(models.Model):
    """Partner Performance Model"""
    _name = 'partner.performance'
    _description = 'Partner Performance'
    _order = 'date desc, id'

    name = fields.Char(
        string='Name',
        required=True,
        tracking=True
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    date = fields.Date(
        string='Evaluation Date',
        required=True,
        tracking=True
    )
    
    evaluator_id = fields.Many2one(
        'res.users',
        string='Evaluator',
        required=True,
        tracking=True
    )
    
    score = fields.Float(
        string='Score',
        required=True,
        tracking=True,
        help='Performance score (0-100)'
    )
    
    category = fields.Selection([
        ('quality', 'Quality'),
        ('delivery', 'Delivery'),
        ('communication', 'Communication'),
        ('cost', 'Cost'),
        ('overall', 'Overall')
    ], string='Category',
        required=True,
        tracking=True
    )
    
    comments = fields.Text(
        string='Comments',
        tracking=True
    )

class PartnerCommunication(models.Model):
    """Partner Communication Model"""
    _name = 'partner.communication'
    _description = 'Partner Communication'
    _order = 'date desc, id'

    name = fields.Char(
        string='Subject',
        required=True,
        tracking=True
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    date = fields.Datetime(
        string='Date',
        default=fields.Datetime.now,
        tracking=True
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='User',
        default=lambda self: self.env.user,
        tracking=True
    )
    
    type = fields.Selection([
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('mail', 'Mail'),
        ('in_person', 'In Person'),
        ('other', 'Other')
    ], string='Type',
        required=True,
        tracking=True
    )
    
    direction = fields.Selection([
        ('incoming', 'Incoming'),
        ('outgoing', 'Outgoing')
    ], string='Direction',
        required=True,
        tracking=True
    )
    
    content = fields.Text(
        string='Content',
        tracking=True
    )
    
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Attachments'
    ) 