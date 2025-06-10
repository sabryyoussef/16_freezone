
import ast
import json
from pytz import UTC
from collections import defaultdict
from datetime import timedelta, datetime, time
from random import randint

from odoo import api, Command, fields, models, tools, SUPERUSER_ID, _, _lt
from odoo.addons.rating.models import rating_data
from odoo.addons.web_editor.controllers.main import handle_history_divergence
from odoo.exceptions import UserError, ValidationError, AccessError
import re


class ProjectPartnerFields(models.Model):
    _name = 'project.res.partner.fields'

    partner_id = fields.Many2one('res.partner', related='project_id.partner_id', string='Partner')
    project_id = fields.Many2one('project.project')
    field_id = fields.Many2one('ir.model.fields', domain="[('model','=', 'res.partner')]", readonly=False)
    is_required = fields.Boolean('Check Required', readonly=True)
    current_value = fields.Char(string="Current Value")
    update_value = fields.Char(string="Update Value")
    is_line_readonly = fields.Boolean('Is Line Readonly', copy=False)

    state_id = fields.Many2one('res.country.state', string='State')
    field_name = fields.Char(related='field_id.name', string='Field Name')
    field_type = fields.Selection(related='field_id.ttype', string='Field Type')

    def update_values(self):
        for rec in self:
            if rec.field_id.ttype == 'many2one':
                match = re.search(r'\((\d+),?\)', str(rec.update_value))
                if match:
                    record = self.env[rec.field_id.relation].sudo().browse(int(match.group(1)))
                    rec.update_value = record.name if record else ''

            elif rec.field_id.ttype == 'many2many':
                ids = [re.search(r'\((\d+),?\)', str(line)) for line in rec.current_value]
                ids = [match.group(1) for match in ids if match]
                records = self.env[rec.field_id.relation].sudo().browse([int(id) for id in ids])
                rec.update_value = ', '.join(records.mapped('name')) if records else ''

    def action_update_relation_fields(self,many2one_id=None):
        for rec in self:
            rec.update_value = ''
            if rec.field_id and rec.hand_partner_id:
                field_name = rec.field_id.name
                if not hasattr(rec.hand_partner_id, field_name):
                    raise ValidationError(_('Field "%s" does not exist on the partner model.') % field_name)

                # Determine the value to update
                update_value = many2one_id
                if not update_value:
                    raise ValidationError(_('No value provided for the field update.'))
                try:
                    # Update the partner field with the determined value
                    setattr(rec.hand_partner_id, field_name, update_value)
                    # Save the partner record to persist changes
                    rec.hand_partner_id.with_context(skip_validation=True).write({field_name: update_value})
                    rec.update_value = update_value
                    rec.update_values()
                except Exception as e:
                    raise ValidationError(_('Error updating field value: %s') % str(e))

    def action_update_many2many_fields(self, many2many_ids=None):
        for rec in self:
            rec.update_value = ''

            if rec.field_id and rec.hand_partner_id:
                field_name = rec.field_id.name

                if not hasattr(rec.hand_partner_id, field_name):
                    raise ValidationError(_('Field "%s" does not exist on the partner model.') % field_name)

                if not many2many_ids or not many2many_ids.exists():
                    raise ValidationError(_('No valid records provided to update the Many2many field.'))

                try:
                    # Ensure only one record is selected for Many2many field
                    if len(many2many_ids) > 1:
                        raise ValidationError(_('Please select only one value from partner assessment.'))

                    new_id = many2many_ids[0].id  # Get the ID of the single selected record

                    rec.hand_partner_id.with_context(skip_validation=True).write({
                        field_name: [(6, 0, [new_id])]  # Update with a single ID
                    })

                    rec.update_value = new_id
                    rec.update_values()

                except Exception as e:
                    raise ValidationError(_('Error updating Many2many field value: %s') % str(e))
            else:
                raise ValidationError(_('Field or Partner is not set on the record.'))

    def action_update_normal_fields(self):
        for rec in self:
            if rec.field_id and rec.hand_partner_id:
                field_name = rec.field_id.name
                if not hasattr(rec.hand_partner_id, field_name):
                    raise ValidationError(_('Field "%s" does not exist on the partner model.') % field_name)

                # Determine the value to update
                update_value = rec.update_value

                # Handle boolean fields specifically
                if rec.field_type == 'boolean':
                    if rec.update_value is False:
                        update_value = False
                elif not update_value:
                    raise ValidationError(_('No value provided for the field update.'))

                try:
                    # Update the partner field with the determined value
                    setattr(rec.hand_partner_id, field_name, update_value)
                    # Save the partner record to persist changes
                    rec.hand_partner_id.with_context(skip_validation=True).write({field_name: update_value})
                    rec.update_value = update_value
                    rec.update_values()
                except Exception as e:
                    raise ValidationError(_('Error updating field value: %s') % str(e))

    def action_update_lines(self):
        for rec in self:
            return {
                'res_model': 'project.update.fields',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
                'context': {'default_line_id': rec.id},
                'view_id': self.env.ref("freezoner_custom.project_update_fields_form_view").id,
                'target': 'new'
            }

    def action_reset(self):
        for rec in self:
            rec.is_line_readonly = False

    def action_retain_value(self):
        for rec in self:
            rec.is_line_readonly = True

