from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, date


class InitialClientOnboarding(models.Model):
    _name = 'initial.client.onboarding'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.onchange('initial_risk_rating')
    def _prepare_documents(self):
        documents = []
        for rec in self:
            if rec.initial_risk_rating:
                rec.document_required_type_ids = None
                record = self.env['risk.rating'].sudo().search([('name', '=', str(rec.initial_risk_rating))], limit=1)
                if record:
                    for line in record.document_required_type_ids:
                        documents.append((0, 0, {
                            'document_id': line.document_id.id,
                            'is_required': line.is_required,
                        }))
                rec.document_required_type_ids =  documents

    def create_documents(self):
        for rec in self:
            for line in rec.document_required_type_ids:
                if line.is_moved == False and line.issue_date and line.is_ready == False:
                    if line.is_moved == False and line.issue_date:
                        vals = {
                            'name': str(line.name),
                            'folder_id': 15,
                            'onboarding_id': rec.id,
                            'type_id': line.document_id.id,
                            'partner_id': rec.partner_id.id,
                            'issue_date': line.issue_date or False,
                            'expiration_date': line.expiration_date or False,
                            'datas': line.document,
                            'thumbnail': line.document,
                        }
                        doc = self.sudo().env['documents.document'].sudo().create(vals)
                        print(' docccccccccccc ', doc.id)
                        line.is_moved = True
    def action_view_document(self):
        """ Smart button to open kanban view with tree view as an option """
        recs = self.mapped('document_ids')
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

    def _default_service_ids(self):
        services = []
        record = self.env['risk.category'].sudo().search([('type', '=', 'service')], limit=1)
        if record:
            for line in record.data_ids:
                services.append((0, 0, {
                    'assessment_id': line.id,
                }))
        return services

    def _default_product_ids(self):
        products = []
        record = self.env['risk.category'].sudo().search([('type', '=', 'product')], limit=1)
        if record:
            for line in record.data_ids:
                products.append((0, 0, {
                    'assessment_id': line.id,
                }))
        return products

    def _default_client_ids(self):
        clients = []
        record = self.env['risk.category'].sudo().search([('type', '=', 'client')], limit=1)
        if record:
            for line in record.data_ids:
                clients.append((0, 0, {
                    'assessment_id': line.id,
                }))
        return clients

    def _default_geography_ids(self):
        geography = []
        record = self.env['risk.category'].sudo().search([('type', '=', 'geography')], limit=1)
        if record:
            for line in record.data_ids:
                geography.append((0, 0, {
                    'assessment_id': line.id,
                }))
        return geography

    def _default_pep_ids(self):
        pep = []
        record = self.env['risk.category'].sudo().search([('type', '=', 'PEP')], limit=1)
        if record:
            for line in record.data_ids:
                pep.append((0, 0, {
                    'assessment_id': line.id,
                }))
        return pep

    def _default_adverse_media_ids(self):
        adverse_media = []
        record = self.env['risk.category'].sudo().search([('type', '=', 'adverse_media')], limit=1)
        if record:
            for line in record.data_ids:
                adverse_media.append((0, 0, {
                    'assessment_id': line.id,
                }))
        return adverse_media

    def _default_sanction_ids(self):
        sanction = []
        record = self.env['risk.category'].sudo().search([('type', '=', 'Sanction')], limit=1)
        if record:
            for line in record.data_ids:
                sanction.append((0, 0, {
                    'assessment_id': line.id,
                }))
        return sanction

    def _default_interface_ids(self):
        interface = []
        record = self.env['risk.category'].sudo().search([('type', '=', 'interface')], limit=1)
        if record:
            for line in record.data_ids:
                interface.append((0, 0, {
                    'assessment_id': line.id,
                }))
        return interface

    name = fields.Char(default='New', tracking=True, copy=False)
    state = fields.Selection(selection=[('new', 'New'), ('submitted', 'Submitted'), ('validated', 'Validated'),
                                        ('secondary', 'Secondary Approval'), ('approved', 'Approved'), ], default="new",
                             tracking=True)
    type = fields.Selection(selection=[('onboarding', 'Initial Client Onboarding'), ('trigger', 'Trigger Events'), ('periodic', 'Periodic Review'), ], default='')
    partner_id = fields.Many2one('res.partner', string='Contact')
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    date = fields.Date(string='Date', default=fields.Date.context_today)
    phone = fields.Char('Phone', related='partner_id.phone', store=True)
    email = fields.Char('Email', related='partner_id.email', store=True)
    initial_risk_scoring = fields.Char('Initial Risk Scoring', compute='_compute_initial_risk_scoring')
    submitted_user_id = fields.Many2one('res.users', string='Submitted By', default=lambda self: self.env.user)
    initial_risk_rating = fields.Char('Initial Risk Rating', compute='_compute_initial_risk_rating')
    submission_date = fields.Date('Submission Date')
    compliance_recommendation = fields.Text(string="Compliance Recommendation")
    final_risk_rating_id = fields.Many2one('risk.rating', string='Final Risk Rating')
    approved_user_id = fields.Many2one('res.users', string='Approved By')
    approval_date = fields.Date('Approval Date')
    secondary_user_id = fields.Many2one('res.users', string='Management Approval By')
    secondary_date = fields.Date('Management Approval Date')
    next_risk_assessment_date = fields.Date('Next Risk Assessment Date', compute='_get_next_risk_assessment_date',
                                            store=True)
    document_required_type_ids = fields.One2many("task.document.required.lines", 'onboarding_id')
    document_ids = fields.One2many('documents.document', 'onboarding_id')
    document_count = fields.Integer(compute='get_document_ids_count')

    service_risk_ids = fields.One2many('onboarding.service.risk', 'onboarding_id', default=_default_service_ids)
    service_risk_scoring_id = fields.Many2one('risk.scoring', 'Service Risk Scoring',
                                              compute='get_service_risk_scoring', store=True)
    service_risk_rating_id = fields.Many2one('risk.rating', 'Service Risk Rating',
                                             related='service_risk_scoring_id.rating_id', store=True)
    product_risk_ids = fields.One2many('onboarding.product.risk', 'onboarding_id', default=_default_product_ids)
    product_risk_scoring_id = fields.Many2one('risk.scoring', 'Product Risk Scoring',
                                              compute='get_product_risk_scoring', store=True)
    product_risk_rating_id = fields.Many2one('risk.rating', 'Product Risk Rating',
                                             related='product_risk_scoring_id.rating_id', store=True)
    client_risk_ids = fields.One2many('onboarding.client.risk', 'onboarding_id', default=_default_client_ids)
    client_risk_scoring_id = fields.Many2one('risk.scoring', 'Client Risk Scoring', compute='get_client_risk_scoring',
                                             store=True)
    client_risk_rating_id = fields.Many2one('risk.rating', 'Client Risk Rating',
                                            related='client_risk_scoring_id.rating_id', store=True)
    geography_risk_ids = fields.One2many('onboarding.geography.risk', 'onboarding_id', default=_default_geography_ids)
    geography_risk_scoring_id = fields.Many2one('risk.scoring', 'Geography Risk Scoring',
                                                compute='get_geography_risk_scoring', store=True)
    geography_risk_rating_id = fields.Many2one('risk.rating', 'Geography Risk Rating',
                                               related='geography_risk_scoring_id.rating_id', store=True)
    pep_risk_ids = fields.One2many('onboarding.pep.risk', 'onboarding_id', default=_default_pep_ids)
    pep_risk_scoring_id = fields.Many2one('risk.scoring', 'PEP Risk Scoring', compute='get_pep_risk_scoring',
                                          store=True)
    pep_risk_rating_id = fields.Many2one('risk.rating', 'PEP Risk Rating', related='pep_risk_scoring_id.rating_id',
                                         store=True)
    adverse_media_risk_ids = fields.One2many('onboarding.adverse_media.risk', 'onboarding_id',
                                             default=_default_adverse_media_ids)
    adverse_media_risk_scoring_id = fields.Many2one('risk.scoring', 'Adverse Media Risk Scoring',
                                                    compute='get_adverse_media_risk_scoring', store=True)
    adverse_media_risk_rating_id = fields.Many2one('risk.rating', 'Adverse Media Risk Rating',
                                                   related='adverse_media_risk_scoring_id.rating_id', store=True)
    sanction_risk_ids = fields.One2many('onboarding.sanction.risk', 'onboarding_id', default=_default_sanction_ids)
    sanction_risk_scoring_id = fields.Many2one('risk.scoring', 'Sanction Risk Scoring',
                                               compute='get_sanction_risk_scoring', store=True)
    sanction_risk_rating_id = fields.Many2one('risk.rating', 'Sanction Risk Rating',
                                              related='sanction_risk_scoring_id.rating_id', store=True)
    interface_risk_ids = fields.One2many('onboarding.interface.risk', 'onboarding_id', default=_default_interface_ids)
    interface_risk_scoring_id = fields.Many2one('risk.scoring', 'Interface Risk Scoring',
                                                compute='get_interface_risk_scoring', store=True)
    interface_risk_rating_id = fields.Many2one('risk.rating', 'Interface Risk Rating',
                                               related='interface_risk_scoring_id.rating_id', store=True)
    is_hide = fields.Boolean(compute='_check_is_hide', copy=False)
    is_validated = fields.Boolean(copy=False)
    is_secondary = fields.Boolean(copy=False)
    is_approved = fields.Boolean(copy=False)

    @api.depends('document_ids')
    def get_document_ids_count(self):
        for rec in self:
            rec.document_count = len(rec.document_ids)

    def action_draft(self):
        for rec in self:
            rec.state= 'new'

    @api.depends('final_risk_rating_id', 'approval_date')
    def _get_next_risk_assessment_date(self):
        for rec in self:
            if rec.final_risk_rating_id and rec.approval_date:
                try:
                    months_to_add = int(rec.final_risk_rating_id.type)
                    rec.next_risk_assessment_date = rec.approval_date + relativedelta(months=months_to_add)
                except (ValueError, TypeError):
                    rec.next_risk_assessment_date = False
            else:
                rec.next_risk_assessment_date = False

    @api.depends('final_risk_rating_id')
    def _check_is_hide(self):
        for rec in self:
            initial_risk = rec.initial_risk_rating in {'Low', 'Medium'}
            final_risk = rec.final_risk_rating_id.name in {'Low', 'Medium'}
            rec.is_hide = initial_risk and final_risk



    @api.depends(
        'service_risk_scoring_id.name',
        'product_risk_scoring_id.name',
        'client_risk_scoring_id.name',
        'geography_risk_scoring_id.name',
        'pep_risk_scoring_id.name',
        'sanction_risk_scoring_id.name',
        'interface_risk_scoring_id.name',
        'adverse_media_risk_scoring_id.name',
    )
    def _compute_initial_risk_scoring(self):
        for rec in self:
            fields_to_sum = [
                rec.service_risk_scoring_id.name,
                rec.product_risk_scoring_id.name,
                rec.client_risk_scoring_id.name,
                rec.geography_risk_scoring_id.name,
                rec.pep_risk_scoring_id.name,
                rec.sanction_risk_scoring_id.name,
                rec.interface_risk_scoring_id.name,
                rec.adverse_media_risk_scoring_id.name,
            ]
            try:
                rec.initial_risk_scoring = sum(int(field or 0) for field in fields_to_sum)
            except ValueError:
                rec.initial_risk_scoring = 0  # Set to default if conversion fails

    @api.depends('initial_risk_scoring')
    def _compute_initial_risk_rating(self):
        for rec in self:
            scoring = int(rec.initial_risk_scoring or 0)
            if scoring <= 20:
                rec.initial_risk_rating = 'Low'
            elif 21 <= scoring <= 32:
                rec.initial_risk_rating = 'Medium'
            elif 33 <= scoring <= 53:
                rec.initial_risk_rating = 'High'
            else:
                rec.initial_risk_rating = 'Very High'

    def action_submit(self):
        for rec in self:
            if any(not line.listing_id for line in rec.service_risk_ids):
                raise ValidationError("Please add a listing group value in the service risk table.")
            if any(not line.listing_id for line in rec.product_risk_ids):
                raise ValidationError("Please add a listing group value in the product risk table.")
            if any(not line.listing_id for line in rec.client_risk_ids):
                raise ValidationError("Please add a listing group value in the client risk table.")
            if any(not line.listing_id for line in rec.geography_risk_ids):
                raise ValidationError("Please add a listing group value in the geography risk table.")
            if any(not line.listing_id for line in rec.pep_risk_ids):
                raise ValidationError("Please add a listing group value in the pep risk table.")
            if any(not line.listing_id for line in rec.adverse_media_risk_ids):
                raise ValidationError("Please add a listing group value in the adverse media risk table.")
            if any(not line.listing_id for line in rec.sanction_risk_ids):
                raise ValidationError("Please add a listing group value in the sanction risk table.")
            if any(not line.listing_id for line in rec.interface_risk_ids):
                raise ValidationError("Please add a listing group value in the interface risk table.")
            if rec.type == 'onboarding':
                rec.name = self.env['ir.sequence'].next_by_code('initial.client.onboarding') or _('New')
            elif rec.type == 'trigger':
                rec.name = self.env['ir.sequence'].next_by_code('initial.client.trigger') or _('New')
            elif rec.type == 'periodic':
                rec.name = self.env['ir.sequence'].next_by_code('initial.client.periodic') or _('New')
            rec.submission_date = fields.Date.today()
            user = self.env['res.users'].sudo().search([('name', 'ilike', 'Aldrin D’Costa')], limit=1)
            data = {
                'res_model_id': self.env['ir.model'].sudo().search([('model', '=', 'initial.client.onboarding')]).id,
                'res_id': self.id,
                'activity_type_id': self.env['mail.activity.type'].sudo().search(
                    [('name', 'like', 'Compliance')]).id,
                'summary': _(' Assessment Validation : ' + rec.name + " -->  " + user.name),
                'note': _(' Assessment Validation : ' + rec.name + " -->  " + user.name),
                'date_deadline': fields.Date.today() + timedelta(days=1),
                'user_id': user.id
            }
            self.env['mail.activity'].sudo().create(data)

            rec.state = 'submitted'

    def action_validated(self):
        for rec in self:
            if not rec.final_risk_rating_id:
                raise ValidationError("Please add 'Final Risk Rating'")
            type_mapping = {
                'onboarding': 'Initial Client Onboarding',
                'trigger': 'Trigger Events',
                'periodic': 'Periodic Review Assessment'
            }
            type = type_mapping.get(rec.type, '')
            body = (
                f"<b>{type}</b> for {rec.partner_id.name} with initial risk rating as "
                f"{rec.initial_risk_rating} has been validated as {rec.final_risk_rating_id.name}.<br><br>"
                f"<b>Compliance Recommendation:</b> {rec.compliance_recommendation}"
            )
            self.message_post(body=body)

            activity = self.env['mail.activity'].sudo().search([
                ('res_model_id', '=',
                 self.env['ir.model'].sudo().search([('model', '=', 'initial.client.onboarding')]).id),
                ('res_id', '=', self.id),
                ('activity_type_id', '=',self.env['mail.activity.type'].sudo().search([('name', 'like', 'Compliance')]).id),
            ], limit=1)
            if activity:
                activity.action_done()  # Mark the activity as done
            if rec.is_hide:
                user = self.env['res.users'].sudo().search([('name', 'ilike', 'Aldrin D’Costa')], limit=1)
                data = {
                    'res_model_id': self.env['ir.model'].sudo().search(
                        [('model', '=', 'initial.client.onboarding')]).id,
                    'res_id': self.id,
                    'activity_type_id': self.env['mail.activity.type'].sudo().search(
                        [('name', 'like', 'Compliance')]).id,
                    'summary': _(' Pending Compliance Officer Approval : ' + rec.name + " -->  " + user.name),
                    'note': _(' Pending Compliance Officer Approval : ' + rec.name + " -->  " + user.name),
                    'date_deadline': fields.Date.today() + timedelta(days=1),
                    'user_id': user.id
                }
                self.env['mail.activity'].sudo().create(data)
            else:
                user = self.env['res.users'].sudo().search([('name', 'ilike', 'Ramy Amin')], limit=1)
                data = {
                    'res_model_id': self.env['ir.model'].sudo().search(
                        [('model', '=', 'initial.client.onboarding')]).id,
                    'res_id': self.id,
                    'activity_type_id': self.env['mail.activity.type'].sudo().search(
                        [('name', 'like', 'Compliance')]).id,
                    'summary': _(' Pending Management Approval : ' + rec.name + " -->  " + user.name),
                    'note': _(' Pending Management Approval : ' + rec.name + " -->  " + user.name),
                    'date_deadline': fields.Date.today() + timedelta(days=1),
                    'user_id': user.id
                }
                self.env['mail.activity'].sudo().create(data)

            rec.is_validated = True
            rec.state = 'validated'

    def action_secondary(self):
        for rec in self:
            rec.secondary_date = fields.Date.today()
            rec.secondary_user_id = self.env.user.id
            activity = self.env['mail.activity'].sudo().search([
                ('res_model_id', '=',
                 self.env['ir.model'].sudo().search([('model', '=', 'initial.client.onboarding')]).id),
                ('res_id', '=', self.id),
                ('activity_type_id', '=',
                 self.env['mail.activity.type'].sudo().search([('name', 'like', 'Compliance')]).id),
            ], limit=1)
            if activity:
                activity.action_done()  # Mark the activity as done
            rec.is_secondary = True
            rec.state = 'secondary'

    def action_approved(self):
        for rec in self:
            activity = self.env['mail.activity'].sudo().search([
                ('res_model_id', '=',
                 self.env['ir.model'].sudo().search([('model', '=', 'initial.client.onboarding')]).id),
                ('res_id', '=', self.id),
                ('activity_type_id', '=',
                 self.env['mail.activity.type'].sudo().search([('name', 'like', 'Compliance')]).id),
            ], limit=1)
            if activity:
                activity.action_done()
            rec.approval_date = fields.Date.today()
            rec.approved_user_id = self.env.user.id
            rec.is_approved = True
            rec.state = 'approved'

    @api.depends('service_risk_ids.scoring_id.name')
    def get_service_risk_scoring(self):
        for rec in self:
            max_score = 0
            for line in rec.service_risk_ids:
                if line.scoring_id.name and line.scoring_id.name.isdigit():
                    max_score = max(max_score, int(line.scoring_id.name))
            rec.service_risk_scoring_id = self.env['risk.scoring'].sudo().search([('name', '=', str(max_score))],
                                                                                 limit=1).id or False

    @api.depends('product_risk_ids.scoring_id.name')
    def get_product_risk_scoring(self):
        for rec in self:
            max_score = 0
            for line in rec.product_risk_ids:
                if line.scoring_id.name and line.scoring_id.name.isdigit():
                    max_score = max(max_score, int(line.scoring_id.name))
            rec.product_risk_scoring_id = self.env['risk.scoring'].sudo().search([('name', '=', str(max_score))],
                                                                                 limit=1).id or False

    @api.depends('client_risk_ids.scoring_id.name')
    def get_client_risk_scoring(self):
        for rec in self:
            max_score = 0
            for line in rec.client_risk_ids:
                if line.scoring_id.name and line.scoring_id.name.isdigit():
                    max_score = max(max_score, int(line.scoring_id.name))
            rec.client_risk_scoring_id = self.env['risk.scoring'].sudo().search([('name', '=', str(max_score))],
                                                                                limit=1).id or False

    @api.depends('pep_risk_ids.scoring_id.name')
    def get_pep_risk_scoring(self):
        for rec in self:
            max_score = 0
            for line in rec.pep_risk_ids:
                if line.scoring_id.name and line.scoring_id.name.isdigit():
                    max_score = max(max_score, int(line.scoring_id.name))
            rec.pep_risk_scoring_id = self.env['risk.scoring'].sudo().search([('name', '=', str(max_score))],
                                                                             limit=1).id or False

    @api.depends('geography_risk_ids.scoring_id.name')
    def get_geography_risk_scoring(self):
        for rec in self:
            max_score = 0
            for line in rec.geography_risk_ids:
                if line.scoring_id.name and line.scoring_id.name.isdigit():
                    max_score = max(max_score, int(line.scoring_id.name))
            rec.geography_risk_scoring_id = self.env['risk.scoring'].sudo().search([('name', '=', str(max_score))],
                                                                                   limit=1).id or False

    @api.depends('adverse_media_risk_ids.scoring_id.name')
    def get_adverse_media_risk_scoring(self):
        for rec in self:
            max_score = 0
            for line in rec.adverse_media_risk_ids:
                if line.scoring_id.name and line.scoring_id.name.isdigit():
                    max_score = max(max_score, int(line.scoring_id.name))
            rec.adverse_media_risk_scoring_id = self.env['risk.scoring'].sudo().search([('name', '=', str(max_score))],
                                                                                       limit=1).id or False

    @api.depends('sanction_risk_ids.scoring_id.name')
    def get_sanction_risk_scoring(self):
        for rec in self:
            max_score = 0
            for line in rec.sanction_risk_ids:
                if line.scoring_id.name and line.scoring_id.name.isdigit():
                    max_score = max(max_score, int(line.scoring_id.name))
            rec.sanction_risk_scoring_id = self.env['risk.scoring'].sudo().search([('name', '=', str(max_score))],
                                                                                  limit=1).id or False

    @api.depends('interface_risk_ids.scoring_id.name')
    def get_interface_risk_scoring(self):
        for rec in self:
            max_score = 0
            for line in rec.interface_risk_ids:
                if line.scoring_id.name and line.scoring_id.name.isdigit():
                    max_score = max(max_score, int(line.scoring_id.name))
            rec.interface_risk_scoring_id = self.env['risk.scoring'].sudo().search([('name', '=', str(max_score))],
                                                                                   limit=1).id or False

