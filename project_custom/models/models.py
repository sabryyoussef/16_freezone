from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ReachedCheckpoint(models.Model):
    _name = 'reached.checkpoint'
    _rec_name = 'record_name'
    _order = 'record_name'

    name = fields.Selection(string="Name",
                            selection=[
                                ('is_complete_return_compliance', 'Compliance Complete'),
                                ('is_confirm_compliance', 'Compliance Confirm'),
                                ('is_update_compliance', 'Compliance Update'),
                                ('is_complete_return_hand', 'Handover Complete'),
                                ('is_confirm_hand', 'Handover Confirm'),
                                ('is_update_hand', 'Handover Update'),
                                ('is_complete_return_required', 'Required Document Complete'),
                                ('is_confirm_required', 'Required Document Confirm'),
                                ('is_update_required', 'Required Document Update'),
                                ('is_complete_return_deliverable', 'Deliverable Document Complete'),
                                ('is_confirm_deliverable', 'Deliverable Document Confirm'),
                                ('is_update_deliverable', 'Deliverable Document Update'),
                                ('is_complete_return_partner_fields', 'Partner Fields Complete'),
                                ('is_confirm_partner_fields', 'Partner Fields Confirm'),
                                ('is_update_partner_fields', 'Partner Fields Update'),
                            ], default='', required=True, )
    record_name = fields.Char(compute='get_record_name')

    @api.depends('name')
    def get_record_name(self):
        for rec in self:
            rec.record_name = dict(self.fields_get(allfields=['name'])['name']['selection'])[rec.name]


class ChannelPartnerPlan(models.Model):
    _name = 'channel.partner.plan'

    name = fields.Char(required=True)
    license_authority_ids = fields.Many2many('product.attribute.value', string='License Authority')
    description = fields.Text()


class HnadLegalType(models.Model):
    _name = 'hand.legal.type'

    name = fields.Char(required=True)
    license_authority_ids = fields.Many2many('product.attribute.value', string='License Authority')


class TaskCheckpoint(models.Model):
    _name = 'project.task.checkpoint'

    task_id = fields.Many2one("project.task")
    reached_checkpoint_ids = fields.Many2many("reached.checkpoint")
    stage_id = fields.Many2one("project.task.type")
    milestone_id = fields.Many2one("project.milestone")
    sequence = fields.Integer()


class PartnerVisaApplication(models.Model):
    _name = 'contact.visa.application'

    parent_id = fields.Many2one('res.partner', string='Parent Contact')
    partner_id = fields.Many2one('res.partner', string='Contact')
    existing_uae_visa = fields.Boolean(string='Existing UAE Visa', copy=False)
    apply_visa = fields.Boolean(string='Apply Visa', copy=False)
    inside = fields.Boolean(string='Inside', copy=False)
    vip_medical = fields.Boolean(string='Vip Medical', copy=False)
    vip_biometric = fields.Boolean(string='Vip Biometric', copy=False)
    visa_type = fields.Selection(string="Visa Type", selection=[('investor', 'Investor'),
                                                                ('employee', 'Employee'), ], default='')
    eid_no = fields.Char("Eid No.")
    eid_document = fields.Binary("Eid Document", size=15)
    visa_start_date = fields.Date("Visa Start Date")
    visa_expiry_date = fields.Date("Visa Expiry Date")
    is_active = fields.Boolean("Is Active")
    is_visa_active = fields.Boolean("Is Visa Active")
    eid_link = fields.Binary("EID Link")

    @api.constrains('eid_no')
    def _check_eid_number_length(self):
        for record in self:
            if len(record.eid_no) != 15:
                raise ValidationError('The EID Number must be exactly 15 digits long.')


class ProjectVisaApplication(models.Model):
    _name = 'project.visa.application'

    project_id = fields.Many2one('project.project', string='Project')
    partner_id = fields.Many2one('res.partner', string='Contact')
    existing_uae_visa = fields.Boolean(string='Existing UAE Visa', copy=False)
    apply_visa = fields.Boolean(string='Apply Visa', copy=False)
    inside = fields.Boolean(string='Inside', copy=False)
    vip_medical = fields.Boolean(string='Vip Medical', copy=False)
    vip_biometric = fields.Boolean(string='Vip Biometric', copy=False)
    visa_type = fields.Selection(string="Visa Type", selection=[('investor', 'Investor'),
                                                                ('employee', 'Employee'), ], default='')


class LicenseActivity(models.Model):
    _name = 'license.activity'

    name_code = fields.Char(compute='_get_name_code', string='Activity Name Code', store=True)
    name = fields.Char(required=True)
    code = fields.Char(string='Activity Code', required=True)
    license_authority_ids = fields.Many2many('product.attribute.value', string='License Authority')
    license_authority_id = fields.Many2one('product.attribute.value', string='License Authority')

    @api.depends('name', 'code')
    def _get_name_code(self):
        for rec in self:
            name = rec.name
            if rec.code:
                name = f'{name} - ({rec.code})'
            rec.name_code = name

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if name:
            name = name.split(' / ')[-1]
            args = ['|', ('name', operator, name), ('name_code', operator, name)] + args
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)


