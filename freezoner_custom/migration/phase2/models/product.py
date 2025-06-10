from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class ProductTemplateDocuments(models.Model):
    """
    Product Template Documents
    Manages required documents for product templates
    """
    _name = 'product.template.documents'
    _description = 'Product Template Documents'
    _order = 'sequence, id'

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Order of document in the list'
    )
    
    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Product Template',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    document_id = fields.Many2one(
        'res.partner.document.type',
        string='Document Type',
        required=True,
        tracking=True,
        help='Type of document required for this product'
    )
    
    is_required = fields.Boolean(
        string='Required',
        default=True,
        tracking=True,
        help='Whether this document is mandatory for the product'
    )
    
    description = fields.Text(
        string='Description',
        help='Additional information about the document requirement'
    )
    
    validity_days = fields.Integer(
        string='Validity (Days)',
        help='Number of days the document remains valid'
    )

class ProductTemplateRequiredDocuments(models.Model):
    """
    Product Template Required Documents
    Manages mandatory documents for product templates
    """
    _name = 'product.template.required.documents'
    _description = 'Product Template Required Documents'
    _order = 'sequence, id'

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Order of document in the list'
    )
    
    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Product Template',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    document_id = fields.Many2one(
        'res.partner.document.type',
        string='Document Type',
        required=True,
        tracking=True,
        help='Type of document required for this product'
    )
    
    is_required = fields.Boolean(
        string='Required',
        default=True,
        tracking=True,
        help='Whether this document is mandatory for the product'
    )
    
    validation_rule = fields.Selection([
        ('none', 'No Validation'),
        ('expiry', 'Check Expiry'),
        ('completeness', 'Check Completeness'),
        ('both', 'Check Both')
    ], string='Validation Rule',
        default='none',
        tracking=True,
        help='Rule to validate the document'
    )

class PartnerFields(models.Model):
    """
    Partner Fields for Products
    Manages required partner fields for products
    """
    _name = 'product.res.partner.fields'
    _description = 'Product Partner Fields'
    _order = 'sequence, id'

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Order of field in the list'
    )
    
    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Product Template',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    field_id = fields.Many2one(
        'ir.model.fields',
        string='Partner Field',
        domain="[('model','=', 'res.partner')]",
        required=True,
        tracking=True,
        help='Partner field required for this product',
        ondelete='cascade'
    )
    
    is_required = fields.Boolean(
        string='Required',
        default=True,
        tracking=True,
        help='Whether this field is mandatory for the product'
    )
    
    validation_rule = fields.Char(
        string='Validation Rule',
        help='Python expression for field validation'
    )
    
    help_text = fields.Text(
        string='Help Text',
        help='Additional information about the field requirement'
    )

