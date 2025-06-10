
from odoo import api, fields, models

class ProductTemplateDocuments(models.Model):
    _name = 'product.template.documents'

    product_tmpl_id = fields.Many2one('product.template')
    document_id = fields.Many2one('res.partner.document.type', required=True)
    is_required = fields.Boolean('Check Required')

class ProductTemplateRequiredDocuments(models.Model):
    _name = 'product.template.required.documents'

    product_tmpl_id = fields.Many2one('product.template')
    document_id = fields.Many2one('res.partner.document.type', required=True)
    is_required = fields.Boolean('Check Required')

class PartnerFields(models.Model):
    _name = 'product.res.partner.fields'

    product_tmpl_id = fields.Many2one('product.template')
    field_id = fields.Many2one('ir.model.fields', domain="[('model','=', 'res.partner')]")
    is_required = fields.Boolean('Check Required')

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    partner_field_ids = fields.One2many("product.res.partner.fields",'product_tmpl_id')
    document_type_ids = fields.One2many(comodel_name="product.template.documents",inverse_name="product_tmpl_id")
    document_required_type_ids = fields.One2many(comodel_name="product.template.required.documents",inverse_name="product_tmpl_id")
    task_ids = fields.Many2many('project.task', string='Tasks', domain="[('project_id.state','=','a_template')]")
    is_service_commission = fields.Boolean()
    stripe_visa = fields.Boolean()
    service_tracking = fields.Selection(
            selection_add=[("new_workflow", "New Workflow")], ondelete={"new_workflow": "set default"}
    )

class Product(models.Model):
    _inherit = 'product.product'

    is_service_commission = fields.Boolean(related='product_tmpl_id.is_service_commission', store=True)

