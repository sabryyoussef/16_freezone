from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class TaskDocumentLines(models.Model):
    """
    Task Document Lines
    Manages document types for tasks
    """
    _name = 'task.document.lines'
    _description = 'Task Document Lines'
    _order = 'sequence, id'

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Order of document in the list'
    )
    
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        required=True,
        ondelete='cascade',
        index=True,
        help='Related project'
    )
    
    document_id = fields.Many2one(
        'res.partner.document.type',
        string='Document Type',
        required=True,
        tracking=True,
        help='Type of document'
    )
    
    is_required = fields.Boolean(
        string='Required',
        default=True,
        tracking=True,
        help='Whether this document is mandatory'
    )
    
    description = fields.Text(
        string='Description',
        help='Additional information about the document requirement'
    )
    
    validity_days = fields.Integer(
        string='Validity (Days)',
        help='Number of days the document remains valid'
    )

class TaskDocumentRequiredLines(models.Model):
    """
    Task Document Required Lines
    Manages mandatory documents for tasks
    """
    _name = 'task.document.required.lines'
    _description = 'Task Document Required Lines'
    _order = 'sequence, id'

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Order of document in the list'
    )
    
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        required=True,
        ondelete='cascade',
        index=True,
        help='Related project'
    )
    
    document_id = fields.Many2one(
        'res.partner.document.type',
        string='Document Type',
        required=True,
        tracking=True,
        help='Type of document'
    )
    
    is_required = fields.Boolean(
        string='Required',
        default=True,
        tracking=True,
        help='Whether this document is mandatory'
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
    
    description = fields.Text(
        string='Description',
        help='Additional information about the document requirement'
    )
    
    validity_days = fields.Integer(
        string='Validity (Days)',
        help='Number of days the document remains valid'
    ) 