class OnboardingServiceRisk(models.Model):
    _name = 'onboarding.service.risk'
    _rec_name = 'assessment_id'

    onboarding_id = fields.Many2one('initial.client.onboarding')
    name = fields.Char('Description')
    assessment_id = fields.Many2one('assessment.list', readonly=True, string='Assessment List')
    listing_ids = fields.Many2many('listing.group.line', compute='get_related_listing_ids', string='List Group Value')
    listing_id = fields.Many2one('listing.group.line', string='List Group Value')
    scoring_id = fields.Many2one('risk.scoring', readonly=True, string='Risk Scoring')
    rating_id = fields.Many2one('risk.rating', string='Risk Rating', related='scoring_id.rating_id', store=True)

    @api.onchange('listing_id')
    def onchange_scoring(self):
        for rec in self:
            rec.scoring_id = rec.listing_id.scoring_id.id

    @api.depends('assessment_id')
    def get_related_listing_ids(self):
        for rec in self:
            rec.listing_ids = self.env['listing.group.line'].sudo().search([
                ('listing_id', '=', rec.assessment_id.listing_id.id)
            ]).ids

class OnboardingProductRisk(models.Model):
    _name = 'onboarding.product.risk'
    _rec_name = 'assessment_id'

    onboarding_id = fields.Many2one('initial.client.onboarding')
    name = fields.Char('Description')
    assessment_id = fields.Many2one('assessment.list', readonly=True, string='Assessment List')
    listing_ids = fields.Many2many('listing.group.line', compute='get_related_listing_ids', string='List Group Value')
    listing_id = fields.Many2one('listing.group.line', string='List Group Value')
    scoring_id = fields.Many2one('risk.scoring', readonly=True, string='Risk Scoring')
    rating_id = fields.Many2one('risk.rating', string='Risk Rating', related='scoring_id.rating_id', store=True)

    @api.onchange('listing_id')
    def onchange_scoring(self):
        for rec in self:
            rec.scoring_id = rec.listing_id.scoring_id.id

    @api.depends('assessment_id')
    def get_related_listing_ids(self):
        for rec in self:
            rec.listing_ids = self.env['listing.group.line'].sudo().search([
                ('listing_id', '=', rec.assessment_id.listing_id.id)
            ]).ids

