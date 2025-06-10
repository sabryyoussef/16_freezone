
from odoo import api, fields, models

class FieldsUpdate(models.TransientModel):
    _inherit = 'project.update.fields'

    nationality_id = fields.Many2one('res.nationality', string='Nationality')
    business_structure_id = fields.Many2one('business.structure', string='Business Structure')

    def action_update(self):
        res = super(FieldsUpdate, self).action_update()
        for rec in self:
            if rec.field_ttype == 'many2one':
                if rec.nationality_id:
                    rec.line_id.update_value = ''
                    rec.line_id.action_update_relation_fields(rec.nationality_id)
                elif rec.business_structure_id:
                    rec.line_id.update_value = ''
                    rec.line_id.action_update_relation_fields(rec.business_structure_id)
        return res

class ProjectPartnerFields(models.Model):
    _inherit = 'project.res.partner.fields'

    hand_partner_id = fields.Many2one('res.partner',related='project_id.hand_partner_id', string='Hand Partners')
    current_value = fields.Char(string="Current Value", compute='_compute_current_value', store=True, readonly=True)

    @api.depends('field_id', 'hand_partner_id')
    def _compute_current_value(self):
        for record in self:
            if record.field_id and record.hand_partner_id:
                try:
                    field_name = record.field_id.name
                    if field_name and hasattr(record.hand_partner_id, field_name):
                        record.current_value = getattr(record.hand_partner_id, field_name, False)
                    else:
                        record.current_value = False
                except Exception as e:
                    record.current_value = False
            else:
                record.current_value = False
