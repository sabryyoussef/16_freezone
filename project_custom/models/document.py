
from odoo import api, fields, models
import base64

class DocumentType(models.Model):
    _inherit = 'res.partner.document'

    type_is_closed = fields.Boolean(compute='get_check_document_type')

    @api.onchange('type_id')
    def get_check_document_type(self):
        for rec in self:
            passport_type = 630   # Passport (valid within 7 months)
            rec.type_is_closed = rec.type_id.id == passport_type if passport_type else False