class OnboardingClientRisk(models.Model):
    _name = 'onboarding.client.risk'
    _rec_name = 'assessment_id'

    onboarding_id = fields.Many2one('initial.client.onboarding')
    name = fields.Char('Description')
    assessment_id = fields.Many2one('assessment.list', readonly=True, string='Assessment List')
    listing_ids = fields.Many2many('listing.group.line', compute='get_related_listing_ids', string='List Group Value')
    listing_id = fields.Many2one('listing.group.line', string='List Group Value')
    scoring_id = fields.Many2one('risk.scoring', readonly=True, string='Risk Scoring')
    rating_id = fields.Many2one('risk.rating', string='Risk Rating', related='scoring_id.rating_id', store=True)

    @api.onchange('listing_id')
    def onchange_scoring(self):
        for rec in self:
            rec.scoring_id = rec.listing_id.scoring_id.id

    @api.depends('assessment_id')
    def get_related_listing_ids(self):
        for rec in self:
            rec.listing_ids = self.env['listing.group.line'].sudo().search([
                ('listing_id', '=', rec.assessment_id.listing_id.id)
            ]).ids

class OnboardingGeographyRisk(models.Model):
    _name = 'onboarding.geography.risk'
    _rec_name = 'assessment_id'

    onboarding_id = fields.Many2one('initial.client.onboarding')
    name = fields.Char('Description')
    assessment_id = fields.Many2one('assessment.list', readonly=True, string='Assessment List')
    listing_ids = fields.Many2many('listing.group.line', compute='get_related_listing_ids', string='List Group Value')
    listing_id = fields.Many2one('listing.group.line', string='List Group Value')
    scoring_id = fields.Many2one('risk.scoring', readonly=True, string='Risk Scoring')
    rating_id = fields.Many2one('risk.rating', string='Risk Rating', related='scoring_id.rating_id', store=True)

    @api.onchange('listing_id')
    def onchange_scoring(self):
        for rec in self:
            rec.scoring_id = rec.listing_id.scoring_id.id

    @api.depends('assessment_id')
    def get_related_listing_ids(self):
        for rec in self:
            rec.listing_ids = self.env['listing.group.line'].sudo().search([
                ('listing_id', '=', rec.assessment_id.listing_id.id)
            ]).ids

