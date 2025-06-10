from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ClientDocumentsCategory(models.Model):
    _name = 'res.partner.document.category'
    _description = 'Client Document Category'
    _rec_name = 'name'

    name = fields.Char()
    document_ids = fields.One2many(comodel_name='res.partner.document', inverse_name='category_id')


class ClientDocumentsType(models.Model):
    _name = 'res.partner.document.type'
    _description = 'Client Document Type'

    name = fields.Char()
    category_id = fields.Many2one(comodel_name='res.partner.document.category')
    document_ids = fields.One2many(comodel_name='res.partner.document', inverse_name='type_id')
    main_document_ids = fields.Many2many('documents.document', compute='_compute_main_document_ids')

    def _compute_main_document_ids(self):
        for rec in self:
            lst = []
            documents = self.env['documents.document'].search([('type_id', '=', rec.id)])
            for doc in documents:
                lst.append(doc.id)
            rec.main_document_ids = lst


class ClientDocuments(models.Model):
    _name = 'res.partner.document'
    _description = 'Client Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=1, tracking=True)
    number = fields.Char(
        string='Number', required=True, copy=False, readonly=True,
        index=True, default=lambda self: _('New'), track_visibility='onchange')
    attachment_ids = fields.Many2many('ir.attachment', string='Document', required=True, tracking=True)
    issue_date = fields.Date(required=1,tracking=True)
    type_id = fields.Many2one(comodel_name='res.partner.document.type',tracking=True)
    expiration_date = fields.Date(tracking=True)

    category_id = fields.Many2one(comodel_name='res.partner.document.category', related='type_id.category_id')
    partner_id = fields.Many2one(comodel_name='res.partner', required=1,tracking=True)
    expiration_reminder = fields.Boolean(default=False,tracking=True)
    document = fields.Char(tracking=True)
    expiration_reminder_sent = fields.Boolean(default=False,tracking=True)
    is_verify = fields.Boolean('Is Verify',tracking=True)
    document_create_date = fields.Datetime(readonly=True, string='Document Create Date',  default=fields.datetime.now(),tracking=True)

    def action_numbers(self):
        docs = self.env['res.partner.document'].sudo().search([])
        for doc in docs:
            doc.number = self.env['ir.sequence'].next_by_code('res.partner.document') or _('New')

    @api.model
    def create(self, vals):
        vals['number'] = self.env['ir.sequence'].next_by_code('res.partner.document') or _('New')
        return super(ClientDocuments, self).create(vals)

    @api.constrains('partner_id', 'issue_date', 'type_id')
    def check_duplicate_document(self):
        if self.env.context.get('bypass_duplicate_check'):
            return
        for rec in self:
            duplicate_document = self.search(
                [('partner_id', '=', rec.partner_id.id), ('issue_date', '=', rec.issue_date),
                 ('type_id', '=', rec.type_id.id), ('id', '!=', rec.id)]
            )
            if duplicate_document:
                raise ValidationError("This document already exists!")

    def write(self, vals):
        res = super(ClientDocuments, self).write(vals)
        if vals.get('expiration_date'):
            self.write({'expiration_reminder_sent': False})
        if vals.get('attachment_ids'):
            self.write({'document_create_date': fields.Datetime.today()})
        return res


class Client(models.Model):
    _inherit = 'res.partner'

    document_ids = fields.One2many(comodel_name='res.partner.document', inverse_name='partner_id')
    documents_count = fields.Integer(compute='_compute_total_documents')

    @api.depends('document_ids')
    def _compute_total_documents(self):
        for rec in self:
            rec.documents_count = len(rec.document_ids.ids)

    def action_view_documents(self):
        action = {
            'type': 'ir.actions.act_window',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
            'view_mode': 'tree,kanban,form',
            'name': f'{self.name}\'s Documents',
            # 'view_ids': [(kanban_view, 'kanban'), (tree_view, 'tree'), (False, 'form')],
            'res_model': 'res.partner.document',
        }
        return action

    def action_see_documents(self):
        self.ensure_one()
        return {
            'name': _('Documents'),
            'domain': [('partner_id', '=', self.id)],
            'res_model': 'documents.document',
            'type': 'ir.actions.act_window',
            'views': [(False, 'kanban')],
            'view_mode': 'kanban',
            'context': {
                "default_partner_id": self.id,
                "searchpanel_default_folder_id": True
            },
        }
