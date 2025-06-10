
from odoo import api, fields, models,_

class Commission(models.Model):
    _name = 'partner.commission'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Number', required=True, copy=False, readonly=True,
        index=True, default=lambda self: _('New'), track_visibility='onchange')
    partner_id = fields.Many2one('res.partner')
    amount = fields.Float("Amount")
    invoice_id = fields.Many2one('account.move')
    notes = fields.Text("Notes")
    state = fields.Selection([('draft', 'Draft'), ('approved', 'Approved'), ('cancel', 'Cancel')], default='draft',
                             string='State', tracking=True)
    move_ids = fields.One2many('account.move', 'commission_id')
    company_id = fields.Many2one('res.company',default=lambda self: self.env.company, readonly=True)


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

    @api.model 
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('partner.commission') or _('New')
        return super(Commission, self).create(vals)

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def action_approve(self):
        for rec in self:
            if rec.company_id.product_id and rec.company_id.journal_id:
                invoice_line_list = []
                vals = (0, 0, {
                    'name': rec.name,
                    'product_id': rec.company_id.product_id.id,
                    'price_unit': rec.amount,
                    'account_id':  rec.company_id.product_id.property_account_income_id.id
                                  or rec.product_id.categ_id.property_account_income_categ_id.id,
                    'tax_ids': False,
                    'quantity': 1,
                })
                invoice_line_list.append(vals)
                self.env['account.move'].create({
                    'move_type': 'in_invoice',
                    'invoice_origin': rec.name,
                    'invoice_user_id': self.env.user.id,
                    'narration': rec.name,
                    'partner_id': rec.partner_id.id,
                    'currency_id': self.company_id.currency_id.id,
                    'journal_id': rec.company_id.journal_id.id,
                    'payment_reference': rec.name,
                    'commission_id': rec.id,
                    'invoice_line_ids': invoice_line_list,
                })




