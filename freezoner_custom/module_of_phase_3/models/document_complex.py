from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class DocumentComplex(models.Model):
    """
    Complex Document Model
    Extends the base document model with advanced features:
    - Document versioning and history
    - Advanced metadata and categorization
    - Document workflows and approvals
    - Document templates
    - Document relationships and dependencies
    - Document quality and compliance
    """
    _inherit = 'documents.document'
    _description = 'Complex Document'
    _order = 'version_number desc, id'

    # Versioning Fields
    version_number = fields.Float(
        string='Version',
        default=1.0,
        tracking=True,
        help='Document version number'
    )
    
    version_ids = fields.One2many(
        'document.version',
        'document_id',
        string='Version History',
        help='Document version history'
    )
    
    is_latest_version = fields.Boolean(
        string='Latest Version',
        compute='_compute_is_latest_version',
        store=True,
        help='Indicates if this is the latest version'
    )
    
    previous_version_id = fields.Many2one(
        'documents.document',
        string='Previous Version',
        tracking=True,
        help='Previous version of this document'
    )
    
    next_version_id = fields.Many2one(
        'documents.document',
        string='Next Version',
        compute='_compute_next_version',
        store=True,
        help='Next version of this document'
    )

    # Metadata Fields
    document_type = fields.Selection([
        ('contract', 'Contract'),
        ('report', 'Report'),
        ('proposal', 'Proposal'),
        ('specification', 'Specification'),
        ('policy', 'Policy'),
        ('procedure', 'Procedure'),
        ('template', 'Template'),
        ('other', 'Other')
    ], string='Document Type',
        required=True,
        tracking=True,
        help='Type of document'
    )
    
    category_id = fields.Many2one(
        'document.category',
        string='Category',
        tracking=True,
        help='Document category'
    )
    
    tags = fields.Many2many(
        'document.tag',
        string='Tags',
        help='Document tags for better organization'
    )
    
    keywords = fields.Char(
        string='Keywords',
        help='Search keywords for the document'
    )
    
    expiry_date = fields.Date(
        string='Expiry Date',
        tracking=True,
        help='Document expiry date'
    )
    
    is_confidential = fields.Boolean(
        string='Confidential',
        default=False,
        tracking=True,
        help='Indicates if the document is confidential'
    )

    # Workflow Fields
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_review', 'In Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('archived', 'Archived')
    ], string='Status',
        default='draft',
        tracking=True,
        help='Document status'
    )
    
    reviewer_ids = fields.Many2many(
        'res.users',
        'document_reviewer_rel',
        'document_id',
        'user_id',
        string='Reviewers',
        help='Users responsible for reviewing the document'
    )
    
    approver_ids = fields.Many2many(
        'res.users',
        'document_approver_rel',
        'document_id',
        'user_id',
        string='Approvers',
        help='Users responsible for approving the document'
    )
    
    review_ids = fields.One2many(
        'document.review',
        'document_id',
        string='Reviews',
        help='Document review history'
    )
    
    approval_ids = fields.One2many(
        'document.approval',
        'document_id',
        string='Approvals',
        help='Document approval history'
    )

    # Template Fields
    is_template = fields.Boolean(
        string='Is Template',
        default=False,
        tracking=True,
        help='Indicates if this document is a template'
    )
    
    template_id = fields.Many2one(
        'documents.document',
        string='Based on Template',
        domain="[('is_template', '=', True)]",
        tracking=True,
        help='Template this document is based on'
    )

    # Relationship Fields
    related_document_ids = fields.Many2many(
        'documents.document',
        'document_relation_rel',
        'document_id',
        'related_document_id',
        string='Related Documents',
        help='Documents related to this document'
    )
    
    dependency_ids = fields.Many2many(
        'documents.document',
        'document_dependency_rel',
        'document_id',
        'dependency_id',
        string='Dependencies',
        domain="[('id', '!=', id)]",
        help='Documents this document depends on'
    )
    
    dependent_ids = fields.Many2many(
        'documents.document',
        'document_dependency_rel',
        'dependency_id',
        'document_id',
        string='Dependent Documents',
        help='Documents that depend on this document'
    )

    # Quality Fields
    quality_check_ids = fields.One2many(
        'document.quality.check',
        'document_id',
        string='Quality Checks',
        help='Quality control checks for this document'
    )
    
    quality_score = fields.Float(
        string='Quality Score',
        compute='_compute_quality_score',
        store=True,
        help='Overall quality score of the document'
    )
    
    compliance_ids = fields.Many2many(
        'document.compliance',
        string='Compliance Requirements',
        help='Compliance requirements for this document'
    )

    # Computed Methods
    @api.depends('version_number', 'version_ids')
    def _compute_is_latest_version(self):
        for doc in self:
            latest_version = doc.version_ids.sorted('version_number', reverse=True)[:1]
            doc.is_latest_version = doc.version_number == latest_version.version_number if latest_version else True

    @api.depends('version_ids')
    def _compute_next_version(self):
        for doc in self:
            next_version = doc.version_ids.filtered(
                lambda v: v.version_number > doc.version_number
            ).sorted('version_number')[:1]
            doc.next_version_id = next_version.document_id if next_version else False

    @api.depends('quality_check_ids', 'quality_check_ids.score')
    def _compute_quality_score(self):
        for doc in self:
            checks = doc.quality_check_ids.filtered(lambda c: c.score is not False)
            doc.quality_score = sum(checks.mapped('score')) / len(checks) if checks else 0.0

    # Constraint Methods
    @api.constrains('dependency_ids')
    def _check_dependencies(self):
        for doc in self:
            if doc in doc.dependency_ids:
                raise ValidationError(_('A document cannot depend on itself.'))

    # Action Methods
    def action_view_versions(self):
        return {
            'name': _('Version History'),
            'type': 'ir.actions.act_window',
            'res_model': 'document.version',
            'view_mode': 'tree,form',
            'domain': [('document_id', '=', self.id)],
            'context': {'default_document_id': self.id}
        }

    def action_view_reviews(self):
        return {
            'name': _('Reviews'),
            'type': 'ir.actions.act_window',
            'res_model': 'document.review',
            'view_mode': 'tree,form',
            'domain': [('document_id', '=', self.id)],
            'context': {'default_document_id': self.id}
        }

    def action_view_approvals(self):
        return {
            'name': _('Approvals'),
            'type': 'ir.actions.act_window',
            'res_model': 'document.approval',
            'view_mode': 'tree,form',
            'domain': [('document_id', '=', self.id)],
            'context': {'default_document_id': self.id}
        }

    def action_create_new_version(self):
        self.ensure_one()
        return {
            'name': _('Create New Version'),
            'type': 'ir.actions.act_window',
            'res_model': 'document.create.version',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_document_id': self.id}
        }

    def action_create_from_template(self):
        self.ensure_one()
        if not self.is_template:
            raise UserError(_('Only template documents can be used to create new documents.'))
        
        return {
            'name': _('Create Document from Template'),
            'type': 'ir.actions.act_window',
            'res_model': 'document.create.from.template',
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
                raise UserError(_('The selected document is not a template.'))
            # Copy relevant fields from template
            vals.update(self._get_template_vals(template))
        
        return super(DocumentComplex, self).create(vals)

    def _get_template_vals(self, template):
        """Get values to copy from template"""
        return {
            'document_type': template.document_type,
            'category_id': template.category_id.id,
            'tags': [(6, 0, template.tags.ids)],
            'is_confidential': template.is_confidential,
            'compliance_ids': [(6, 0, template.compliance_ids.ids)],
            'quality_check_ids': [(0, 0, {
                'name': q.name,
                'description': q.description,
                'check_type': q.check_type,
                'required_score': q.required_score
            }) for q in template.quality_check_ids]
        }

class DocumentVersion(models.Model):
    """Document Version Model"""
    _name = 'document.version'
    _description = 'Document Version'
    _order = 'version_number desc, id'

    name = fields.Char(
        string='Name',
        required=True,
        tracking=True
    )
    
    document_id = fields.Many2one(
        'documents.document',
        string='Document',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    version_number = fields.Float(
        string='Version',
        required=True,
        tracking=True
    )
    
    date = fields.Datetime(
        string='Version Date',
        default=fields.Datetime.now,
        tracking=True
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='Created By',
        default=lambda self: self.env.user,
        tracking=True
    )
    
    changes = fields.Text(
        string='Changes',
        tracking=True,
        help='Description of changes in this version'
    )
    
    attachment_id = fields.Many2one(
        'ir.attachment',
        string='Attachment',
        required=True,
        tracking=True
    )

class DocumentReview(models.Model):
    """Document Review Model"""
    _name = 'document.review'
    _description = 'Document Review'
    _order = 'date desc, id'

    name = fields.Char(
        string='Name',
        required=True,
        tracking=True
    )
    
    document_id = fields.Many2one(
        'documents.document',
        string='Document',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    reviewer_id = fields.Many2one(
        'res.users',
        string='Reviewer',
        required=True,
        tracking=True
    )
    
    date = fields.Datetime(
        string='Review Date',
        default=fields.Datetime.now,
        tracking=True
    )
    
    state = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status',
        default='pending',
        tracking=True
    )
    
    comments = fields.Text(
        string='Comments',
        tracking=True
    )
    
    score = fields.Float(
        string='Score',
        tracking=True,
        help='Review score'
    )

class DocumentApproval(models.Model):
    """Document Approval Model"""
    _name = 'document.approval'
    _description = 'Document Approval'
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
    
    document_id = fields.Many2one(
        'documents.document',
        string='Document',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    approver_id = fields.Many2one(
        'res.users',
        string='Approver',
        required=True,
        tracking=True
    )
    
    date = fields.Datetime(
        string='Approval Date',
        tracking=True
    )
    
    state = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status',
        default='pending',
        tracking=True
    )
    
    comments = fields.Text(
        string='Comments',
        tracking=True
    )

class DocumentQualityCheck(models.Model):
    """Document Quality Check Model"""
    _name = 'document.quality.check'
    _description = 'Document Quality Check'
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
    
    document_id = fields.Many2one(
        'documents.document',
        string='Document',
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

class DocumentCategory(models.Model):
    """Document Category Model"""
    _name = 'document.category'
    _description = 'Document Category'
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
        'document.category',
        string='Parent Category',
        tracking=True
    )
    
    child_ids = fields.One2many(
        'document.category',
        'parent_id',
        string='Child Categories'
    )

class DocumentTag(models.Model):
    """Document Tag Model"""
    _name = 'document.tag'
    _description = 'Document Tag'
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

class DocumentCompliance(models.Model):
    """Document Compliance Model"""
    _name = 'document.compliance'
    _description = 'Document Compliance'
    _order = 'name'

    name = fields.Char(
        string='Name',
        required=True,
        tracking=True
    )
    
    code = fields.Char(
        string='Code',
        tracking=True,
        help='Compliance requirement code'
    )
    
    description = fields.Text(
        string='Description',
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
    
    is_mandatory = fields.Boolean(
        string='Mandatory',
        default=False,
        tracking=True,
        help='Indicates if this is a mandatory requirement'
    )
    
    validity_period = fields.Integer(
        string='Validity Period (Days)',
        tracking=True,
        help='Number of days the compliance is valid'
    )
    
    document_ids = fields.Many2many(
        'documents.document',
        string='Compliant Documents'
    ) 