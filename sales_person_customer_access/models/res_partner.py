
from odoo import models, fields, api,_
from odoo.exceptions import Warning, UserError

class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        restricted_customer = self.env.user.has_group('sales_person_customer_access.group_restricted_customer')
        if restricted_customer:
            args = [('user_id','=',self.env.user.id)] + list(args)
        return super(ResPartner, self)._search(args, offset, limit, order, count, access_rights_uid)

    @api.model_create_multi
    def create(self, vals):
        if not self.env.user.has_group('sales_person_customer_access.group_create_customer'):
            raise UserError(_("You can't create contact , you not have access."))
        res = super(ResPartner, self).create(vals)
        return res


