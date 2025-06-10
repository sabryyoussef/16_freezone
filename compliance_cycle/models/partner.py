from odoo import api, fields, models
from odoo.exceptions import ValidationError

class Partner(models.Model):
    _inherit = 'res.partner'

    compliance_shareholder_ids = fields.One2many('res.partner.shareholder', 'partner_id')
    partner_address_lines = fields.One2many('res.partner.address', 'partner_id')
    business_structure_id = fields.Many2one('business.structure', string='Business Structure')
    nationality_id = fields.Many2one('res.nationality', string='Nationality')

    @api.onchange('parent_id')
    def onchange_parent_id(self):
        # return values in result, as this method is used by _fields_sync()
        if not self.parent_id:
            return
        result = {}
        partner = self._origin
        if partner.parent_id and partner.parent_id != self.parent_id:
            pass
        if partner.type == 'contact' or self.type == 'contact':
            # for contacts: copy the parent address, if set (aka, at least one
            # value is set in the address: otherwise, keep the one from the
            # contact)
            address_fields = self._address_fields()
            if any(self.parent_id[key] for key in address_fields):
                def convert(value):
                    return value.id if isinstance(value, models.BaseModel) else value

                result['value'] = {key: convert(self.parent_id[key]) for key in address_fields}
        return result

    @api.constrains('partner_address_lines')
    def _check_partner_address_lines(self):
        for rec in self:
            types = [line.type for line in rec.partner_address_lines]
            if len(types) != len(set(types)):
                raise ValidationError('The address type already exists .')

    @api.onchange('parent_partner_ids', 'business_structure_id')
    def action_shareholder_lines(self):
        self.prepare_shareholder_lines()

    def prepare_shareholder_lines(self):
        for rec in self:
            existing_partner_ids = rec.compliance_shareholder_ids.mapped('contact_id.id')
            for partner in rec.parent_partner_ids:
                partner_id = partner._origin.id or partner.id
                if partner_id not in existing_partner_ids:
                    rec.compliance_shareholder_ids = [(0, 0, {
                        'partner_id': rec.id,
                        'contact_id': partner_id,  # Use the resolved partner_id
                        'relationship_ids': rec.business_structure_id.relationships_ids.ids,
                    })]
                else:
                    print(f'Partner {partner.name} already exists, skipping.')

    # @api.constrains('compliance_shareholder_ids', 'parent_partner_ids')
    # def _check_data(self):
    #     for rec in self:
    #         parent_ids = set(rec.parent_partner_ids.ids)
    #         shareholder_contact_ids = set(rec.compliance_shareholder_ids.mapped('contact_id.id'))
    #         if parent_ids != shareholder_contact_ids and not rec.project_id:
    #             raise ValidationError(" Please remove the shareholder item first. ")
