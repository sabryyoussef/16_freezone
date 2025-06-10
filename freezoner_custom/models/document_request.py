
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.tools.misc import clean_context

class RequestDocument(models.TransientModel):
    _inherit = 'documents.request_wizard'

    project_id = fields.Many2one('project.project')
    partner_ids = fields.Many2many('res.partner', compute='get_project_partners')
    partner_id = fields.Many2one('res.partner', domain="[('id', 'in', partner_ids)]")
    type_id = fields.Many2one(comodel_name='res.partner.document.type', string='Document Type')

    @api.depends('project_id')
    def get_project_partners(self):
        for rec in self:
            if rec.project_id:
                partners = rec.project_id.compliance_shareholder_ids.mapped('contact_id.id')
                rec.partner_ids = [(6, 0, [rec.project_id.partner_id.id, rec.project_id.hand_partner_id.id] + partners)]
            else:
                rec.partner_ids = [(6, 0, self.env['res.partner'].search([]).ids)]

    def request_document(self):
        document = super(RequestDocument, self).request_document()  # Call the original function
        if self.project_id:
            document.write({'project_id': self.project_id.id,'type_id': self.type_id.id})
        return document


