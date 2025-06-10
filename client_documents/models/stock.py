# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ServiceDocument(models.Model):
    _inherit = 'product.template'

    document_ids = fields.Many2many(
        comodel_name='res.partner.document.type',
        relation="product_template_document_1_rel",
        column1='product_template_id',
        column2='document_type_id',
        string='Service Documents'
    )
    required_template_ids = fields.Many2many(
        comodel_name='res.partner.document.type',
        relation='product_template_document_2_rel',
        column1='document_type_id',
        column2='product_template_id',
        string='Mandatory Documents',
    )


class ProductProductDocuments(models.Model):
    _inherit = 'product.product'

    document_ids = fields.Many2many(
        comodel_name='res.partner.document.type',
        relation="product_template_document_1_rel",
        column1='product_template_id',
        column2='document_type_id',
        string='Service Documents',
        related='product_tmpl_id.document_ids'
    )
    required_template_ids = fields.Many2many(
        comodel_name='res.partner.document.type',
        relation='product_template_document_2_rel',
        column1='document_type_id',
        column2='product_template_id',
        string='Mandatory Documents',
        related='product_tmpl_id.required_template_ids'
    )
