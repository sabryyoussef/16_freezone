from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import html_escape
from markupsafe import Markup
from urllib.parse import urlencode
import re
import logging

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    """
    Enhanced Partner Model for Odoo 18
    Extends the base partner model with additional features and improved validation
    """
    _inherit = 'res.partner'
    _inherit_mixin = ['mail.thread', 'mail.activity.mixin']
    _description = 'Enhanced Partner'

    # Enhanced Fields
    project_product_ids = fields.Many2many(
        'project.project.products',
        compute='_compute_project_product_ids',
        string='Project Products',
        tracking=True,
        help='Products associated with this partner in projects'
    )
    
    partner_type = fields.Selection([
        ('customer', 'Customer'),
        ('vendor', 'Vendor'),
        ('both', 'Customer & Vendor'),
        ('other', 'Other')
    ], string='Partner Type',
        tracking=True,
        help='Type of business relationship'
    )
    
    partner_status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending Review'),
        ('blocked', 'Blocked')
    ], string='Partner Status',
        default='active',
        tracking=True,
        help='Current status of the partner relationship'
    )
    
    last_review_date = fields.Date(
        string='Last Review Date',
        tracking=True,
        help='Date of last partner review'
    )
    
    next_review_date = fields.Date(
        string='Next Review Date',
        tracking=True,
        help='Date of next scheduled partner review'
    )
    
    partner_score = fields.Float(
        string='Partner Score',
        compute='_compute_partner_score',
        store=True,
        tracking=True,
        help='Overall partner performance score'
    )
    
    document_ids = fields.One2many(
        'documents.document',
        'partner_id',
        string='Documents',
        help='Documents associated with this partner'
    )
    
    document_count = fields.Integer(
        string='Document Count',
        compute='_compute_document_count',
        help='Number of documents associated with this partner'
    )
    
    project_count = fields.Integer(
        string='Project Count',
        compute='_compute_project_count',
        help='Number of projects associated with this partner'
    )

    # Computed Methods
    @api.depends('project_product_ids')
    def _compute_project_product_ids(self):
        for rec in self:
            projects = self.env['project.project.products'].sudo().search([
                ('partner_id', '=', rec.id)
            ])
            rec.project_product_ids = projects

    @api.depends('project_count', 'document_count')
    def _compute_partner_score(self):
        for rec in self:
            # Implement scoring logic based on various factors
            base_score = 50.0
            if rec.project_count > 0:
                base_score += min(rec.project_count * 5, 30)
            if rec.document_count > 0:
                base_score += min(rec.document_count * 2, 20)
            rec.partner_score = min(base_score, 100.0)

    @api.depends('document_ids')
    def _compute_document_count(self):
        for rec in self:
            rec.document_count = len(rec.document_ids)

    @api.depends('project_ids')
    def _compute_project_count(self):
        for rec in self:
            rec.project_count = len(rec.project_ids)

    # Enhanced Validation Methods
    @api.constrains('phone', 'mobile', 'email')
    def _check_contact_info_uniqueness(self):
        """Enhanced validation for contact information uniqueness"""
        for rec in self:
            # Skip validation for parent companies
            if rec.is_company:
                continue

            # Helper function to clean contact info
            def clean_contact_info(value):
                return value.replace(" ", "").lower() if value else ""

            # Get all contact info
            phone = clean_contact_info(rec.phone)
            mobile = clean_contact_info(rec.mobile)
            email = clean_contact_info(rec.email)

            # Check for duplicates within the same company
            domain = [
                ('id', '!=', rec.id),
                ('company_id', '=', rec.company_id.id),
                '|', '|',
                ('phone', '=', phone) if phone else ('id', '=', False),
                ('mobile', '=', mobile) if mobile else ('id', '=', False),
                ('email', '=', email) if email else ('id', '=', False)
            ]

            duplicates = self.search(domain, limit=1)
            if duplicates:
                # Prepare error message with clickable link
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                action_id = self.env.ref('base.action_partner_form').id
                menu_id = self.env.ref('contacts.menu_contacts').id
                
                url_params = {
                    'id': duplicates.id,
                    'menu_id': menu_id,
                    'cids': self.env.company.id,
                    'action': action_id,
                    'model': 'res.partner',
                    'view_type': 'form',
                }
                
                partner_url = f"{base_url}/web?{urlencode(url_params)}"
                
                # Determine which field caused the duplicate
                duplicate_fields = []
                if phone and duplicates.phone == phone:
                    duplicate_fields.append('Phone')
                if mobile and duplicates.mobile == mobile:
                    duplicate_fields.append('Mobile')
                if email and duplicates.email == email:
                    duplicate_fields.append('Email')
                
                raise ValidationError(_(
                    'The following contact information already exists for another partner:\n'
                    '%(fields)s\n\n'
                    'Partner: %(partner_name)s\n'
                    'View Partner: %(partner_url)s'
                ) % {
                    'fields': '\n'.join(duplicate_fields),
                    'partner_name': duplicates.name,
                    'partner_url': partner_url
                })

    # Action Methods
    def action_review_partner(self):
        """Schedule a partner review"""
        self.ensure_one()
        return {
            'name': _('Schedule Partner Review'),
            'type': 'ir.actions.act_window',
            'res_model': 'partner.review.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
                'default_review_type': 'scheduled'
            }
        }

    def action_block_partner(self):
        """Block a partner"""
        self.ensure_one()
        if self.partner_status != 'blocked':
            self.write({
                'partner_status': 'blocked',
                'message_post': _('Partner has been blocked')
            })
        return True

    def action_unblock_partner(self):
        """Unblock a partner"""
        self.ensure_one()
        if self.partner_status == 'blocked':
            self.write({
                'partner_status': 'active',
                'message_post': _('Partner has been unblocked')
            })
        return True

    # Override Methods
    @api.model_create_multi
    def create(self, vals_list):
        """Enhanced create method with additional validation"""
        partners = super().create(vals_list)
        for partner in partners:
            if not partner.is_company:
                partner._check_contact_info_uniqueness()
        return partners

    def write(self, vals):
        """Enhanced write method with additional validation"""
        res = super().write(vals)
        if any(field in vals for field in ['phone', 'mobile', 'email', 'parent_partner_ids']):
            for rec in self:
                if not rec.is_company:
                    rec._check_contact_info_uniqueness()
        return res

    def name_get(self):
        """Enhanced name_get to include partner type"""
        result = []
        for partner in self:
            name = partner.name
            if partner.partner_type and not partner.is_company:
                name = f"{name} ({dict(partner._fields['partner_type'].selection).get(partner.partner_type)})"
            result.append((partner.id, name))
        return result 