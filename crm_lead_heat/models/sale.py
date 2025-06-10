from odoo import fields, models
from odoo.exceptions import UserError


class SaleOrder(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def create_invoices(self):
        for rec in self.sale_order_ids:
            if rec.opportunity_id and rec.opportunity_id.lead_heat != 'hot':
                raise UserError('You can\'t invoice an opportunity that is not hot ')
        res = super(SaleOrder, self).create_invoices()
        return res
