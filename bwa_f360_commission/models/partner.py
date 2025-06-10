
from odoo import api, fields, models

class Partner(models.Model):
    _inherit = 'res.partner'

    commission_ids = fields.One2many('partner.commission','partner_id')

    def action_view_commissions(self):
        """ Smart button to run action """
        recs = self.mapped('commission_ids')
        action = self.env.ref('bwa_f360_commission.partner_commission_action').read()[0]
        if len(recs) > 1:
            action['domain'] = [('id', 'in', recs.ids)]
        elif len(recs) == 1:
            action['views'] = [(
                self.env.ref('bwa_f360_commission.partner_commission_form').id, 'form'
            )]
            action['res_id'] = recs.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
