from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class AccountMove(models.Model):
    """
    Account Move Model Extension
    Extends the standard account move with additional fields and functionality
    for project-related accounting operations
    """
    _inherit = 'account.move'
    _description = 'Account Move Extension'

    sale_id = fields.Many2one(
        'sale.order',
        string='Sales Order',
        tracking=True,
        help='Related sales order',
        index=True
    )
    
    payment_method = fields.Selection([
        ('bank', 'Bank Transfer'),
        ('visa', 'Credit Card (Stripe)'),
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('other', 'Other')
    ], string='Payment Method',
        tracking=True,
        default='bank',
        help='Method used for payment processing'
    )
    
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        tracking=True,
        help='Related project',
        index=True
    )
    
    task_id = fields.Many2one(
        'project.task',
        string='Task',
        tracking=True,
        help='Related task',
        index=True
    )
    
    payment_reference = fields.Char(
        string='Payment Reference',
        tracking=True,
        help='External reference for the payment'
    )
    
    payment_date = fields.Date(
        string='Payment Date',
        tracking=True,
        help='Date when the payment was received'
    )
    
    payment_status = fields.Selection([
        ('pending', 'Pending'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    ], string='Payment Status',
        tracking=True,
        default='pending',
        compute='_compute_payment_status',
        store=True,
        help='Current status of the payment'
    )
    
    payment_amount = fields.Monetary(
        string='Payment Amount',
        tracking=True,
        compute='_compute_payment_amount',
        store=True,
        help='Total amount of the payment'
    )
    
    currency_id = fields.Many2one(
        related='company_id.currency_id',
        string='Currency',
        store=True
    )
    
    payment_notes = fields.Text(
        string='Payment Notes',
        tracking=True,
        help='Additional notes about the payment'
    )
    
    is_project_payment = fields.Boolean(
        string='Is Project Payment',
        compute='_compute_is_project_payment',
        store=True,
        help='Indicates if this move is related to a project payment'
    )

    @api.depends('sale_id', 'project_id', 'task_id')
    def _compute_is_project_payment(self):
        for move in self:
            move.is_project_payment = bool(move.sale_id or move.project_id or move.task_id)

    @api.depends('amount_residual', 'amount_total')
    def _compute_payment_status(self):
        for move in self:
            if move.state == 'draft':
                move.payment_status = 'pending'
            elif move.state == 'cancel':
                move.payment_status = 'cancelled'
            elif move.amount_residual == 0:
                move.payment_status = 'paid'
            elif move.amount_residual < move.amount_total:
                move.payment_status = 'partial'
            else:
                move.payment_status = 'pending'

    @api.depends('amount_total', 'amount_residual')
    def _compute_payment_amount(self):
        for move in self:
            move.payment_amount = move.amount_total - move.amount_residual

    @api.constrains('payment_method', 'payment_date')
    def _check_payment_method_date(self):
        for move in self:
            if move.payment_method and not move.payment_date:
                raise ValidationError(_('Payment date is required when payment method is specified.'))

    def action_register_payment(self):
        self.ensure_one()
        if self.payment_method == 'visa':
            return self._action_register_stripe_payment()
        return super(AccountMove, self).action_register_payment()

    def _action_register_stripe_payment(self):
        """Handle Stripe payment registration"""
        self.ensure_one()
        # Implement Stripe payment logic here
        return {
            'type': 'ir.actions.act_window',
            'name': _('Register Stripe Payment'),
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_model': 'account.move',
                'active_ids': self.ids,
                'default_payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
            }
        }

    def action_mark_as_paid(self):
        self.ensure_one()
        if self.payment_status != 'paid':
            self.write({
                'payment_status': 'paid',
                'payment_date': fields.Date.today()
            })
        return True

    def action_cancel_payment(self):
        self.ensure_one()
        if self.payment_status not in ['cancelled', 'failed']:
            self.write({
                'payment_status': 'cancelled',
                'payment_notes': f"Cancelled by {self.env.user.name} on {fields.Datetime.now()}"
            })
        return True

    @api.model
    def create(self, vals):
        if vals.get('payment_method') == 'visa' and not vals.get('payment_date'):
            vals['payment_date'] = fields.Date.today()
        return super(AccountMove, self).create(vals)

    def write(self, vals):
        if 'payment_method' in vals and vals['payment_method'] == 'visa' and not vals.get('payment_date'):
            vals['payment_date'] = fields.Date.today()
        return super(AccountMove, self).write(vals)

    def name_get(self):
        result = []
        for move in self:
            name = f"{move.name} - {move.payment_method}"
            if move.sale_id:
                name += f" - {move.sale_id.name}"
            result.append((move.id, name))
        return result 