from odoo import api, fields, models

class ComplianceLines(models.Model):
    _name = 'compliance.document.lines'
    _description = 'Compliance Document Lines'

    compliance_id = fields.Many2one('compliance.ticket', string='Compliance')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments', required=True)
    document_id = fields.Many2one('res.partner.document.type', string='Document Type')
    name = fields.Char(string='Name')
    is_moved = fields.Boolean(string='Is Moved', default=False)
    is_required_expiration = fields.Boolean(string='Required Expiration', default=False)
    issue_date = fields.Date(string='Issue Date')
    expiration_date = fields.Date(string='Expiration Date')
    is_required = fields.Boolean(string='Check Required', default=False)
    is_verify = fields.Boolean(string='Is Verify', default=False)
    is_ready = fields.Boolean(string='Is Ready', default=False)
