
from odoo import api, fields, models

class Shareholder(models.Model):
    _name = 'shareholder.data'

    name = fields.Char()
    position = fields.Char()
    project_id = fields.Many2one('project.project')
    partner_id = fields.Many2one('res.partner')
    contact_id = fields.Many2one('res.partner')
    relationship_ids = fields.Many2many("business.relationships", string="Relationships")
    shares = fields.Float(string="# of Shares", default=1)
    total = fields.Float(string="Total Shareholding Value", default=1)


class LicenseActivity(models.Model):
    _name = 'license.activity'

    name = fields.Char(string="name", required=True, )

class LegalForm(models.Model):
    _name = 'legal.form'

    name = fields.Char(string="name", required=True, )
