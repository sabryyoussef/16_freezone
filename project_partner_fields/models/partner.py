from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
import re

class ResPartner(models.Model):
    _inherit = 'res.partner'

    corporate_tax_registered = fields.Boolean("Corporate Tax Registered")
    corporate_tax_number = fields.Char("Corporate Tax Number")
    corporate_tax_period_from = fields.Date("Corporate Tax (Date From)")
    corporate_tax_period_to = fields.Date("Corporate Tax (Date To)")
    corporate_tax_filing = fields.Date("Corporate Tax Filing")


class LicenseActivity(models.Model):
    _name = 'license.activity'

    name = fields.Char(required=True)
    code = fields.Char(string='Activity Code',required=True)
    license_authority_ids = fields.Many2many('product.attribute.value', string='License Authority')
    license_authority_id = fields.Many2one('product.attribute.value', string='License Authority')

