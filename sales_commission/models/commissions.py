# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from collections import Counter
from dateutil.relativedelta import relativedelta
from datetime import datetime
from dateutil.relativedelta import relativedelta

class Commission(models.Model):
    _name = 'crm.commission'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'



    @api.onchange('member_id')
    def _get_default_manager(self):
        for rec in self:
            rec.manager_id =  rec.member_id.employee_id.parent_id.id

    @api.onchange('member_id')
    def _get_manager_team_ids(self):
        for rec in self:
            user_group = self.env.ref("account.group_account_manager")
            users = [usr.id for usr in user_group.users]
            rec.finance_team_ids =  users

    @api.model
    def _get_default_team(self):
        user = self.env.user
        teams = self.env['crm.team'].search([])
        line = 0
        for team in teams:
            if user.id in team.member_ids.ids:
                line = team.id
        return line

    @api.model
    def _get_default_target(self):
        return self.env['crm.team.member'].search([('user_id', '=', self.member_id.id)],
                                                                   limit=1).target_amount


    member_id = fields.Many2one(comodel_name='res.users', required=True, default=lambda self: self.env.user)
    team_id = fields.Many2one(comodel_name='crm.team', required=True, default=_get_default_team)
    team_name = fields.Char(related='team_id.name')
    target = fields.Float(default=_get_default_target)
    net_achievement = fields.Float(compute='get_sov_net_achievement')
    planned_expenses = fields.Float(compute='get_sov_planned_expenses')
    revenue = fields.Float(compute='compute_sov_revenue')
    sov_revenue = fields.Float(compute='get_sov_revenue')
    target_percentage = fields.Float(string='Target', compute="_compute_target_percentage", store=True)
    years = fields.Selection([
        ('2023', '2023'), ('2024', '2024'), ('2025', '2025'),
        ('2026', '2026'), ('2027', '2027'), ('2028', '2028'),
        ('2029', '2029'), ('2030', '2030'),
    ], string='Year', default=lambda self: str(datetime.now().year), required=True) #
    months = fields.Selection([
        ('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
        ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'),
        ('09', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'),
    ], string='Month', default=lambda self: datetime.now().strftime('%m'), required=True)
    achieving_date = fields.Date(default=fields.Date.context_today, helps='Get the data in lines based the month that selected in this field')
    display_name = fields.Char(compute="_compute_display_name")
    type_commission = fields.Selection(selection=[('member', 'Member'), ('team', 'Team')], default='member', required=True)
    commission_perc = fields.Float('Commission Perc % ')
    net = fields.Float('Achievement Net minus Variable Deductions', compute='get_net')
    deductions = fields.Float('Deductions')
    sov_ids = fields.One2many('commission.sale.sov','commission_id')
    license = fields.Float(string='Cross/Up Sell License', compute='get_commission_attribute')
    license2 = fields.Float(compute='get_value_perc')
    value = fields.Float(string='Cross/Up Sell Value Added Service', compute='get_commission_attribute')
    value2 = fields.Float(compute='get_value_perc')
    renewals = fields.Float(string='Renewals', compute='get_commission_attribute')
    renewals2 = fields.Float(compute='get_value_perc')
    network = fields.Float(string='Personal Network', compute='get_commission_attribute')
    network2 = fields.Float(compute='get_value_perc')
    annual = fields.Float(string='Annual Contract', compute='get_commission_attribute')
    annual2 = fields.Float(compute='get_value_perc')
    bank = fields.Float(string='Banking Deals', compute='get_commission_attribute')
    bank2 = fields.Float(compute='get_value_perc')
    accounting = fields.Float(string='Accounting Deals', compute='get_commission_attribute')
    accounting2 = fields.Float(compute='get_value_perc')
    misc = fields.Float(string='Miscellaneous Deals', compute='get_commission_attribute')
    misc2 = fields.Float(compute='get_value_perc')
    misc_perc = fields.Float()
    state = fields.Selection(string="Status", selection=[('draft', 'Draft'),('submitted', 'Submitted'), ('approved', 'Approved'), ('posted', 'Posted'), ], default='draft', tracking=True )
    move_ids = fields.One2many('account.move', 'commission_id')
    journal_id = fields.Many2one('account.journal',  domain=[('type', 'in', ['bank', 'cash'])])
    manager_id = fields.Many2one('hr.employee',readonly=False)
    finance_team_ids = fields.Many2many('res.users',readonly=False, string='Finance Team')
    total_profit = fields.Float(string='Total',compute='get_total_profit')
    total = fields.Float(string='Total',compute='get_total')

    @api.depends('license','value','renewals','network','annual','bank','accounting','misc')
    def get_total(self):
        for rec in self:
            rec.total = rec.license + rec.value + rec.renewals + rec.network + rec.annual + rec.bank + rec.accounting + rec.misc

    @api.depends('license2','value2','renewals2','network2','annual2','bank2','accounting2','misc2')
    def get_total_profit(self):
        for rec in self:
            rec.total_profit = rec.license2 + rec.value2 + rec.renewals2 + rec.network2 + rec.annual2 + rec.bank2 + rec.accounting2 + rec.misc2

    @api.depends('sov_ids.commission_attribute')
    def get_commission_attribute(self):
        for rec in self:
            rec.license = sum(line.net for line in rec.sov_ids if line.commission_attribute == 'license')
            rec.value = sum(line.net for line in rec.sov_ids if line.commission_attribute == 'value')
            rec.renewals = sum(line.net for line in rec.sov_ids if line.commission_attribute == 'renewals')
            rec.network = sum(line.net for line in rec.sov_ids if line.commission_attribute == 'network')
            rec.annual = sum(line.net for line in rec.sov_ids if line.commission_attribute == 'annual')
            rec.bank = sum(line.net for line in rec.sov_ids if line.commission_attribute == 'bank')
            rec.accounting = sum(line.net for line in rec.sov_ids if line.commission_attribute == 'accounting')
            rec.misc = sum(line.net for line in rec.sov_ids if line.commission_attribute == 'misc')

    @api.depends('license','value','renewals','network','annual','bank','accounting','misc','misc_perc')
    def get_value_perc(self):
        for rec in self:
            rec.license2 = (rec.license * 6) / 100
            rec.value2 = (rec.value * 5) / 100
            rec.renewals2 = (rec.renewals * 3) / 100
            rec.network2 = (rec.network * 7) / 100
            rec.annual2 = (rec.annual * 20) / 100
            rec.bank2 = (rec.bank * 10) / 100
            rec.accounting2 = (rec.accounting * 7.5) / 100
            rec.misc2 = (rec.misc * rec.misc_perc) / 100

    @api.depends('sov_ids', 'sov_ids.revenue')
    def get_sov_revenue(self):
        for rec in self:
            rec.sov_revenue = sum(line.revenue for line in rec.sov_ids)

    @api.depends('sov_ids', 'sov_ids.net')
    def get_sov_net_achievement(self):
        for rec in self:
            rec.net_achievement = sum(line.net for line in rec.sov_ids)

    @api.depends('sov_ids', 'sov_ids.planned_expenses')
    def get_sov_planned_expenses(self):
        for rec in self:
            rec.planned_expenses = sum(line.planned_expenses for line in rec.sov_ids)

    @api.depends('sov_ids', 'sov_ids.revenue')
    def compute_sov_revenue(self):
        for rec in self:
            rec.revenue = sum(line.revenue for line in rec.sov_ids)

    def action_submit(self):
        for rec in self:
            if not rec.manager_id:
                raise ValidationError(" PLease select the manager ")
            if rec.manager_id:
                data = {
                    'res_model_id': self.env['ir.model'].sudo().search([('model', '=', 'crm.commission')]).id,
                    'res_id': self.id,
                    'activity_type_id': self.env['mail.activity.type'].sudo().search(
                        [('name', 'like', 'Inbox')]).id,
                    'summary': _(' Commission Submitted : ' + rec.member_id.name + " -->  " + rec.manager_id.name),
                    'date_deadline': fields.Date.today(),
                    'user_id': rec.manager_id.user_id.id
                }
                self.env['mail.activity'].sudo().create(data)
            rec.state = 'submitted'

    def action_approve(self):
        for rec in self:
            if rec.finance_team_ids:
                for usr in rec.finance_team_ids:
                    data = {
                        'res_model_id': self.env['ir.model'].sudo().search([('model', '=', 'crm.commission')]).id,
                        'res_id': self.id,
                        'activity_type_id': self.env['mail.activity.type'].sudo().search(
                            [('name', 'like', 'Inbox')]).id,
                        'summary': _(' Commission Approved : ' + rec.member_id.name + " -->  " + usr.name),
                        'date_deadline': fields.Date.today(),
                        'user_id': usr.id
                    }
                    self.env['mail.activity'].sudo().create(data)
            rec.state = 'approved'

    def action_view_entry(self):
        """ Smart button to run action """
        recs = self.mapped('move_ids')
        action = self.env.ref('account.action_move_journal_line').read()[0]
        if len(recs) > 1:
            action['domain'] = [('id', 'in', recs.ids)]
        elif len(recs) == 1:
            action['views'] = [(
                self.env.ref('account.view_move_form').id, 'form'
            )]
            action['res_id'] = recs.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def action_draft(self):
        for rec in self:
            if rec.move_ids:
                for move in rec.move_ids:
                    move.button_draft()
                    move.unlink()
            rec.state = 'draft'

    def action_posted(self):
        for rec in self:
            if not rec.journal_id:
                raise ValidationError('Please add journal')
            lines = []
            debit = {
                'debit': rec.net,
                'credit': 0.0,
                'account_id': rec.member_id.partner_id.property_account_payable_id.id,
                'tax_line_id': False,
                'name': str('Commission'),
                'partner_id': rec.member_id.partner_id.id or False,
            }
            lines.append(debit)
            credit = {
                'debit': 0.0,
                'credit': rec.net,
                'account_id': rec.journal_id.default_account_id.id,
                'partner_id': rec.member_id.partner_id.id or False,
                'tax_ids': False,
                'name': str('Commission'),
            }
            lines.append(credit)
            vals = {
                'partner_id': rec.member_id.partner_id.id or False,
                'journal_id': rec.journal_id.id,
                'date': fields.Date.today(),
                'state': 'draft',
                'commission_id': rec.id,
                'ref': 'Commission',
                'line_ids': [(0, 0, line) for line in lines]
            }
            move = self.env['account.move'].sudo().create(vals)
            if move:
                for entry in move:
                    entry.action_post()
            rec.state = 'posted'

    @api.constrains('sov_ids')
    def check_sov_ids(self):
        for rec in self:
            count = Counter(line.sov_id.id for line in rec.sov_ids)
            duplicate_ids = [id for id, cnt in count.items() if cnt > 1]
            if duplicate_ids:
                raise ValidationError('Duplicate SOV  lines')

    @api.onchange('member_id','months','years','achieving_date','type_commission')
    def action_calculate(self):
        if self.type_commission == 'member':
            self.prepare_member_lines()
        if self.type_commission == 'team':
            self.prepare_team_lines()

    def prepare_member_lines(self):
        sov_lines = []
        self.sov_ids = None
        for rec in self:
            if rec.member_id and rec.years and rec.months:
                date_from = datetime(int(rec.years), int(rec.months), 1)
                date_to = date_from + relativedelta(months=1)
                date_from_str = date_from.strftime('%Y-%m-%d')
                date_to_str = date_to.strftime('%Y-%m-%d')
                sov = self.env['sale.sov'].sudo().search([('sale_id.state','=', 'sale'),('sale_id.user_id','=', rec.member_id.id),
                                                          ('sale_id.date_confirmed', '>=', date_from_str),
                                                          ('sale_id.date_confirmed', '<', date_to_str)
                                                           ])
                if sov:
                    for line in sov:
                        sov_lines.append(
                            (0, 0, {
                                'sale_id': line.sale_id.id,
                                'sov_id': line.id,
                                'name': line.name,
                                'revenue': line.revenue,
                                'planned_expenses': line.planned_expenses,
                                'profit': line.profit,
                                'tax': line.tax,
                                'net': line.net,
                                'commission_attribute': line.commission_attribute,
                            }))
                self.write({'sov_ids': sov_lines})

    def prepare_team_lines(self):
        sov_lines = []
        self.sov_ids = None
        for rec in self:
            if rec.member_id and rec.years and rec.months:
                date_from = datetime(int(rec.years), int(rec.months), 1)
                date_to = date_from + relativedelta(months=1)
                date_from_str = date_from.strftime('%Y-%m-%d')
                date_to_str = date_to.strftime('%Y-%m-%d')
                sov = self.env['sale.sov'].sudo().search([('sale_id.state','=', 'sale'),('sale_id.user_id','in', rec.team_id.member_ids.ids),
                                                          ('sale_id.date_confirmed', '>=', date_from_str),
                                                          ('sale_id.date_confirmed', '<', date_to_str)
                                                           ])
                if sov:
                    for line in sov:
                        sov_lines.append(
                            (0, 0, {
                                'sale_id': line.sale_id.id,
                                'sov_id': line.id,
                                'name': line.name,
                                'revenue': line.revenue,
                                'planned_expenses': line.planned_expenses,
                                'profit': line.profit,
                                'tax': line.tax,
                                'net': line.net,
                                'commission_attribute': line.commission_attribute,
                            }))
                self.write({'sov_ids': sov_lines})

    def write(self, vals):
        if self.state == 'submitted' and 'state' not in vals and not self.env.user.has_group('sales_commission.commission_admin'):
            raise ValidationError(" You not have access to edit ")
        return super(Commission, self).write(vals)

    @api.depends('net_achievement', 'commission_perc','deductions')
    def get_net(self):
        for rec in self:
            rec.net = (rec.net_achievement - rec.deductions)  * (rec.commission_perc / 100) if rec.commission_perc else 0.0

    @api.depends('target', 'net_achievement')
    def _compute_target_percentage(self):
        for rec in self:
            try:
                rec.target_percentage = (rec.net_achievement / rec.target) * 100
            except:
                rec.target_percentage = 0.0

    @api.onchange('member_id', 'type')
    def _on_change_member_id(self):
        for rec in self:
            # Basic Values
            try:
                rec.target, rec.planned_expenses, rec.net_achievement = 0, 0, 0,
                date_from = datetime(int(rec.years), int(rec.months), 1)
                date_to = date_from + relativedelta(months=1)
                month_begin = date_from.strftime('%Y-%m-%d')
                month_end = date_to.strftime('%Y-%m-%d')
                member_id = rec.member_id
                team_target = self.env['crm.team'].search([('id', '=', rec.team_id.id)]).invoiced_target
                member_target = self.env['crm.team.member'].search([('user_id', '=', member_id.id)],
                                                                   limit=1).target_amount
                team_achievement_sales = self.env['sale.order'].search(
                    [('team_id', '=', rec.team_id.id), ('invoice_status', '=', 'invoiced'),
                     ('date_confirmed', '>=', month_begin), ('date_confirmed', '<=', month_end)])
                member_achievement = self.env['sale.order'].search([('user_id', '=', rec.member_id.id),
                                                                    ('invoice_status', '=', 'invoiced'),
                                                                    ('date_confirmed', '>=', month_begin),
                                                                    ('date_confirmed', '<=', month_end)])
                achievement_objs = team_achievement_sales if rec.type_commission == "team" else member_achievement
                total_achievement = 0.0
                for sale in achievement_objs:
                    sale_sale = 0.0
                    sale_purchase_planned = 0.0
                    if sale.analytic_account_id:
                        sale_sale = sale_sale = + sale.amount_total
                        for line in sale.analytic_account_id.crossovered_budget_line:
                            sale_purchase_planned = sale_purchase_planned = - line.planned_amount

                    rec.planned_expenses = sale_purchase_planned
                    total_achievement = sale_sale - sale_purchase_planned
                    rec.net_achievement = total_achievement
                target = member_target if rec.type_commission == "member" else team_target

                # Value Assignation
                rec.target = target
                rec.net_achievement = total_achievement
            except Exception as e:
                print(e)

    @api.depends('display_name')
    def _compute_display_name(self):
        for rec in self:
            name = rec.team_id.name if rec.type_commission == "team" else rec.member_id.name
            rec.display_name = f"{name} - {rec.achieving_date} - ({rec.type_commission})"

    def _cron_sales_commission(self):
        teams = self.env['crm.team'].search([('user_id', '!=', False)])
        for team in teams:
            vals = {
                'member_id': team.user_id.id,
                'team_id': team.id,
                'type': 'Team',
                'achieving_date': datetime.date.today(),
            }
            team_commission = self.create(vals)
            team_commission._on_change_member_id()
        members = self.env['crm.team.member'].search([('target_amount', '!=', 0)])
        for member in members:
            vals = {
                'member_id': member.user_id.id,
                'team_id': member.crm_team_id.id,
                'type_commission': 'member',
                'achieving_date': datetime.date.today(),
            }
            member_commission = self.create(vals)
            member_commission._on_change_member_id()
