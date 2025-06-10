from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class ComplianceRequirement(models.Model):
    """
    Compliance Requirement Model
    Manages compliance requirements and standards:
    - Requirement definitions and categories
    - Compliance rules and validations
    - Compliance assessments and audits
    - Compliance reporting and tracking
    - Compliance notifications and alerts
    """
    _name = 'compliance.requirement'
    _description = 'Compliance Requirement'
    _order = 'sequence, name'

    # Basic Fields
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Order of requirements in the list'
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
        help='Unique requirement code'
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

    # Category Fields
    category_id = fields.Many2one(
        'compliance.category',
        string='Category',
        required=True,
        tracking=True,
        help='Requirement category'
    )
    
    subcategory_ids = fields.Many2many(
        'compliance.subcategory',
        string='Subcategories',
        help='Requirement subcategories'
    )
    
    tags = fields.Many2many(
        'compliance.tag',
        string='Tags',
        help='Requirement tags'
    )

    # Rule Fields
    rule_type = fields.Selection([
        ('document', 'Document'),
        ('process', 'Process'),
        ('training', 'Training'),
        ('certification', 'Certification'),
        ('other', 'Other')
    ], string='Rule Type',
        required=True,
        tracking=True
    )
    
    validation_criteria = fields.Text(
        string='Validation Criteria',
        tracking=True,
        help='Criteria for validating compliance'
    )
    
    is_mandatory = fields.Boolean(
        string='Mandatory',
        default=False,
        tracking=True,
        help='Indicates if this is a mandatory requirement'
    )
    
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], string='Priority',
        required=True,
        tracking=True
    )

    # Timeline Fields
    effective_date = fields.Date(
        string='Effective Date',
        required=True,
        tracking=True
    )
    
    expiry_date = fields.Date(
        string='Expiry Date',
        tracking=True
    )
    
    review_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('biannual', 'Biannual'),
        ('annual', 'Annual'),
        ('custom', 'Custom')
    ], string='Review Frequency',
        required=True,
        tracking=True
    )
    
    custom_review_days = fields.Integer(
        string='Custom Review Days',
        tracking=True,
        help='Number of days between reviews (for custom frequency)'
    )

    # Relationship Fields
    parent_id = fields.Many2one(
        'compliance.requirement',
        string='Parent Requirement',
        tracking=True,
        help='Parent requirement in the hierarchy'
    )
    
    child_ids = fields.One2many(
        'compliance.requirement',
        'parent_id',
        string='Child Requirements',
        help='Child requirements in the hierarchy'
    )
    
    related_requirement_ids = fields.Many2many(
        'compliance.requirement',
        'compliance_requirement_rel',
        'requirement_id',
        'related_id',
        string='Related Requirements',
        help='Related compliance requirements'
    )

    # Assessment Fields
    assessment_ids = fields.One2many(
        'compliance.assessment',
        'requirement_id',
        string='Assessments',
        help='Compliance assessments'
    )
    
    last_assessment_date = fields.Date(
        string='Last Assessment',
        compute='_compute_last_assessment_date',
        store=True
    )
    
    compliance_status = fields.Selection([
        ('compliant', 'Compliant'),
        ('non_compliant', 'Non-Compliant'),
        ('pending', 'Pending'),
        ('expired', 'Expired')
    ], string='Compliance Status',
        compute='_compute_compliance_status',
        store=True
    )

    # Notification Fields
    notify_before_days = fields.Integer(
        string='Notify Before (Days)',
        default=30,
        tracking=True,
        help='Days before expiry to send notification'
    )
    
    notify_user_ids = fields.Many2many(
        'res.users',
        string='Notify Users',
        help='Users to notify about compliance status'
    )

    # Computed Methods
    @api.depends('assessment_ids', 'assessment_ids.date')
    def _compute_last_assessment_date(self):
        for req in self:
            last_assessment = req.assessment_ids.sorted('date', reverse=True)[:1]
            req.last_assessment_date = last_assessment.date if last_assessment else False

    @api.depends('assessment_ids', 'assessment_ids.status', 'expiry_date')
    def _compute_compliance_status(self):
        for req in self:
            if not req.assessment_ids:
                req.compliance_status = 'pending'
            elif req.expiry_date and req.expiry_date < fields.Date.today():
                req.compliance_status = 'expired'
            else:
                last_assessment = req.assessment_ids.sorted('date', reverse=True)[:1]
                req.compliance_status = last_assessment.status if last_assessment else 'pending'

    # Constraint Methods
    @api.constrains('parent_id')
    def _check_parent_id(self):
        for req in self:
            if req.parent_id:
                if req.parent_id == req:
                    raise ValidationError(_('A requirement cannot be its own parent.'))
                if req.parent_id in req.child_ids:
                    raise ValidationError(_('Circular dependency detected in requirement hierarchy.'))

    @api.constrains('custom_review_days')
    def _check_custom_review_days(self):
        for req in self:
            if req.review_frequency == 'custom' and not req.custom_review_days:
                raise ValidationError(_('Custom review days must be specified for custom review frequency.'))

    # Action Methods
    def action_view_assessments(self):
        return {
            'name': _('Assessments'),
            'type': 'ir.actions.act_window',
            'res_model': 'compliance.assessment',
            'view_mode': 'tree,form',
            'domain': [('requirement_id', '=', self.id)],
            'context': {'default_requirement_id': self.id}
        }

    def action_create_assessment(self):
        self.ensure_one()
        return {
            'name': _('Create Assessment'),
            'type': 'ir.actions.act_window',
            'res_model': 'compliance.assessment',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_requirement_id': self.id}
        }

