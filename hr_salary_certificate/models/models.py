
from odoo import api, fields, models

class CertificateName(models.Model):
    _name = 'certificate.name'

    name = fields.Char(required=True)
    report_ids = fields.Many2many('ir.actions.report', domain="[('model','=','salary.certificate.master')]", string='Reports')