class OnboardingPepRisk(models.Model):
    _name = 'onboarding.pep.risk'
    _rec_name = 'assessment_id'

    onboarding_id = fields.Many2one('initial.client.onboarding')
    name = fields.Char('Description')
    assessment_id = fields.Many2one('assessment.list', readonly=True, string='Assessment List')
    listing_ids = fields.Many2many('listing.group.line', compute='get_related_listing_ids', string='List Group Value')
    listing_id = fields.Many2one('listing.group.line', string='List Group Value')
    scoring_id = fields.Many2one('risk.scoring', readonly=True, string='Risk Scoring')
    rating_id = fields.Many2one('risk.rating', string='Risk Rating', related='scoring_id.rating_id', store=True)

    @api.onchange('listing_id')
    def onchange_scoring(self):
        for rec in self:
            rec.scoring_id = rec.listing_id.scoring_id.id

    @api.depends('assessment_id')
    def get_related_listing_ids(self):
        for rec in self:
            rec.listing_ids = self.env['listing.group.line'].sudo().search([
                ('listing_id', '=', rec.assessment_id.listing_id.id)
            ]).ids

class OnboardingAdverseRisk(models.Model):
    _name = 'onboarding.adverse_media.risk'
    _rec_name = 'assessment_id'

    onboarding_id = fields.Many2one('initial.client.onboarding')
    name = fields.Char('Description')
    assessment_id = fields.Many2one('assessment.list', readonly=True, string='Assessment List')
    listing_ids = fields.Many2many('listing.group.line', compute='get_related_listing_ids', string='List Group Value')
    listing_id = fields.Many2one('listing.group.line', string='List Group Value')
    scoring_id = fields.Many2one('risk.scoring', readonly=True, string='Risk Scoring')
    rating_id = fields.Many2one('risk.rating', string='Risk Rating', related='scoring_id.rating_id', store=True)

    @api.onchange('listing_id')
    def onchange_scoring(self):
        for rec in self:
            rec.scoring_id = rec.listing_id.scoring_id.id

    @api.depends('assessment_id')
    def get_related_listing_ids(self):
        for rec in self:
            rec.listing_ids = self.env['listing.group.line'].sudo().search([
                ('listing_id', '=', rec.assessment_id.listing_id.id)
            ]).ids