class Models(models.Model):
    _inherit = 'res.partner.shareholder'

    company_type = fields.Selection(string="Contact Type", related='contact_id.company_type', readonly=False)
    customer_id = fields.Many2one('res.partner', string='Customer')
    first_name = fields.Char(string="First Name", related='contact_id.first_name', readonly=False)
    middle_name = fields.Char(string="Middle Name", related='contact_id.middle_name', readonly=False)
    last_name = fields.Char(string="Last Name", related='contact_id.last_name', readonly=False)
    place_of_birth = fields.Many2one('res.country', string="PLace Of Birth", related='contact_id.place_of_birth',
                                     readonly=False)
    email = fields.Char(string="Email", related='contact_id.email', readonly=False)
    mobile = fields.Char(string="Mobile", related='contact_id.mobile', readonly=False)
    nationality_id = fields.Many2one(string="Nationality", related='contact_id.nationality_id', readonly=False)
    birthday = fields.Date(string="Birthday", related='contact_id.birthday', readonly=False)
    gender = fields.Selection(string="Gender", selection=[('male', 'Male'), ('female', 'Female'), ],
                              related='contact_id.gender', readonly=False)
    passport = fields.Many2one('documents.document', string='Passport Copy',
                               related='contact_id.passport', readonly=False,
                               domain="[('partner_id','=', contact_id)]")
    current_visa = fields.Many2one('documents.document', string='Tourist Visa Copy',
                                   related='contact_id.current_visa', readonly=False,
                                   domain="[('partner_id','=', contact_id)]")
    emirates_no_id = fields.Many2one('documents.document', string="Emirates ID",
                                     related='contact_id.emirates_no_id',
                                     readonly=False,
                                     domain="[('partner_id','=', contact_id)]")
    residence_visa_id = fields.Many2one('documents.document', string="Residence Visa",
                                        related='contact_id.residence_visa_id',
                                        readonly=False,
                                        domain="[('partner_id','=', contact_id)]"
                                        )
    entry_stamp = fields.Many2one('documents.document', string='Entry Stamp',
                                  related='contact_id.entry_stamp', readonly=False,
                                  domain="[('partner_id','=', contact_id)]")
    permanent_address_id = fields.Many2one("res.country", string="Permanent Address",
                                           related='contact_id.permanent_address_id', readonly=False)

    license_authority_id = fields.Many2one("product.attribute.value", string="License Authority",
                                           domain="[('attribute_id.name', '=', 'Authorities')]",
                                           related='contact_id.license_authority_id', readonly=False)

    incorporation_date = fields.Date("Incorporation Date", related='contact_id.incorporation_date', readonly=False)
    license_number = fields.Char("License Number", related='contact_id.license_number', readonly=False)
    license_validity = fields.Selection(string="Applied Years", relaed='contact_id.license_validity',
                                        selection=[('1', '1 Year'), ('2', '2 Years'),
                                                   ('3', '3 Years'), ('4', '4 Years'),
                                                   ('5', '5 Years'), ('6', '6 Years'),
                                                   ('7', '7 Years'), ('8', '8 Years'),
                                                   ('9', '9 Years'), ('10', '10 Years'), ], )
    apply_visa = fields.Boolean("Apply Visa")
    uae_resident = fields.Boolean("UAE Resident", related='contact_id.residency', readonly=False)
    eid_copy = fields.Many2one('documents.document', string='Emirates ID (Copy)',
                               related='contact_id.emirates_no_id', readonly=False,
                               domain="[('partner_id','=', contact_id)]")
    residence_visa_copy = fields.Many2one('documents.document',
                                          related='contact_id.residence_visa_id', readonly=False,
                                          string='Residence Visa Copy (for UAE Residents)',
                                          domain="[('partner_id','=', contact_id)]")
    trade_license = fields.Many2one('documents.document', string='Trade/Professional/Commercial License (Copy)',
                                    domain="[('partner_id','=', contact_id)]")
    memorandum_association = fields.Many2one('documents.document',
                                             string='Memorandum/Article of Association (Copy)',
                                             domain="[('partner_id','=', contact_id)]")
    project_id = fields.Many2one("project.project")
    documents_folder_id = fields.Many2one("documents.folder")
    address_ids = fields.One2many("res.partner.shareholder.address", 'shareholder_id')

    @api.onchange('contact_id')
    def action_calculate(self):
        self.prepare_lines()

    def prepare_lines(self):
        lines = []
        self.address_ids = None
        for rec in self:
            if rec.contact_id:
                for line in rec.contact_id.partner_address_lines:
                    lines.append(
                        (0, 0, {
                            'partner_id': line.partner_id.id,
                            'type': line.type,
                            'street': line.street,
                            'street2': line.street2,
                            'zip': line.zip,
                            'city': line.city,
                            'state_id': line.state_id.id,
                            'country_id': line.country_id.id,
                        }))
            rec.write({'address_ids': lines})

    # @api.constrains('shareholding')
    # def _check_shareholding(self):
    #     for rec in self:
    #         if rec.shareholding <= 0:
    #             raise ValidationError('Please add value in Shareholding')



class shareholderAddress(models.Model):
    _name = 'res.partner.shareholder.address'

    shareholder_id = fields.Many2one('res.partner.shareholder')
    partner_id = fields.Many2one('res.partner')
    type = fields.Selection(
        [
            ('invoice', 'Invoice Address'),
            ('delivery', 'Delivery Address'),
            ('private', 'Private Address'),
            ('current', 'Current Address'),
            ('permanent', 'Permanent Address'),
            ('other', 'Other Address'),
        ], string='Address Type',
        default='current')
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
