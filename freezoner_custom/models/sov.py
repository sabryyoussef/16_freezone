
from odoo import api, fields, models

class SOV(models.Model):
    _name = 'sale.sov'
    _rec_name = 'product_id'

    sale_id = fields.Many2one('sale.order')
    state = fields.Selection(related='sale_id.state')
    product_id = fields.Many2one('product.product', string='Description')
    name = fields.Char(string='Name')
    qty = fields.Float('Qty', default=1.0)
    unit_price = fields.Float('Unit Price')
    unit_cost = fields.Float('Unit Cost')
    revenue = fields.Float('Revenue', compute='get_revenue',store=True)
    planned_expenses = fields.Float('Planned Expenses', compute='get_planned_expenses',store=True)
    profit = fields.Float('Profit', compute='get_profit',store=True)
    tax = fields.Float('Tax', compute='get_tax',store=True)
    net = fields.Float('Net Achievement', compute='get_net',store=True)
    commission_attribute = fields.Selection(string="Commission Attribute",
                                            selection=[('license', 'Cross/Up Sell License'),
                                                       ('value', 'Cross/Up Sell Value Added Service '),
                                                       ('renewals', 'Renewals'),
                                                       ('network', 'Personal Network'),
                                                       ('annual', 'Annual Contract'),
                                                       ('bank', 'Banking Deals'),
                                                       ('accounting', 'Accounting Deals'),
                                                       ('misc', 'Miscellaneous Deals'), ])
    user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user)
    is_access_price = fields.Boolean(compute='_compute_is_access_price')
    sale_commission_user_ids = fields.Many2many('res.users',string='User',
                                                compute='_get_sale_commission_user_id')

    def _get_sale_commission_user_id(self):
        for rec in self:
            commissions = self.env['commission.sale.sov'].sudo().search([
                ('sale_id', '=', rec.sale_id.id),
                ('commission_member_uid', '!=', False),
                ('state', '=', 'approved'),
                ('sov_id', '=', rec.id),
            ])
            users = commissions.mapped('commission_member_uid')
            rec.sale_commission_user_ids = users

    @api.depends('user_id')  # Adjust the dependencies if needed
    def _compute_is_access_price(self):
        current_user = self.env.user
        for record in self:
            if current_user.has_group('freezoner_custom.proforma_sov_price_group'):
                record.is_access_price = True
            elif record.sale_id.state == 'draft':
                record.is_access_price = True
            else:
                record.is_access_price = False


    @api.depends('qty','unit_price')
    def get_revenue(self):
        for rec in self:
            rec.revenue = rec.qty * rec.unit_price

    @api.depends('qty','unit_cost')
    def get_planned_expenses(self):
        for rec in self:
            rec.planned_expenses = rec.qty * rec.unit_cost

    @api.depends('revenue','planned_expenses')
    def get_profit(self):
        for rec in self:
            rec.profit = rec.revenue - rec.planned_expenses

    @api.depends('profit')
    def get_tax(self):
        for rec in self:
            rec.tax = (rec.profit /1.05) * 0.05



    @api.depends('profit','tax')
    def get_net(self):
        for rec in self:
            rec.net = rec.profit - rec.tax