class OnboardingSanctionRisk(models.Model):
    _name = 'onboarding.sanction.risk'
    _rec_name = 'assessment_id'

    onboarding_id = fields.Many2one('initial.client.onboarding')
    name = fields.Char('Description')
    assessment_id = fields.Many2one('assessment.list', readonly=True, string='Assessment List')
    listing_ids = fields.Many2many('listing.group.line', compute='get_related_listing_ids', string='List Group Value')
    listing_id = fields.Many2one('listing.group.line', string='List Group Value')
    scoring_id = fields.Many2one('risk.scoring', readonly=True, string='Risk Scoring')
    rating_id = fields.Many2one('risk.rating', string='Risk Rating', related='scoring_id.rating_id', store=True)

    @api.onchange('listing_id')
    def onchange_scoring(self):
        for rec in self:
            rec.scoring_id = rec.listing_id.scoring_id.id

    @api.depends('assessment_id')
    def get_related_listing_ids(self):
        for rec in self:
            rec.listing_ids = self.env['listing.group.line'].sudo().search([
                ('listing_id', '=', rec.assessment_id.listing_id.id)
            ]).ids

class OnboardingInterfaceRisk(models.Model):
    _name = 'onboarding.interface.risk'
    _rec_name = 'assessment_id'

    onboarding_id = fields.Many2one('initial.client.onboarding')
    name = fields.Char('Description')
    assessment_id = fields.Many2one('assessment.list', readonly=True, string='Assessment List')
    listing_ids = fields.Many2many('listing.group.line', compute='get_related_listing_ids', string='List Group Value')
    listing_id = fields.Many2one('listing.group.line', string='List Group Value')
    scoring_id = fields.Many2one('risk.scoring', readonly=True, string='Risk Scoring')
    rating_id = fields.Many2one('risk.rating', string='Risk Rating', related='scoring_id.rating_id', store=True)

    @api.onchange('listing_id')
    def onchange_scoring(self):
        for rec in self:
            rec.scoring_id = rec.listing_id.scoring_id.id

    @api.depends('assessment_id')
    def get_related_listing_ids(self):
        for rec in self:
            rec.listing_ids = self.env['listing.group.line'].sudo().search([
                ('listing_id', '=', rec.assessment_id.listing_id.id)
            ]).ids
