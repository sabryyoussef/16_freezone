from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class Document(models.Model):
    """
    Document Model Extension
    Extends the base document model with additional fields and functionality
    for enhanced document management
    """
    _inherit = 'documents.document'
    _description = 'Document Extension'

    # Project and Task Relations
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        tracking=True,
        help='Related project'
    )
    
    required_project_id = fields.Many2one(
        'project.project',
        string='Required Project',
        tracking=True,
        help='Project requiring this document'
    )
    
    deliverable_project_id = fields.Many2one(
        'project.project',
        string='Deliverable Project',
        tracking=True,
        help='Project delivering this document'
    )
    
    task_id = fields.Many2one(
        'project.task',
        string='Task',
        tracking=True,
        help='Related task'
    )
    
    task_ids = fields.Many2many(
        'project.task',
        string='Related Tasks',
        help='Tasks associated with this document'
    )

    # Document Details
    issue_date = fields.Date(
        string='Issue Date',
        required=True,
        tracking=True,
        help='Date when the document was issued'
    )
    
    type_id = fields.Many2one(
        'res.partner.document.type',
        string='Document Type',
        tracking=True,
        help='Type of document'
    )
    
    expiration_date = fields.Date(
        string='Expiration Date',
        tracking=True,
        help='Date when the document expires'
    )
    
    is_verify = fields.Boolean(
        string='Verified',
        default=False,
        tracking=True,
        help='Whether the document has been verified'
    )
    
    verification_date = fields.Datetime(
        string='Verification Date',
        tracking=True,
        help='Date when the document was verified'
    )
    
    verified_by = fields.Many2one(
        'res.users',
        string='Verified By',
        tracking=True,
        help='User who verified the document'
    )
    
    verification_notes = fields.Text(
        string='Verification Notes',
        tracking=True,
        help='Notes about document verification'
    )

    # Partner Relations
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        tracking=True,
        help='Partner associated with this document'
    )
    
    partner_ids = fields.Many2many(
        'res.partner',
        relation='document_partner_rel',
        column1='document_id',
        column2='partner_id',
        string='Related Partners',
        compute='_compute_partner_ids',
        store=True,
        help='Partners associated with this document'
    )

    # Sharing Fields
    lead_id = fields.Many2one(
        'crm.lead',
        string='Lead',
        tracking=True,
        help='Related lead'
    )
    
    share_access = fields.Selection([
        ('internal', 'Internal Only'),
        ('portal', 'Portal Users'),
        ('public', 'Public')
    ], string='Share Access',
        default='internal',
        tracking=True,
        help='Access level for document sharing'
    )
    
    share_token = fields.Char(
        string='Share Token',
        copy=False,
        help='Token for secure document sharing'
    )

    @api.depends('project_id', 'required_project_id', 'deliverable_project_id', 'partner_id')
    def _compute_partner_ids(self):
        for rec in self:
            partners = self.env['res.partner']
            if rec.partner_id:
                partners += rec.partner_id
            
            project = rec.project_id or rec.required_project_id or rec.deliverable_project_id
            if project:
                # Add project partners
                if project.partner_id:
                    partners += project.partner_id
                # Add project manager as partner
                if project.user_id and project.user_id.partner_id:
                    partners += project.user_id.partner_id
                # Add task assignees as partners
                task_assignees = project.task_ids.mapped('user_ids.partner_id')
                if task_assignees:
                    partners += task_assignees
                # Add compliance shareholders if they exist
                if hasattr(project, 'compliance_shareholder_ids'):
                    partners += project.compliance_shareholder_ids.mapped('contact_id')
            
            rec.partner_ids = partners

    def action_verify_document(self):
        """Verify the document"""
        self.ensure_one()
        if not self.is_verify:
            self.write({
                'is_verify': True,
                'verification_date': fields.Datetime.now(),
                'verified_by': self.env.user.id
            })
            # Log the verification
            self.message_post(
                body=_('Document verified by %s') % self.env.user.name,
                message_type='comment'
            )
        return True

    def action_unverify_document(self):
        """Unverify the document"""
        self.ensure_one()
        if self.is_verify:
            self.write({
                'is_verify': False,
                'verification_date': False,
                'verified_by': False,
                'verification_notes': False
            })
            # Log the unverification
            self.message_post(
                body=_('Document unverified by %s') % self.env.user.name,
                message_type='comment'
            )
        return True

    @api.constrains('expiration_date', 'issue_date')
    def _check_dates(self):
        for rec in self:
            if rec.expiration_date and rec.issue_date and rec.expiration_date < rec.issue_date:
                raise ValidationError(_('Expiration date cannot be earlier than issue date.'))

    def action_view_related_tasks(self):
        """Smart button to view related tasks"""
        self.ensure_one()
        return {
            'name': _('Related Tasks'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.task_ids.ids)],
            'context': {'create': False}
        }

    def action_view_related_partners(self):
        """Smart button to view related partners"""
        self.ensure_one()
        return {
            'name': _('Related Partners'),
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.partner_ids.ids)],
            'context': {'create': False}
        }

    def action_share_document(self):
        """Share document with external users"""
        self.ensure_one()
        if not self.share_token:
            self.share_token = self.env['ir.attachment']._generate_access_token()
        
        # Update access rights based on share_access
        if self.share_access == 'portal':
            self.access_token = self.share_token
        elif self.share_access == 'public':
            self.public = True
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/document/share/{self.id}?token={self.share_token}',
            'target': 'self'
        }

    def action_create_activity(self):
        """Open activity creation wizard"""
        return {
            'name': _('Create Activity'),
            'type': 'ir.actions.act_window',
            'res_model': 'files.activity.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('cabinet_directory.cabinet_meeting_form_view').id,
            'target': 'new'
        }

    def action_send_email(self):
        """Open email composition wizard"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_model': self._name,
                'default_res_id': self.id,
                'default_subject': self.name,
                'default_partner_ids': [self.partner_id.id] if self.partner_id else [],
                'default_composition_mode': 'comment',
            }
        } 