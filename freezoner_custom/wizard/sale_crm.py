
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SaleCrmWizard(models.TransientModel):
    _name = 'sale.crm.wizard'

    sale_id = fields.Many2one("sale.order",string="Sale")
    payment_type = fields.Selection(string="Payment Type",
                                    selection=[('fully', 'Fully Paid'), ('partial', 'Partial Paid'), ],
                                    default='fully',required=True, )

    def submit(self):
        for rec in self:
            partial_stage = self.env['crm.stage'].sudo().search([('name','=','Partial Payment Collected')],limit=1)
            fully_stage = self.env['crm.stage'].sudo().search([('name','=','Full Payment')],limit=1)
            if rec.payment_type == 'fully':
                rec.sale_id.sudo().opportunity_id.stage_id = fully_stage.id
            if rec.payment_type == 'partial':
                rec.sale_id.sudo().opportunity_id.stage_id = partial_stage.id
            rec.sale_id.sudo().action_confirm()


