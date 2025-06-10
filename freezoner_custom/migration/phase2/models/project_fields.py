from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import re
import logging

_logger = logging.getLogger(__name__)

class ProjectPartnerFields(models.Model):
    """
    Project Partner Fields Model
    Manages partner fields for projects with enhanced validation and update capabilities
    """
    _name = 'project.partner.fields'
    _description = 'Project Partner Fields'
    _order = 'id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Basic Fields
    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True,
        help='Name of the field record'
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        related='project_id.partner_id',
        string='Partner',
        store=True,
        readonly=True,
        help='Related partner from the project'
    )
    
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    field_id = fields.Many2one(
        'ir.model.fields',
        string='Field',
        domain="[('model','=', 'res.partner')]",
        required=True,
        ondelete='cascade',
        index=True
    )
    
    field_name = fields.Char(
        related='field_id.name',
        string='Field Name',
        store=True,
        help='Name of the field'
    )
    
    field_type = fields.Selection(
        related='field_id.ttype',
        string='Field Type',
        store=True,
        help='Type of the field'
    )

    # Value Fields
    is_required = fields.Boolean(
        string='Required',
        readonly=True,
        help='Indicates if this field is required'
    )
    
    current_value = fields.Char(
        string='Current Value',
        help='Current value of the field'
    )
    
    update_value = fields.Char(
        string='Update Value',
        help='New value to update the field with'
    )
    
    is_line_readonly = fields.Boolean(
        string='Read Only',
        copy=False,
        help='Indicates if this line is read-only'
    )

    # Special Fields
    state_id = fields.Many2one(
        'res.country.state',
        string='State',
        help='State field for address-related fields'
    )

    # Methods
    def update_values(self):
        """Update field values based on field type"""
        for rec in self:
            if not rec.field_id or not rec.update_value:
                continue

            try:
                if rec.field_id.ttype == 'many2one':
                    # Handle many2one fields
                    match = re.search(r'\((\d+),?\)', str(rec.update_value))
                    if match:
                        record = self.env[rec.field_id.relation].sudo().browse(int(match.group(1)))
                        rec.update_value = record.name if record else ''

                elif rec.field_id.ttype == 'many2many':
                    # Handle many2many fields
                    ids = [re.search(r'\((\d+),?\)', str(line)) for line in rec.current_value]
                    ids = [match.group(1) for match in ids if match]
                    records = self.env[rec.field_id.relation].sudo().browse([int(id) for id in ids])
                    rec.update_value = ', '.join(records.mapped('name')) if records else ''

            except Exception as e:
                _logger.error('Error updating field values: %s', str(e))
                raise ValidationError(_('Error updating field values: %s') % str(e))

    def action_update_relation_fields(self, many2one_id=None):
        """Update relation fields (many2one)"""
        for rec in self:
            if not rec.field_id or not rec.partner_id:
                continue

            try:
                field_name = rec.field_id.name
                if not hasattr(rec.partner_id, field_name):
                    raise ValidationError(_('Field "%s" does not exist on the partner model.') % field_name)

                if not many2one_id:
                    raise ValidationError(_('No value provided for the field update.'))

                # Update the partner field
                rec.partner_id.with_context(skip_validation=True).write({field_name: many2one_id})
                rec.update_value = many2one_id
                rec.update_values()

            except Exception as e:
                _logger.error('Error updating relation field: %s', str(e))
                raise ValidationError(_('Error updating field value: %s') % str(e))

    def action_update_many2many_fields(self, many2many_ids=None):
        """Update many2many fields"""
        for rec in self:
            if not rec.field_id or not rec.partner_id:
                continue

            try:
                field_name = rec.field_id.name
                if not hasattr(rec.partner_id, field_name):
                    raise ValidationError(_('Field "%s" does not exist on the partner model.') % field_name)

                if not many2many_ids or not many2many_ids.exists():
                    raise ValidationError(_('No valid records provided to update the Many2many field.'))

                if len(many2many_ids) > 1:
                    raise ValidationError(_('Please select only one value from partner assessment.'))

                # Update the partner field
                new_id = many2many_ids[0].id
                rec.partner_id.with_context(skip_validation=True).write({
                    field_name: [(6, 0, [new_id])]
                })
                rec.update_value = new_id
                rec.update_values()

            except Exception as e:
                _logger.error('Error updating many2many field: %s', str(e))
                raise ValidationError(_('Error updating Many2many field value: %s') % str(e))

    def action_update_normal_fields(self):
        """Update normal fields (char, text, boolean, etc.)"""
        for rec in self:
            if not rec.field_id or not rec.partner_id:
                continue

            try:
                field_name = rec.field_id.name
                if not hasattr(rec.partner_id, field_name):
                    raise ValidationError(_('Field "%s" does not exist on the partner model.') % field_name)

                # Handle boolean fields
                if rec.field_type == 'boolean':
                    update_value = bool(rec.update_value)
                else:
                    update_value = rec.update_value
                    if not update_value:
                        raise ValidationError(_('No value provided for the field update.'))

                # Update the partner field
                rec.partner_id.with_context(skip_validation=True).write({field_name: update_value})
                rec.update_value = update_value
                rec.update_values()

            except Exception as e:
                _logger.error('Error updating normal field: %s', str(e))
                raise ValidationError(_('Error updating field value: %s') % str(e))

    def action_update_lines(self):
        """Open update fields wizard"""
        self.ensure_one()
        return {
            'name': _('Update Field'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.update.fields',
            'view_mode': 'form',
            'view_id': self.env.ref('freezoner_custom.project_update_fields_form_view').id,
            'target': 'new',
            'context': {'default_line_id': self.id}
        }

    def action_reset(self):
        """Reset line to editable state"""
        self.ensure_one()
        self.write({'is_line_readonly': False})
        return True

    def action_retain_value(self):
        """Make line read-only"""
        self.ensure_one()
        self.write({'is_line_readonly': True})
        return True

    # Model Methods
    @api.model
    def create(self, vals):
        """Override create to set initial values"""
        if vals.get('field_id'):
            field = self.env['ir.model.fields'].browse(vals['field_id'])
            if field.ttype == 'boolean':
                vals['update_value'] = False
        return super(ProjectPartnerFields, self).create(vals)

    def write(self, vals):
        """Override write to handle field updates"""
        if vals.get('field_id'):
            field = self.env['ir.model.fields'].browse(vals['field_id'])
            if field.ttype == 'boolean':
                vals['update_value'] = False
        return super(ProjectPartnerFields, self).write(vals)

    @api.depends('field_id', 'project_id')
    def _compute_name(self):
        for rec in self:
            if rec.field_id and rec.project_id:
                rec.name = f"{rec.project_id.name} - {rec.field_id.name}"
            else:
                rec.name = "New Partner Field" 