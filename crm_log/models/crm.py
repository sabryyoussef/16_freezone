
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,UserError
AVAILABLE_PRIORITIES = [
    ('0', 'Low'),
    ('1', 'Medium'),
    ('2', 'High'),
    ('3', 'Very High'),
]
import phonenumbers
from dateutil.relativedelta import relativedelta

SERVICE_SELCTION = [
    ('free', 'Free Consultation'),
    ('business_setup', 'Business Setup'),
    ('freelance', 'Freelance Permit Setup'),
    ('bank', 'Bank Account Setup'),
    ('accounting', 'Accounting Services'),
    ('marketing', 'Marketing Services'),
    ('golden', 'Golden Visa'),
    ('pro', 'PRO Services'),
    ('service_interested', 'Service Interested'),
    ('ksa_business', 'KSA Business Setup'),
]

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    referred_id = fields.Many2one('res.partner', string='Referred By')
    is_hide_quotation_button = fields.Boolean(related='stage_id.is_hide_quotation_button')
    is_required_referred = fields.Boolean(related='source_id.is_required_referred')
    mail_sent = fields.Boolean()
    priority = fields.Selection(
        AVAILABLE_PRIORITIES, string='Heat', index=True,
        default=AVAILABLE_PRIORITIES[0][0])
    service = fields.Selection(
        SERVICE_SELCTION, string='Service Interested In ', index=True,
        default=SERVICE_SELCTION[0][0])
    nationality_id = fields.Many2one('res.country')
    stage_name = fields.Char(related='stage_id.name', store=True)
    customer_status = fields.Selection([
        ('approved', 'Customer Approved'),
        ('approved_reservations', 'Customer Approved with Reservations'),
        ('deferred', 'Customer Deferred'),
        ('non_responsive', 'Customer Non-Responsive'),
    ], default='', string='Customer Status')
    salesperson_notes = fields.Text('Salesperson Notes')
    lead_ref = fields.Char(
        string='Number', required=True, copy=False, readonly=True,
        index=True, default=lambda self: _('New'), track_visibility='onchange')
    employee_id = fields.Many2one('hr.employee')
    business_proposal = fields.Many2one('documents.document',string='Business Proposal', tracking=True)
    is_quotation_expired = fields.Boolean(compute='_compute_is_quotation_expired', store=True)
    # Add this to your model (if needed)

    def action_view_document(self):
        """ Smart button to open kanban view with tree view as an option """
        recs = self.env['documents.document'].browse(self.business_proposal.id)
        action = self.env.ref('documents.document_action').read()[0]
        # Get the kanban and tree view IDs
        kanban_view = self.env.ref('documents.document_view_kanban').id
        tree_view = self.env.ref('documents.documents_view_list').id
        form_view = self.env.ref('documents.document_view_form').id
        # Configure views to show kanban first and tree as an option
        action['views'] = [
            (kanban_view, 'kanban'),
            (tree_view, 'tree'),
            (form_view, 'form')
        ]
        action['view_mode'] = 'kanban,tree,form'
        if recs:
            action['domain'] = [('id', 'in', recs.ids)]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action


    @api.depends('date_closed')
    def _compute_is_quotation_expired(self):
        today = fields.Date.today()
        for lead in self:
            lead.is_quotation_expired = (
                    lead.date_closed and lead.date_closed.date() <= today - relativedelta(months=6)
            )


    # def write(self, vals):
    #     if not 'source_id' in vals:
    #         raise ValidationError(" Please add source ")
    #     res = super(CrmLead, self).write(vals)
    #     return res

    @api.model
    def create(self, vals):
        if vals['source_id'] == False:
            raise ValidationError(" Please add source ")
        vals['lead_ref'] = self.env['ir.sequence'].next_by_code('crm.lead') or _('New')
        return super(CrmLead, self).create(vals)

    def action_convert_opportunity(self):
        for rec in self:
            if not rec.email_from and not rec.phone:
                err_msg = _("""
                                Please make sure to add a phone number or/and an Email
                            """)
                raise ValidationError(_(err_msg))
            else:
                return {
                    'res_model': 'crm.lead2opportunity.partner',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'view_type': 'form',
                    'view_id': self.env.ref("crm.view_crm_lead2opportunity_partner").id,
                    'target': 'new'
                }



    def _get_country_codes(self):
        countries = self.env['res.country'].search([])
        return [(country.code, f"{country.name} ({country.code})") for country in countries]

    @api.depends('country_code')
    def _get_codes(self):
        for rec in self:
            if rec.country_code:
                rec.code = str(rec.country_code)
            else:
                rec.code = ''

    @api.depends('country_code')
    def _compute_mobile_country_code(self):
        for record in self:
            if record.country_code:
                selected_country = self.env['res.country'].search([('code', '=', record.country_code)], limit=1)
                if selected_country:
                    record.mobile_country_code = '+' + str(selected_country.phone_code)
                else:
                    record.mobile_country_code = False
            else:
                record.mobile_country_code = False

    country_code = fields.Selection(selection='_get_country_codes', string='Country Code')
    code = fields.Char(compute='_get_codes', string='Code')
    mobile_country_code = fields.Char(string='Mobile Country Code', compute='_compute_mobile_country_code')
    custom_phone = fields.Char(string='Enter Phone')
    phone = fields.Char(string='Phone', compute='compute_custom_phone', store=True)

    @api.constrains('custom_phone', 'code')
    def _phone_number_constraints(self):
        for record in self:
            if record.custom_phone and record.code == 'EG' and len(record.custom_phone) != 10:
                raise ValidationError(_('Please make sure to enter at least 11 digits'))
            elif record.custom_phone and record.code == 'LB' and len(record.custom_phone) != 10:
                raise ValidationError(_('Please make sure to enter at least 11 digits'))
            elif record.custom_phone and record.code == 'AE' and len(record.custom_phone) != 9:
                raise ValidationError(_('Please make sure to enter at least 11 digits'))
            elif record.custom_phone and record.code == 'SA' and len(record.custom_phone) != 9:
                raise ValidationError(_('Please make sure to enter at least 9 digits'))
            elif record.custom_phone and record.code == 'US' and len(record.custom_phone) != 12:
                raise ValidationError(_('Please make sure to enter at least 12 digits'))
            elif record.custom_phone and record.code == 'DE' and len(record.custom_phone) != 12:
                raise ValidationError(_('Please make sure to enter at least 12 digits'))
            elif record.custom_phone and record.code == 'GB' and len(record.custom_phone) != 11:
                raise ValidationError(_('Please make sure to enter at least 11 digits'))

    @api.depends('custom_phone','mobile_country_code')
    def compute_custom_phone(self):
        for rec in self:
            phone = ''
            if rec.mobile_country_code and rec.custom_phone :
                phone = str(rec.mobile_country_code) + str(rec.custom_phone)
            rec.phone = phone


    def action_stage(self):
        for rec in self:
            call = self.env['mail.message'].sudo().search([('model', '=', 'crm.lead'),
                                                          ('res_id', '=', rec.id),('body', 'ilike', 'Call')])
            for c in call:
                print(c.body)
            mails = self.env['mail.mail'].sudo().search([('model', '=', 'crm.lead'),('res_id', '=', rec.id)]) or rec.mail_sent
            attachments = self.env['ir.attachment'].sudo().search([('res_model', '=', 'crm.lead'),
                                                                   ('res_id', '=', rec.id)])
            # call = self.env['mail.activity'].sudo().search([('res_model', '=', 'crm.lead'),
            #                                                 ('activity_type_id.name', '=', 'Call'),
            #                                                 ('res_id', '=', rec.id)])


            if rec.stage_id.name == 'New':
                if not rec.email_from and not rec.custom_phone:
                    err_msg = _("""
                                    Please make sure to add a phone number or/and an Email
                                """)
                    raise ValidationError(_(err_msg))
                # elif not mails and not call:
                #     err_msg = _("""
                #                     Please make sure to log a call or/and send an Email to move to the next stage
                #                 """)
                #     raise ValidationError(_(err_msg))
                else:
                    return {
                        'res_model': 'crm.wizard',
                        'type': 'ir.actions.act_window',
                        'view_mode': 'form',
                        'view_type': 'form',
                        'context': {'default_crm_id': rec.id},
                        'view_id': self.env.ref("crm_log.crm_wizard_form_view").id,
                        'target': 'new'
                    }
                # if not mails:
                #     err_msg = _(""" Please Send Mail To Customer """)
                #     raise ValidationError(_(err_msg))
                # if not call:
                #     raise ValidationError(_(""" Please Add Call """))
                # if mails and call:
                #     return {
                #         'res_model': 'crm.wizard',
                #         'type': 'ir.actions.act_window',
                #         'view_mode': 'form',
                #         'view_type': 'form',
                #         'context': {'default_crm_id': rec.id,},
                #         'view_id': self.env.ref("crm_log.crm_wizard_form_view").id,
                #         'target': 'new'
                #     }
            elif rec.stage_id.name == 'In Contact':
                if not mails and not call:
                    err_msg = _("""
                                     Please make sure to log a Call or send an Email
                                """)
                    raise ValidationError(_(err_msg))
                return {
                    'res_model': 'crm.wizard',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'view_type': 'form',
                    'context': {'default_crm_id': rec.id},
                    'view_id': self.env.ref("crm_log.crm_wizard_form_view").id,
                    'target': 'new'
                }
            elif rec.stage_id.name == 'Negotiation':
                if not attachments:
                    err_msg = _("""
                                     Please attach at least one Proposal
                                """)
                    raise ValidationError(_(err_msg))
                else:
                    return {
                        'res_model': 'crm.wizard',
                        'type': 'ir.actions.act_window',
                        'view_mode': 'form',
                        'view_type': 'form',
                        'context': {'default_crm_id': rec.id},
                        'view_id': self.env.ref("crm_log.crm_wizard_form_view").id,
                        'target': 'new'
                    }
            elif rec.stage_id.name == 'Proposal Sent':
                if rec.quotation_count == 0:
                    err_msg = _("""
                                    At least generate one Pro-Forma invoice via Odoo
                                """)
                    raise ValidationError(_(err_msg))
                return {
                    'res_model': 'crm.wizard',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'view_type': 'form',
                    'context': {'default_crm_id': rec.id},
                    'view_id': self.env.ref("crm_log.crm_wizard_form_view").id,
                    'target': 'new'
                }
            else:
                return {
                    'res_model': 'crm.wizard',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'view_type': 'form',
                    'context': {'default_crm_id': rec.id},
                    'view_id': self.env.ref("crm_log.crm_wizard_form_view").id,
                    'target': 'new'
                }

    def open_call(self):
        for rec in self:
            return {
                'res_model': 'crm.call.wizard',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
                'context': {'default_crm_id': rec.id},
                'view_id': self.env.ref("crm_log.crm_call_wizard_form_view").id,
                'target': 'new'
            }

    @api.onchange('expected_revenue')
    def get_priority(self):
        for rec in self:
            if rec.expected_revenue <= 10000:
                rec.priority = '1'
            elif 10000 < rec.expected_revenue < 25000:
                rec.priority = '2'
            else:
                rec.priority = '3'

class CrmStages(models.Model):
    _inherit = 'crm.stage'

    is_hide_quotation_button = fields.Boolean()
