from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
import re

class ResPartner(models.Model):
    _inherit = 'res.partner'

    project_id = fields.Many2one('project.project', string='Project')
    hand_partner_id = fields.Many2one('res.partner', string='Contact')
    hand_legal_type = fields.Selection(string="Legal Entity/Type",
                                       selection=[('fzco', 'FZCO'), ('fze', 'FZE'), ('llc', 'LLC'), ], default='')
    hand_legal_type_id = fields.Many2one('hand.legal.type', string='Legal Entity/Type')
    visa_eligibility = fields.Float('Visa Eligibility')
    price_per_share = fields.Float('Price Per Share')
    total_number_shares = fields.Float('Total Number Of Shares')
    total_share_value = fields.Monetary('Total Share Value', compute='_get_share_value')
    hand_country_ids = fields.Many2many('res.country', string='Top 5 Countries of Operation')

    channel_plan_id = fields.Many2one('channel.partner.plan',string="Channel Partner Plan")
    place_of_birth = fields.Many2one('res.country',string="Place Of Birth")
    current_address = fields.Char(string="Current Address")
    passport = fields.Many2one('documents.document',string='Passport Copy')
    current_visa = fields.Many2one('documents.document',string='Tourist Visa')
    entry_stamp = fields.Many2one('documents.document',string='Entry Stamp')
    permanent_address_id = fields.Many2one("res.country", string="Permanent Address")
    contact_visa_application_ids = fields.One2many('contact.visa.application', 'parent_id', string='Visa Application')


    @api.depends('price_per_share','total_number_shares')
    def _get_share_value(self):
        for rec in self:
            rec.total_share_value = rec.price_per_share * rec.total_number_shares


