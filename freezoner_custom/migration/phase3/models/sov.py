from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class SaleSOV(models.Model):
    _name = 'sale.sov'
    _description = 'Statement of Values'
    _order = 'sequence, id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Basic Fields
    name = fields.Char(
        string='Description',
        required=True,
        tracking=True
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    active = fields.Boolean(
        default=True,
        tracking=True
    )

    # Related Fields
    sale_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        required=True,
        ondelete='cascade',
        tracking=True,
        index=True
    )
    project_id = fields.Many2one(
        'project.project',
        related='sale_id.project_ids',
        string='Project',
        store=True,
        tracking=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        related='sale_id.partner_id',
        string='Customer',
        store=True,
        tracking=True
    )

    # Financial Fields
    revenue = fields.Float(
        string='Revenue',
        tracking=True,
        digits=(16, 2)
    )
    planned_expenses = fields.Float(
        string='Planned Expenses',
        tracking=True,
        digits=(16, 2)
    )
    net = fields.Float(
        string='Net Achievement',
        compute='_compute_net',
        store=True,
        digits=(16, 2)
    )
    actual_expenses = fields.Float(
        string='Actual Expenses',
        compute='_compute_actual_expenses',
        store=True,
        digits=(16, 2)
    )
    profit_margin = fields.Float(
        string='Profit Margin',
        compute='_compute_profit_margin',
        store=True,
        digits=(16, 2)
    )

    # Analytic Fields
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        related='project_id.analytic_account_id',
        store=True
    )
    analytic_line_ids = fields.One2many(
        'account.analytic.line',
        'sov_id',
        string='Analytic Lines'
    )

    # Status Fields
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status',
        default='draft',
        tracking=True,
        required=True
    )

    # Computed Methods
    @api.depends('revenue', 'planned_expenses')
    def _compute_net(self):
        for record in self:
            record.net = record.revenue - record.planned_expenses

    @api.depends('analytic_line_ids.amount')
    def _compute_actual_expenses(self):
        for record in self:
            record.actual_expenses = sum(
                line.amount for line in record.analytic_line_ids
                if line.amount < 0
            )

    @api.depends('revenue', 'actual_expenses')
    def _compute_profit_margin(self):
        for record in self:
            if record.revenue:
                record.profit_margin = (
                    (record.revenue + record.actual_expenses) / record.revenue
                ) * 100
            else:
                record.profit_margin = 0.0

    # Action Methods
    def action_draft(self):
        self.write({'state': 'draft'})

    def action_in_progress(self):
        self.write({'state': 'in_progress'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_view_analytic_lines(self):
        self.ensure_one()
        action = self.env.ref('analytic.account_analytic_line_action').read()[0]
        action['domain'] = [('sov_id', '=', self.id)]
        action['context'] = {
            'default_sov_id': self.id,
            'default_account_id': self.analytic_account_id.id,
            'default_project_id': self.project_id.id,
            'default_partner_id': self.partner_id.id
        }
        return action

    # Constraint Methods
    @api.constrains('revenue', 'planned_expenses')
    def _check_amounts(self):
        for record in self:
            if record.revenue < 0:
                raise ValidationError(_("Revenue cannot be negative."))
            if record.planned_expenses < 0:
                raise ValidationError(_("Planned expenses cannot be negative."))

    # CRUD Methods
    @api.model_create_multi
    def create(self, vals_list):
        # Set sequence if not provided
        for vals in vals_list:
            if 'sequence' not in vals:
                vals['sequence'] = self.env['ir.sequence'].next_by_code('sale.sov')
        return super().create(vals_list)

    def write(self, vals):
        return super().write(vals)

    def copy(self, default=None):
        default = dict(default or {})
        default.update({
            'name': _("%s (Copy)") % self.name,
            'state': 'draft',
            'analytic_line_ids': [],
        })
        return super().copy(default)

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    sov_id = fields.Many2one(
        'sale.sov',
        string='SOV Item',
        ondelete='set null',
        tracking=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        # Update SOV actual expenses when analytic lines are created
        for line in lines:
            if line.sov_id:
                line.sov_id._compute_actual_expenses()
        return lines

    def write(self, vals):
        res = super().write(vals)
        # Update SOV actual expenses when analytic lines are modified
        if 'amount' in vals or 'sov_id' in vals:
            for line in self:
                if line.sov_id:
                    line.sov_id._compute_actual_expenses()
        return res

    def unlink(self):
        sov_ids = self.mapped('sov_id')
        res = super().unlink()
        # Update SOV actual expenses when analytic lines are deleted
        for sov in sov_ids:
            sov._compute_actual_expenses()
        return res 