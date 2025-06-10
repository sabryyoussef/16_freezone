from odoo import api, fields, models
from odoo.exceptions import ValidationError,UserError


class Partner(models.Model):
    _inherit = 'res.partner'

    def _get_default_stage(self):
        return self.env['partner.stage'].search([], limit=1).id

    stage_id = fields.Many2one(
        'partner.stage', string='Stage', index=True, tracking=True,
        default=_get_default_stage, copy=False
    )

    license_authority_id = fields.Many2one("product.attribute.value", string="License Authority",
                                           domain="[('attribute_id.name', '=', 'Authorities')]")
    incorporation_date = fields.Date(string="Incorporation Date")
    license_validity = fields.Selection(string="Applied Years", selection=[('1', '1 Year'), ('2', '2 Years'),
                                                                           ('3', '3 Years'), ('4', '4 Years'),
                                                                           ('5', '5 Years'), ('6', '6 Years'),
                                                                           ('7', '7 Years'), ('8', '8 Years'),
                                                                           ('9', '9 Years'), ('10', '10 Years'), ], )
    license_validity_from = fields.Date("License Validity (Date From)")
    license_validity_to = fields.Date("License Validity (Date To)")
    source_id = fields.Many2one('utm.source', string="Data Origin")
    license_number = fields.Char(string="License Number")
    legal_form_id = fields.Many2one('legal.form', string="Legal Form")
    source_wealth = fields.Char(string="Source of Fund/Source of Wealth")
    status = fields.Selection(string="Status", selection=[('active', 'Active'), ('not_active', 'Not Active'), ])
    shareholder = fields.Selection([
        ('True', 'True'),
        ('False', 'False'), ], default='', string='Shareholder')
    country_id = fields.Many2one('res.country', string="Country")
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'), ])
    residency = fields.Boolean(string="Residency")
    trade_license_id = fields.Many2one('documents.document', string="Trade License")
    memorandum_articles_id = fields.Many2one('documents.document', string="Memorandum/Articles of Association")
    emirates_no_id = fields.Many2one('documents.document', string="Emirates ID")
    residence_visa_id = fields.Many2one('documents.document', string="Residence Visa")
    foreign_jurisdiction_id = fields.Many2one('res.country', string='Foreign Jurisdiction')
    relationship = fields.Selection([
        ('manager', 'Manager'),
        ('director', 'Director'),
        ('president', 'President'), ], string='Relationship')
    ubo = fields.Boolean(string="UBO")
    shareholder_ids = fields.One2many('shareholder.data', 'partner_id')

    all_license_activity_ids = fields.Many2many("license.activity", relation="activity1", column1="activity2",
                                                column2="activity3", string='ALl License Activity',
                                                compute='_onchange_license_activity_ids')
    license_activity_ids = fields.Many2many("license.activity", string="License Activity",
                                            domain="[('id', 'in', all_license_activity_ids)]")
    is_appear_buttons = fields.Boolean(compute='_check_is_appear_buttons')

    def _check_is_appear_buttons(self):
        current_user_id = self.env.user.id
        has_edit_group = self.env.user.has_group('partner_custom.partner_can_edit_verified_group')
        for rec in self:
            user_ids = {
                rec.primary_support_id.user_id.id,
                rec.secondary_support_id.user_id.id,
                rec.accountant1_id.user_id.id,
                rec.accountant2_id.user_id.id,
                rec.user_id.id,
            }
            rec.is_appear_buttons = has_edit_group or current_user_id in user_ids

    def action_new(self):
        for rec in self:
            rec.stage_id = self.env['partner.stage'].sudo().search([('id','=',1)])

    def action_verified(self):
        for rec in self:
            rec.stage_id = self.env['partner.stage'].sudo().search([('id','=',2)])

    def action_liquidated_struck_off(self):
        for rec in self:
            rec.stage_id = self.env['partner.stage'].sudo().search([('id','=',3)])

    # def write(self, vals):
    #     action_id = self.env.context.get('params', {}).get('action')
    #     active_model = self.env.context.get('active_model')
    #     form_view_id = None
    #     print(' action_id  ========>  ', action_id , self.env.context)
    #     if action_id:
    #         action = self.env['ir.actions.act_window'].browse(action_id)
    #         print(' actionnnnnnnnnnnn ', action, action.view_ids)
    #         for view in action.view_ids:
    #             print(' viewwwwwwwwwwwww ', action.mode)
    #             if view.view_mode == 'form':
    #                 form_view_id = view.view_id.xml_id
    #                 print('xxxxxxxxxx',form_view_id)
    #     if not action_id:
    #         form_view_id = 'base.view_partner_form'
    #
    #     print(' form_view_id  ========> ', action_id,form_view_id, active_model)
    #
    #     if form_view_id == 'base.view_partner_form' and active_model not in ['sale.order','project.project']:
    #
    #         access = self.env.user.has_group('partner_custom.partner_can_edit_verified_group')
    #         verified_stage_id = 2
    #         allowed_fields = {'primary_support_id', 'secondary_support_id', 'accountant1_id', 'accountant2_id',
    #                           'user_id',
    #                           'stage_id'}
    #         for record in self:
    #             if record.stage_id.id == verified_stage_id:
    #                 if not access:
    #                     # User has no access: block all writes
    #                     raise ValidationError(
    #                         "You are not Managing this Contact and not have permission to edit this record. Kindly contact Company Administrator for assistance.")
    #
    #                 # if record.stage_id.id == verified_stage_id:
    #                 #     # User has access but record is in Verified stage
    #                 #     if not set(vals.keys()).issubset(allowed_fields):
    #                 #         raise ValidationError(
    #                 #             "You are not Managing this Contact and not have permission to edit this record. Kindly contact Company Administrator for assistance.")
    #     return super(Partner, self).write(vals)

    @api.depends('license_authority_id')
    def _onchange_license_activity_ids(self):
        for rec in self:
            if self.license_authority_id:
                activity = self.env['license.activity'].sudo().search(
                    [('license_authority_id', '=', self.license_authority_id.id)])
                rec.all_license_activity_ids = [(6, 0, activity.ids)]
            else:
                activity = self.env['license.activity'].sudo().search([])
                rec.all_license_activity_ids = [(6, 0, activity.ids)]

    def action_open_shareholder(self):
        self.ensure_one()
        action = self.env.ref('base.action_partner_form').read()[0]
        action['context'] = {
            # 'default_name': self.name,
            'default_company_type': 'company',
        }
        action['views'] = [(
            self.env.ref('base.view_partner_form').id,
            'form'
        )]
        return action

    @api.onchange('shareholder')
    def action_shareholder(self):
        if self.shareholder == 'False':
            self.prepare_shareholder()
        if self.shareholder == 'True':
            self.action_open_shareholder()

    def prepare_shareholder(self):
        lines = []
        self.shareholder_ids = None
        for rec in self:
            partners = []
            all_partners = self.env['res.partner'].sudo().search([('company_type', '=', 'person')])
            for partner in all_partners:
                if str(partner.parent_id.id) == str(rec.id) or str(partner.parent_id.id) in str(rec.id):
                    partners.append(partner.name)
            for line in partners:
                lines.append(
                    (0, 0, {
                        'name': line,
                    }))
            self.write({'shareholder_ids': lines})
