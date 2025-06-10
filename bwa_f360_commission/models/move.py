
from odoo import api, fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'

    commission_id = fields.Many2one('partner.commission', string="Commission")
    referer_to = fields.Many2one('res.partner', string="Referer To")
    commission_amount = fields.Float("Commission Amount", compute='get_commission_amount')

    @api.depends('referer_to')
    def get_commission_amount(self):
        for rec in self:
            tot = 0
            perc = rec.company_id.commission_perc
            if rec.referer_to:
                for line in rec.invoice_line_ids:
                    tot += line.product_id.profit_margin * line.quantity
            rec.commission_amount = tot * perc/100

    def create_commission(self):
        for rec in self:
            self.env['partner.commission'].create({
                'invoice_id': rec.id,
                'partner_id': rec.referer_to.id,
                'amount': rec.commission_amount
            })


