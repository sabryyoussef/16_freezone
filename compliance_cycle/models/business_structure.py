
from odoo import api, fields, models

class BusinessStructure(models.Model):
    _name = 'business.structure'

    name = fields.Char(required=True)
    relationships_ids = fields.Many2many("business.relationships", string="Business Relationships")

class BusinessRelationships(models.Model):
    _name = 'business.relationships'

    name = fields.Char(required=True)

class PartnerUbo(models.Model):
    _name = 'res.partner.ubo'

    name = fields.Char(required=True)

class BusinessShareholder(models.Model):
    _name = 'res.partner.shareholder'

    partner_id = fields.Many2one("res.partner")
    contact_id = fields.Many2one("res.partner",string='Contact')
    ubo_id = fields.Many2one("res.partner.ubo", string='UBO')
    shareholding = fields.Float(string="Shareholding")
    relationship_ids = fields.Many2many("business.relationships", string='Relationship')
