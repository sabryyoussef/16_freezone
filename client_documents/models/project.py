# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProjectDocument(models.Model):
    _inherit = 'project.project'

    documents_fulfilment = fields.Boolean(compute='compute_documents_fulfilment')

    def compute_documents_fulfilment(self):
        for rec in self:
            check = False
            for task in rec.task_ids:
                for line1 in task.document_required_type_ids:
                    if len(line1.attachment_ids) > 0:
                        check = True
                        break
                for line2 in task.document_type_ids:
                    if len(line2.attachment_ids) > 0:
                        check = True
                        break
            rec.documents_fulfilment = check


    # @api.depends('documents_fulfilment')
    # def _compute_documents_fulfilment(self):
    #     for rec in self:
    #         if rec.partner_id:
    #             fulfilment = True
    #             required_documents = self.env['product.product'].search([('id', '=', rec.sale_line_id.product_id.id)],
    #                                                                     limit=1).document_required_type_ids
    #             for document_type in required_documents:
    #                 if document_type.is_required and document_type.document_id.id not in rec.partner_id.document_ids.mapped('type_id').ids:
    #                     fulfilment = False
    #                     break
    #             rec.documents_fulfilment = fulfilment
    #         else:
    #             rec.documents_fulfilment = True

    # @api.depends('documents_fulfilment')
    # def _compute_documents_fulfilment(self):
    #     for rec in self:
    #         if rec.partner_id:
    #             fulfilment = True
    #             required_documents = self.env['product.product'].search([('id', '=', rec.sale_line_id.product_id.id)],
    #                                                                     limit=1).document_required_type_ids
    #             for document_type in required_documents:
    #                 if document_type.is_required == True:
    #                     if document_type.document_id.id not in rec.partner_id.document_ids.mapped('type_id').ids:
    #                         fulfilment = False
    #                         break
    #             rec.documents_fulfilment = fulfilment
    #         else:
    #             rec.documents_fulfilment = True