class ComplianceCategory(models.Model):
    """Compliance Category Model"""
    _name = 'compliance.category'
    _description = 'Compliance Category'
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
        help='Category code for reference'
    )
    
    description = fields.Text(
        string='Description'
    )
    
    parent_id = fields.Many2one(
        'compliance.category',
        string='Parent Category',
        tracking=True
    )
    
    child_ids = fields.One2many(
        'compliance.category',
        'parent_id',
        string='Child Categories'
    )
    
    requirement_ids = fields.One2many(
        'compliance.requirement',
        'category_id',
        string='Requirements'
    )

class ComplianceSubcategory(models.Model):
    """Compliance Subcategory Model"""
    _name = 'compliance.subcategory'
    _description = 'Compliance Subcategory'
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
        help='Subcategory code for reference'
    )
    
    description = fields.Text(
        string='Description'
    )
    
    category_id = fields.Many2one(
        'compliance.category',
        string='Category',
        required=True,
        tracking=True
    )
    
    requirement_ids = fields.Many2many(
        'compliance.requirement',
        string='Requirements'
    )

class ComplianceTag(models.Model):
    """Compliance Tag Model"""
    _name = 'compliance.tag'
    _description = 'Compliance Tag'
    _order = 'name'

    name = fields.Char(
        string='Name',
        required=True,
        tracking=True
    )
    
    color = fields.Integer(
        string='Color Index',
        default=0
    )
    
    description = fields.Text(
        string='Description'
    )

class ComplianceAssessment(models.Model):
    """Compliance Assessment Model"""
    _name = 'compliance.assessment'
    _description = 'Compliance Assessment'
    _order = 'date desc, id'

    name = fields.Char(
        string='Name',
        required=True,
        tracking=True
    )
    
    requirement_id = fields.Many2one(
        'compliance.requirement',
        string='Requirement',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    date = fields.Date(
        string='Assessment Date',
        required=True,
        tracking=True
    )
    
    assessor_id = fields.Many2one(
        'res.users',
        string='Assessor',
        required=True,
        tracking=True
    )
    
    status = fields.Selection([
        ('compliant', 'Compliant'),
        ('non_compliant', 'Non-Compliant'),
        ('pending', 'Pending')
    ], string='Status',
        required=True,
        tracking=True
    )
    
    score = fields.Float(
        string='Score',
        tracking=True,
        help='Assessment score (0-100)'
    )
    
    findings = fields.Text(
        string='Findings',
        tracking=True
    )
    
    recommendations = fields.Text(
        string='Recommendations',
        tracking=True
    )
    
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Attachments'
    )
    
    next_assessment_date = fields.Date(
        string='Next Assessment',
        compute='_compute_next_assessment_date',
        store=True
    )

    @api.depends('requirement_id', 'requirement_id.review_frequency',
                'requirement_id.custom_review_days', 'date')
    def _compute_next_assessment_date(self):
        for assessment in self:
            if not assessment.date:
                assessment.next_assessment_date = False
                continue
            
            req = assessment.requirement_id
            if req.review_frequency == 'monthly':
                delta = relativedelta(months=1)
            elif req.review_frequency == 'quarterly':
                delta = relativedelta(months=3)
            elif req.review_frequency == 'biannual':
                delta = relativedelta(months=6)
            elif req.review_frequency == 'annual':
                delta = relativedelta(years=1)
            elif req.review_frequency == 'custom':
                delta = relativedelta(days=req.custom_review_days)
            else:
                assessment.next_assessment_date = False
                continue
            
            assessment.next_assessment_date = assessment.date + delta 