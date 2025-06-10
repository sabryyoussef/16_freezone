
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import base64
import collections
import datetime
import hashlib
import pytz
import threading
import re

import requests
from collections import defaultdict
from lxml import etree
from random import randint
from werkzeug import urls

from odoo import api, fields, models, tools, SUPERUSER_ID, _, Command
from odoo.osv.expression import get_unaccent_wrapper
from odoo.exceptions import RedirectWarning, UserError, ValidationError

@api.model
def _lang_get(self):
    return self.env['res.lang'].get_installed()

# put POSIX 'Etc/*' entries at the end to avoid confusing users - see bug 1086728
_tzs = [(tz, tz) for tz in sorted(pytz.all_timezones, key=lambda tz: tz if not tz.startswith('Etc/') else '_')]
def _tz_get(self):
    return _tzs

class ProjectFields(models.TransientModel):
    _name = 'project.update.fields'

    field_name = fields.Char(related='line_id.field_id.name', string='Field Name')
    field_ttype = fields.Selection(related='line_id.field_id.ttype', string='Field Type')
    line_id = fields.Many2one("project.res.partner.fields",string="Line")

    # Many2one
    state_id = fields.Many2one('res.country.state', string='State')
    user_id = fields.Many2one('res.users', string='Sales Person')
    team_id = fields.Many2one('crm.team', string='Sales Team')
    parent_id = fields.Many2one('res.partner', string='Parent')
    mobile_country_id = fields.Many2one('res.country', string='Mobile Country')
    country_id = fields.Many2one('res.country', string='Nationality')
    company_id = fields.Many2one('res.company', string='Company')
    accountant1_id = fields.Many2one('hr.employee', string='Accountant 1')
    accountant2_id = fields.Many2one('hr.employee', string='Accountant 2')
    activity_user_id = fields.Many2one('res.users', string='Responsible User')
    passport = fields.Many2one('res.partner.document', string='Passport Copy')
    current_visa = fields.Many2one('res.partner.document', string='Current Visa')
    entry_stamp = fields.Many2one('res.partner.document', string='Entry Stamp')
    legal_form_id = fields.Many2one('legal.form', string='Legal Form')
    license_authority_id = fields.Many2one('product.attribute.value', string='License Authority')
    place_of_birth = fields.Many2one('res.country', string='Place Of Birth')
    primary_support_id = fields.Many2one('hr.employee', string='Primary Support')
    permanent_address_id = fields.Many2one('res.country', string='Permanent Address')

    # many2many

    parent_partner_ids = fields.Many2many("res.partner", relation="chart_a", column1="chart_b", column2="chart_c", string="Parents", )
    parent_chart_ids = fields.Many2many("res.partner", relation="chart_1", column1="chart_2", column2="chart_3", string="Parents Chart", )
    risk_assessment_ids = fields.Many2many("partner.risk.assessment", string="Partner Assessment")
    license_activity_ids = fields.Many2many('license.activity', string='License Activity')

    update_value_char = fields.Char(string="Update Value")
    update_value_date = fields.Date(string="Update Value")
    update_value_float = fields.Float(string="Update Value")
    update_value_integer = fields.Integer(string="Update Value")
    update_value_bool = fields.Boolean(string="Update Value")

    # Selection
    company_type = fields.Selection(string="Company Type", selection=[('person', 'Individual'), ('company', 'Company'),])
    gender = fields.Selection(string="Gender", selection=[('male', 'Male'), ('female', 'Female'),])
    hand_legal_type = fields.Selection(string="Legal Entity/Type", selection=[('fzco', 'FZCO'), ('fze', 'FZE'),('llc', 'LLC'),])
    hand_legal_type_id = fields.Many2one('hand.legal.type', string='Legal Entity/Type')
    lang = fields.Selection(_lang_get,string="Gender")
    license_validity = fields.Selection(string="Applied Years", selection=[('1', '1 Year'), ('2', '2 Years'),
                                                                           ('3', '3 Years'), ('4', '4 Years'),
                                                                           ('5', '5 Years'), ('6', '6 Years'),
                                                                           ('7', '7 Years'), ('8', '8 Years'),
                                                                           ('9', '9 Years'), ('10', '10 Years'), ], )
    partner_category = fields.Selection(selection=[('normal', 'Normal'), ('vip', 'VIP'), ('vvip', 'VVIP')], required=1,
                                        default='normal')
    relationship = fields.Selection([
        ('manager', 'Manager'),
        ('director', 'Director'),
        ('president', 'President'), ], string='Relationship')
    status = fields.Selection(string="Status", selection=[('active', 'Active'), ('not_active', 'Not Active'), ])
    shareholder = fields.Selection([
        ('True', 'True'),
        ('False', 'False'), ], default='', string='Shareholder')
    type = fields.Selection(
        [('contact', 'Contact'),
         ('invoice', 'Invoice Address'),
         ('delivery', 'Delivery Address'),
         ('private', 'Private Address'),
         ('other', 'Other Address'),
         ], string='Address Type',
        default='contact',)
    tz = fields.Selection(_tz_get, string='Timezone', default=lambda self: self._context.get('tz'))

    def action_update(self):
        for rec in self:
            rec.line_id.update_value = ''
            if rec.field_ttype == 'selection':
                value = ''
                if rec.company_type:
                    value = rec.company_type
                elif rec.gender:
                    value = rec.gender
                elif rec.lang:
                    value = rec.lang
                elif rec.license_validity:
                    value = rec.license_validity
                elif rec.hand_legal_type:
                    value = rec.hand_legal_type
                elif rec.partner_category:
                    value = rec.partner_category
                elif rec.relationship:
                    value = rec.relationship
                elif rec.status:
                    value = rec.status
                elif rec.type:
                    value = rec.type
                elif rec.shareholder:
                    value = rec.shareholder
                elif rec.tz:
                    value = rec.tz
                rec.line_id.update_value = value
                rec.line_id.action_update_normal_fields()
            if rec.field_ttype == 'char':
                rec.line_id.update_value = rec.update_value_char
                rec.line_id.action_update_normal_fields()
            if rec.field_ttype == 'date':
                rec.line_id.update_value = rec.update_value_date
                rec.line_id.action_update_normal_fields()
            if rec.field_ttype == 'float':
                rec.line_id.update_value = rec.update_value_float
                rec.line_id.action_update_normal_fields()
            if rec.field_ttype == 'integer':
                rec.line_id.update_value = rec.update_value_integer
                rec.line_id.action_update_normal_fields()
            if rec.field_ttype == 'boolean':
                if rec.update_value_bool:
                    rec.line_id.update_value = rec.update_value_bool
                    rec.line_id.action_update_normal_fields()
                else:
                    rec.line_id.action_update_normal_fields()
                    rec.line_id.update_value = 'False'
            if rec.field_ttype == 'many2many':
                many2many_field_to_update = None
                # Prioritize the fields based on their availability
                if rec.parent_partner_ids:
                    many2many_field_to_update = rec.parent_partner_ids
                elif rec.parent_chart_ids:
                    many2many_field_to_update = rec.parent_chart_ids
                elif rec.license_activity_ids:
                    many2many_field_to_update = rec.license_activity_ids
                elif rec.risk_assessment_ids:
                    many2many_field_to_update = rec.risk_assessment_ids
                # If a Many2many field is found, call the update method
                if many2many_field_to_update:
                    print('Many2many field to update ========>', many2many_field_to_update)
                    rec.line_id.action_update_many2many_fields(many2many_field_to_update)
            if rec.field_ttype == 'many2one':
                field_to_update = None
                if rec.state_id:
                    field_to_update = rec.state_id
                elif rec.user_id:
                    field_to_update = rec.user_id
                elif rec.team_id:
                    field_to_update = rec.team_id
                elif rec.parent_id:
                    field_to_update = rec.parent_id
                elif rec.nationality_id:
                    field_to_update = rec.nationality_id
                elif rec.mobile_country_id:
                    field_to_update = rec.mobile_country_id
                elif rec.company_id:
                    field_to_update = rec.company_id
                elif rec.accountant1_id:
                    field_to_update = rec.accountant1_id
                elif rec.accountant2_id:
                    field_to_update = rec.accountant2_id
                elif rec.activity_user_id:
                    field_to_update = rec.activity_user_id
                elif rec.passport:
                    field_to_update = rec.passport
                elif rec.current_visa:
                    field_to_update = rec.current_visa
                elif rec.entry_stamp:
                    field_to_update = rec.entry_stamp
                elif rec.legal_form_id:
                    field_to_update = rec.legal_form_id
                elif rec.license_authority_id:
                    field_to_update = rec.license_authority_id
                elif rec.place_of_birth:
                    field_to_update = rec.place_of_birth
                elif rec.primary_support_id:
                    field_to_update = rec.primary_support_id
                elif rec.permanent_address_id:
                    field_to_update = rec.permanent_address_id
                elif rec.business_structure_id:
                    field_to_update = rec.business_structure_id

                # If a field is found, call the update method
                if field_to_update:
                    print('Field to update ========>', field_to_update)
                    rec.line_id.action_update_relation_fields(field_to_update)
