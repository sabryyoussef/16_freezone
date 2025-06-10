
from odoo import api, fields, models

class Sale(models.Model):
    _inherit = 'sale.order'

    referer_to = fields.Many2one('res.partner', string="Referer To")

    def _prepare_invoice(self, ):
        invoice_vals = super(Sale, self)._prepare_invoice()
        invoice_vals.update({
            'referer_to': self.referer_to.id,
        })
        return invoice_vals