class ProductTemplate(models.Model):
    """
    Enhanced Product Template
    Extends the base product template with additional features
    """
    _inherit = 'product.template'
    _inherit_mixin = ['mail.thread', 'mail.activity.mixin']
    _description = 'Enhanced Product Template'

    # Document Management
    partner_field_ids = fields.One2many(
        'product.res.partner.fields',
        'product_tmpl_id',
        string='Required Partner Fields',
        tracking=True
    )
    
    document_type_ids = fields.One2many(
        'product.template.documents',
        'product_tmpl_id',
        string='Document Types',
        tracking=True
    )
    
    document_required_type_ids = fields.One2many(
        'product.template.required.documents',
        'product_tmpl_id',
        string='Required Documents',
        tracking=True
    )
    
    # Task Management
    task_ids = fields.Many2many(
        'project.task',
        string='Related Tasks',
        domain="[('project_id.state','=','a_template')]",
        tracking=True
    )
    
    # Service Configuration
    is_service_commission = fields.Boolean(
        string='Service Commission',
        tracking=True,
        help='Whether this product is eligible for service commission'
    )
    
    stripe_visa = fields.Boolean(
        string='Stripe Visa',
        tracking=True,
        help='Whether this product supports Stripe Visa payments'
    )
    
    service_tracking = fields.Selection([
        ('manual', 'Manual'),
        ('automatic', 'Automatic'),
        ('new_workflow', 'New Workflow')
    ], string='Service Tracking',
        default='manual',
        tracking=True,
        help='How to track service delivery'
    )
    
    # Additional Features
    partner_validation_required = fields.Boolean(
        string='Partner Validation Required',
        default=False,
        tracking=True,
        help='Whether partner validation is required for this product'
    )
    
    document_validation_required = fields.Boolean(
        string='Document Validation Required',
        default=False,
        tracking=True,
        help='Whether document validation is required for this product'
    )
    
    max_partners = fields.Integer(
        string='Maximum Partners',
        tracking=True,
        help='Maximum number of partners allowed for this product'
    )
    
    validity_period = fields.Integer(
        string='Validity Period (Days)',
        tracking=True,
        help='Number of days the product remains valid'
    )

    # Computed Fields
    required_document_count = fields.Integer(
        string='Required Documents',
        compute='_compute_document_counts',
        store=True
    )
    
    optional_document_count = fields.Integer(
        string='Optional Documents',
        compute='_compute_document_counts',
        store=True
    )
    
    required_field_count = fields.Integer(
        string='Required Fields',
        compute='_compute_field_counts',
        store=True
    )

    @api.depends('document_type_ids', 'document_required_type_ids')
    def _compute_document_counts(self):
        for rec in self:
            rec.required_document_count = len(rec.document_required_type_ids.filtered(lambda d: d.is_required))
            rec.optional_document_count = len(rec.document_type_ids.filtered(lambda d: not d.is_required))

    @api.depends('partner_field_ids')
    def _compute_field_counts(self):
        for rec in self:
            rec.required_field_count = len(rec.partner_field_ids.filtered(lambda f: f.is_required))

    # Validation Methods
    @api.constrains('max_partners')
    def _check_max_partners(self):
        for rec in self:
            if rec.max_partners < 0:
                raise ValidationError(_('Maximum partners cannot be negative.'))

    @api.constrains('validity_period')
    def _check_validity_period(self):
        for rec in self:
            if rec.validity_period < 0:
                raise ValidationError(_('Validity period cannot be negative.'))

    # Action Methods
    def action_validate_partner(self, partner):
        """Validate partner against product requirements"""
        self.ensure_one()
        if not self.partner_validation_required:
            return True

        # Check required fields
        for field in self.partner_field_ids.filtered(lambda f: f.is_required):
            if not partner[field.field_id.name]:
                raise ValidationError(_(
                    'Required field %(field_name)s is missing for partner %(partner_name)s.'
                ) % {
                    'field_name': field.field_id.field_description,
                    'partner_name': partner.name
                })

        # Check required documents
        if self.document_validation_required:
            for doc in self.document_required_type_ids.filtered(lambda d: d.is_required):
                if not partner.document_ids.filtered(lambda d: d.type_id == doc.document_id):
                    raise ValidationError(_(
                        'Required document %(doc_name)s is missing for partner %(partner_name)s.'
                    ) % {
                        'doc_name': doc.document_id.name,
                        'partner_name': partner.name
                    })

        return True

class Product(models.Model):
    """
    Enhanced Product
    Extends the base product with additional features
    """
    _inherit = 'product.product'
    _inherit_mixin = ['mail.thread', 'mail.activity.mixin']
    _description = 'Enhanced Product'

    # Partner Relationship
    partner_ids = fields.Many2many(
        'res.partner',
        string='Partners',
        help='Partners associated with this product'
    )

    # Inherited Fields
    is_service_commission = fields.Boolean(
        related='product_tmpl_id.is_service_commission',
        store=True,
        readonly=False
    )
    
    # Additional Fields
    active_partner_count = fields.Integer(
        string='Active Partners',
        compute='_compute_partner_counts',
        store=True
    )
    
    document_completion_rate = fields.Float(
        string='Document Completion Rate',
        compute='_compute_document_completion',
        store=True,
        help='Percentage of required documents that are complete'
    )

    @api.depends('partner_ids', 'partner_ids.partner_status')
    def _compute_partner_counts(self):
        for rec in self:
            rec.active_partner_count = len(rec.partner_ids.filtered(
                lambda p: p.partner_status == 'active'
            ))

    @api.depends('partner_ids', 'partner_ids.document_ids')
    def _compute_document_completion(self):
        for rec in self:
            if not rec.product_tmpl_id.document_required_type_ids:
                rec.document_completion_rate = 100.0
                continue

            total_required = len(rec.product_tmpl_id.document_required_type_ids.filtered(
                lambda d: d.is_required
            ))
            if not total_required:
                rec.document_completion_rate = 100.0
                continue

            completed = 0
            for partner in rec.partner_ids:
                partner_docs = partner.document_ids.mapped('type_id')
                required_docs = rec.product_tmpl_id.document_required_type_ids.filtered(
                    lambda d: d.is_required
                ).mapped('document_id')
                if all(doc in partner_docs for doc in required_docs):
                    completed += 1

            rec.document_completion_rate = (completed / len(rec.partner_ids)) * 100 if rec.partner_ids else 0.0 