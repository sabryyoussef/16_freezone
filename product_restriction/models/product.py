from odoo import api, fields, models,_

class Product(models.Model):
    _inherit = "product.product"
    
    user_id = fields.Many2one('res.users','User', default=lambda self: self.env.user)

    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        groups = self.env.user.has_group('product_restriction.group_product_restriction_user')
        current_uid = self._context.get('uid')
        user = self.env['res.users'].browse(current_uid)
        if user.restriction_on == 'product' and groups:
            args += [('id','in',user.product_ids.ids)]
        if user.restriction_on == 'category' and groups:
            args += [('categ_id','in',user.categories_ids.ids)]
        return super(Product, self)._search(args=args)

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        groups = self.env.user.has_group('product_restriction.group_product_restriction_user')
        current_uid = self._context.get('uid')
        user = self.env['res.users'].browse(current_uid)
        product_ids = user.product_ids
        categories_ids = user.categories_ids
        if user.restriction_on == 'product' and groups:
            args += [('id','in',product_ids.ids)]
        if  user.restriction_on == 'category' and groups:
            args = [('categ_id','in',categories_ids.ids)]
        return super(Product, self)._name_search(name=name,args=args,limit=100, name_get_uid=name_get_uid)

class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _search(self, args, **kwargs):
        groups = self.env.user.has_group('product_restriction.group_product_restriction_user')
        current_uid = self._context.get('uid')
        user = self.env['res.users'].browse(current_uid)
        product_list = []
        for product in user.product_ids:
            product_list.append( product.product_tmpl_id.id)
        if user.restriction_on == 'product' and groups:
            args += [('id','in',product_list)]
        if user.restriction_on == 'category' and groups:
            args += [('categ_id','in',user.categories_ids.ids)]
        return super(ProductTemplate, self)._search(args, **kwargs)

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        product_list = []
        groups = self.env.user.has_group('product_restriction.group_product_restriction_user')
        current_uid = self._context.get('uid')
        user = self.env['res.users'].browse(current_uid)
        categories_ids = user.categories_ids
        for product in user.product_ids:
            product_list.append( product.product_tmpl_id.id)
        if user.restriction_on == 'product' and groups:
            args += [('id','in',product_list)]
        if user.restriction_on == 'category' and groups:
            args += [('categ_id','in',categories_ids.ids)]
        return super(ProductTemplate, self)._name_search(name=name, args=args, operator=operator, limit=100, name_get_uid=name_get_uid)
