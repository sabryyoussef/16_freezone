
from odoo import api, fields, models

class Sale(models.Model):
    _inherit = 'sale.order'

    approval_rquest_ids = fields.One2many('approval.request', 'sale_id', string="Approval Requests")

    def action_approve_sale(self):
        for rec in self:
            # Search for the approval category only once and use sudo if needed
            category = self.env['approval.category'].search([('is_sale', '=', True)], limit=1)

            if category:
                # Prepare product lines using list comprehension for efficiency
                lines = [{
                    'product_id': line.product_id.id,
                    'description': line.name,
                } for line in rec.order_line]

                # Create new approval category record using sale order data
                self.env['approval.request'].create({
                    'name': f'Sale - {rec.name}',  # Using f-string for better readability
                    'sale_id': rec.id,  # Directly using the sale order reference
                    'category_id': category.id,  # Directly using the sale order reference
                    'date': rec.date_order,  # Directly using the sale order reference
                    'reference': rec.name,  # Directly using the sale order reference
                    'amount': rec.amount_total,  # Using the total amount
                    'request_owner_id': self.env.user.id,  # Partner ID from the sale order
                    'partner_id': rec.partner_id.id,  # Partner ID from the sale order
                    'request_status': 'new',  # Default status for new requests
                    'product_line_ids': [(0, 0, line) for line in lines],  # Correct way to handle One2many fields
                })

    def action_view_approvals(self):
        """ Smart button to run action """
        recs = self.mapped('approval_rquest_ids')
        action = self.env.ref('approvals.approval_request_action').read()[0]
        if len(recs) > 1:
            action['domain'] = [('id', 'in', recs.ids)]
        elif len(recs) == 1:
            action['views'] = [(
                self.env.ref('approvals.approval_request_view_form').id, 'form'
            )]
            action['res_id'] = recs.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action





