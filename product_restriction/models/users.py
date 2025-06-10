
from odoo import api, fields, models, _

class ResUsers(models.Model):
    _inherit = 'res.users'

    restriction_on = fields.Selection([('product', 'Product'),
                                ('category', 'Category'),
                                ], string='Restriction On')

    product_ids = fields.Many2many('product.product', string="Products")
    categories_ids=fields.Many2many('product.category',string="category")


    @api.onchange('restriction_on')
    def _onchange_restriction_on(self):
        if self.restriction_on == 'product':
            self.product_ids=[(6,0,[])]
        elif self.restriction_on == 'category':
            self.categories_ids = [(6,0,[])]

