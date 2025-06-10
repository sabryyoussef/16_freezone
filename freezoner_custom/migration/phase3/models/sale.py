from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from collections import defaultdict

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Basic Fields
    active = fields.Boolean(
        default=True,
        copy=False,
        tracking=True
    )
    system_expiry_date = fields.Date(
        string="System Expiry Date",
        copy=False
    )
    
    # State Fields
    state = fields.Selection([
        ('draft', "Pro-forma Invoice"),
        ('sent', "Pro-forma Invoice Sent"),
        ('sale', "Pro-forma Confirm"),
        ('done', "Locked"),
        ('cancel', "Cancelled"),
    ], string="Status",
        readonly=True,
        copy=False,
        index=True,
        tracking=3,
        default='draft'
    )
    
    payment_method = fields.Selection([
        ('bank', "Bank"),
        ('visa', "Stripe"),
    ], string="Payment Method",
        tracking=3,
        default='bank',
        required=True
    )

    # Related Fields
    sov_ids = fields.One2many(
        'sale.sov',
        'sale_id',
        string='SOV Items'
    )
    analytic_item_ids = fields.Many2many(
        'account.analytic.line',
        string='Analytic Items',
        compute='_compute_analytic_item_ids',
        store=True
    )

    # Computed Fields
    total_revenue = fields.Float(
        string='Total Revenue',
        compute='_compute_total_revenue',
        store=True
    )
    total_planned_expenses = fields.Float(
        string='Total Planned Expenses',
        compute='_compute_total_planned_expenses',
        store=True
    )
    total_net_achievement = fields.Float(
        string='Total Net Achievement',
        compute='_compute_total_net_achievement',
        store=True
    )
    date_confirmed = fields.Datetime(
        compute='_compute_first_confirmed_date',
        store=True
    )
    validity_date = fields.Date(
        string="Expiration",
        compute='_compute_validity_date',
        store=True,
        readonly=True,
        copy=False,
        precompute=True
    )
    is_expired = fields.Boolean(
        compute='_compute_is_expired',
        store=True
    )

    # Computed Methods
    @api.depends('validity_date', 'state')
    def _compute_is_expired(self):
        today = fields.Date.context_today(self)
        for order in self:
            order.is_expired = (
                order.validity_date and
                order.state in ['draft', 'sent'] and
                order.validity_date < today
            )

    @api.depends('create_date')
    def _compute_validity_date(self):
        for order in self:
            if order.create_date:
                order.validity_date = order.create_date.date() + timedelta(days=30)
            else:
                order.validity_date = False

    @api.depends('message_ids')
    def _compute_first_confirmed_date(self):
        for order in self:
            first_confirmed_date = None
            for message in order.message_ids:
                if message.subtype_id.description == 'Quotation confirmed':
                    if first_confirmed_date is None or message.date < first_confirmed_date:
                        first_confirmed_date = message.date
            order.date_confirmed = first_confirmed_date

    @api.depends('name')
    def _compute_analytic_item_ids(self):
        for order in self:
            analytic_items = self.env['account.analytic.line'].sudo().search([
                ('account_id.name', 'ilike', order.name)
            ])
            order.analytic_item_ids = analytic_items.ids

    @api.depends('sov_ids.revenue')
    def _compute_total_revenue(self):
        for order in self:
            order.total_revenue = sum(line.revenue for line in order.sov_ids)

    @api.depends('sov_ids.planned_expenses')
    def _compute_total_planned_expenses(self):
        for order in self:
            order.total_planned_expenses = sum(
                line.planned_expenses for line in order.sov_ids
            )

    @api.depends('sov_ids.net')
    def _compute_total_net_achievement(self):
        for order in self:
            order.total_net_achievement = sum(line.net for line in order.sov_ids)

    # Action Methods
    def action_sale_expiration(self):
        today = fields.Date.context_today(self)
        expired_orders = self.env['sale.order'].sudo().search([
            ('state', 'in', ['draft', 'sent']),
            ('validity_date', '<=', today)
        ])
        
        for order in expired_orders:
            if order.validity_date and order.is_expired and order.validity_date <= today:
                order.write({
                    'state': 'cancel',
                    'system_expiry_date': today
                })

    def action_sale_expiration_archive(self):
        today = fields.Date.context_today(self)
        orders_to_archive = self.env['sale.order'].sudo().search([
            ('state', '=', 'cancel'),
            ('system_expiry_date', '<=', today)
        ])
        
        for order in orders_to_archive:
            if order.system_expiry_date:
                days_since_expiry = (today - order.system_expiry_date).days
                if days_since_expiry >= 30:
                    order.write({'active': False})

    def action_cancel(self):
        res = super().action_cancel()
        for order in self:
            for task in order.tasks_ids:
                task.document_type_ids.unlink()
                task.document_required_type_ids.unlink()
        return res

    def action_update_manager(self):
        for order in self:
            for project in order.project_ids:
                project.write({'user_id': order.user_id.id})

    # Override Methods
    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        invoice_vals.update({
            'sale_id': self.id,
            'payment_method': self.payment_method,
        })
        return invoice_vals

    # Constraint Methods
    @api.constrains('partner_id')
    def _check_partner(self):
        for order in self:
            user = self.env.user
            team = self.env['crm.team'].sudo().search([('id', '=', 1)])
            if team and user.id in team.member_ids.ids:
                partner = order.partner_id
                if partner and partner.create_date:
                    create_date = partner.create_date.date()
                    if create_date < (fields.Date.context_today(self) - timedelta(days=180)):
                        raise ValidationError(_(
                            "Customer Profile has been created more than six (6) months ago. "
                            "As a member of Sales Team, you are not allowed to create an invoice "
                            "for this contact. Please contact your Line Manager for assistance."
                        ))

    # CRUD Methods
    @api.model_create_multi
    def create(self, vals_list):
        # Validate partners before creation
        for vals in vals_list:
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            if partner:
                if partner.company_type == 'company':
                    if not partner.phone:
                        raise ValidationError(_("Please add phone number for the customer"))
                    if not partner.email:
                        raise ValidationError(_("Please add email for the customer"))
                    if not partner.license_authority_id:
                        raise ValidationError(_("Please add license authority for the customer"))
                    if not partner.incorporation_date:
                        raise ValidationError(_("Please add incorporation date for the customer"))
                    if not partner.license_number:
                        raise ValidationError(_("Please add license number for the customer"))
                elif partner.company_type == 'person':
                    if not partner.phone:
                        raise ValidationError(_("Please add phone number for the customer"))
                    if not partner.email:
                        raise ValidationError(_("Please add email for the customer"))
                    if not partner.gender:
                        raise ValidationError(_("Please add gender for the customer"))
                    if not partner.nationality_id:
                        raise ValidationError(_("Please add nationality for the customer"))
        
        # Create records in batch
        return super().create(vals_list)

    def write(self, vals):
        # Validate partners after write
        res = super().write(vals)
        for order in self:
            if order.partner_id:
                if order.partner_id.company_type == 'company':
                    if not order.partner_id.phone:
                        raise ValidationError(_("Please add phone number for the customer"))
                    if not order.partner_id.email:
                        raise ValidationError(_("Please add email for the customer"))
                    if not order.partner_id.license_authority_id:
                        raise ValidationError(_("Please add license authority for the customer"))
                    if not order.partner_id.incorporation_date:
                        raise ValidationError(_("Please add incorporation date for the customer"))
                    if not order.partner_id.license_number:
                        raise ValidationError(_("Please add license number for the customer"))
                elif order.partner_id.company_type == 'person':
                    if not order.partner_id.phone:
                        raise ValidationError(_("Please add phone number for the customer"))
                    if not order.partner_id.email:
                        raise ValidationError(_("Please add email for the customer"))
                    if not order.partner_id.gender:
                        raise ValidationError(_("Please add gender for the customer"))
                    if not order.partner_id.nationality_id:
                        raise ValidationError(_("Please add nationality for the customer"))
        return res 