
from odoo import api, fields, models
from odoo.exceptions import ValidationError

class CommissionSOV(models.Model):
    _name = 'commission.sale.sov'


    @api.depends('sale_id')
    def _get_sov_lines(self):
        for rec in self:
            rec.sov_ids = self.sale_id.sov_ids.ids

    @api.onchange('sov_id')
    def _onchange_data(self):
        for rec in self:
            rec.name = rec.sov_id.revenue
            rec.planned_expenses = rec.sov_id.planned_expenses
            rec.revenue = rec.sov_id.revenue
            rec.profit = rec.sov_id.profit
            rec.tax = rec.sov_id.tax
            rec.net = rec.sov_id.net
            rec.commission_attribute = rec.sov_id.commission_attribute

    @api.depends('sale_id')
    def get_date(self):
        for rec in self:
            rec.date_order = rec.sale_id.date_confirmed.date() if rec.sale_id and rec.sale_id.date_confirmed else False

    @api.constrains('sov_id', 'commission_id')
    def _check_unique_sov_per_member(self):
        for rec in self:
            if rec.sov_id and rec.commission_id and rec.commission_id.member_id:
                domain = [
                    ('sov_id', '=', rec.sov_id.id),
                    ('commission_member_uid', '=', rec.commission_id.member_id.id),
                    ('id', '!=', rec.id),  # Exclude self
                ]
                existing = self.search(domain, limit=1)
                if existing:
                    raise ValidationError(
                        f"The SOV line '{rec.sov_id.product_id.name}' is already assigned to a commission for this member."
                    )

    commission_id = fields.Many2one('crm.commission')
    commission_member_uid = fields.Many2one('res.users', related='commission_id.member_id', store=True)
    state = fields.Selection(related='commission_id.state', store=True)
    sale_id = fields.Many2one('sale.order', domain=[('state', '=', 'sale')])
    sov_ids = fields.Many2many('sale.sov', compute='_get_sov_lines')
    sov_id = fields.Many2one('sale.sov', domain="[('id', 'in', sov_ids)]")
    name = fields.Char('Description')
    date_order = fields.Date(compute='get_date')
    partner_id = fields.Many2one('res.partner', string='Client Name',related='sale_id.partner_id', store=True)
    revenue = fields.Float('Revenue', readonly=False)
    planned_expenses = fields.Float('Planned Expenses', readonly=False)
    profit = fields.Float('Profit', compute='get_profit', store=True)
    tax = fields.Float('Tax', compute='get_tax', store=True)
    net = fields.Float('Net Achievement', compute='get_net', store=True)
    commission_attribute = fields.Selection(string="Commission Attribute",
                                            selection=[('license', 'Cross/Up Sell License'),
                                                       ('value', 'Cross/Up Sell Value Added Service '),
                                                       ('renewals', 'Renewals'),
                                                       ('network', 'Personal Network'),
                                                       ('annual', 'Annual Contract'),
                                                       ('bank', 'Banking Deals'),
                                                       ('accounting', 'Accounting Deals'),
                                                       ('misc', 'Miscellaneous Deals'), ], readonly=False)


    @api.depends('revenue', 'planned_expenses')
    def get_profit(self):
        for rec in self:
            rec.profit = rec.revenue - rec.planned_expenses

    @api.depends('profit')
    def get_tax(self):
        for rec in self:
            rec.tax = (rec.profit / 1.05) * 0.05

    @api.depends('profit', 'tax')
    def get_net(self):
        for rec in self:
            rec.net = rec.profit - rec.tax
