from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, date

class OnboardingStage(models.Model):
    _name = 'initial.client.onboarding.stage'

    name = fields.Char(required=True)

class RiskCategory(models.Model):
    _name = 'risk.category'

    name = fields.Char(compute='get_record_name', store=True, string='Name')
    type = fields.Selection(string="Type", selection=[('service', 'Service Risk'), ('product', 'Product Risk'),
                                                      ('client', 'Client Risk'), ('geography', 'Geography Risk'),
                                                      ('PEP', 'PEP Risk'), ('adverse_media', 'Adverse Media Risk'),
                                                      ('Sanction', 'Sanction Risk'), ('interface', 'Interface Risk'),
                                                      ], required=True)
    data_ids = fields.Many2many('assessment.list')

    @api.depends('type')
    def get_record_name(self):
        name_mapping = {
            'service': 'Service Risk',
            'product': 'Product Risk',
            'client': 'Client Risk',
            'geography': 'Geography Risk',
            'PEP': 'PEP Risk',
            'adverse_media': 'Adverse Media Risk',
            'Sanction': 'Sanction Risk',
            'interface': 'Interface Risk',
        }
        for rec in self:
            rec.name = name_mapping.get(rec.type, '')

    @api.constrains('type')
    def _check_unique_type(self):
        for record in self:
            if record.type:
                existing = self.search([
                    ('type', '=', record.type),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(
                        f"The type '{record.type}' is already assigned to another category. Each type must be unique."
                    )

class RiskScoring(models.Model):
    _name = 'risk.scoring'

    name = fields.Char(required=True)
    rating_id = fields.Many2one('risk.rating')

class RiskRating(models.Model):
    _name = 'risk.rating'

    name = fields.Char(required=True)
    type = fields.Selection(string="Re-assessment Period", selection=[('6', '6 Months'),
                                                                      ('12', '1 Year'),
                                                                      ('24', '2 Year'),
                                                                      ('36', '3 Year'), ], required=True)
    document_required_type_ids = fields.One2many("product.template.required.documents",'rating_id')


class AssessmentList(models.Model):
    _name = 'assessment.list'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True)
    category_id = fields.Many2one('risk.category', string='Risk Category')
    listing_id = fields.Many2one('listing.group', string='List Group Value')


class ListingGroup(models.Model):
    _name = 'listing.group'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True)
    listing_ids = fields.One2many('listing.group.line', 'listing_id')


class ListingGroupLine(models.Model):
    _name = 'listing.group.line'

    name = fields.Char(required=True)
    listing_id = fields.Many2one('listing.group')
    scoring_id = fields.Many2one('risk.scoring', string='Scoring')

