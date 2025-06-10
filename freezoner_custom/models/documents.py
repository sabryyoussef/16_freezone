
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class DocumentsShare(models.Model):
    _inherit = 'documents.share'

    lead_id = fields.Many2one('crm.lead')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments', required=True)
    number = fields.Char(
        string='Number', required=True, copy=False, readonly=True,
        index=True, default=lambda self: _('New'))

    @api.model
    def create(self, vals):
        vals['number'] = self.env['ir.sequence'].next_by_code('documents.share') or _('New')
        return super(DocumentsShare, self).create(vals)

    def write(self, values):
        res = super(DocumentsShare, self).write(values)
        if not self.env.user.has_group('documents.group_documents_manager'):
            raise ValidationError(_(' You not have access to edit '))
        return res

    #  keep the old records
    # @api.onchange('partner_id')
    # def _onchange_related_partner_documents(self):
    #     for rec in self:
    #         if rec.partner_id:
    #             # Fetch documents linked to the partner
    #             documents = self.env['documents.document'].sudo().search([('partner_id', '=', rec.partner_id.id)])
    #             # Get existing documents to avoid duplicates
    #             existing_docs = rec.document_ids
    #             # Identify new documents not already linked
    #             new_docs = documents - existing_docs
    #             # Add new documents to the existing list
    #             if new_docs:
    #                 rec.document_ids += new_docs

    @api.onchange('partner_id')
    def _onchange_related_partner_documents(self):
        for rec in self:
            if rec.partner_id:
                # Fetch documents linked to the new partner
                new_documents = self.env['documents.document'].sudo().search(
                    [('partner_id', '=', rec.partner_id.id)]
                )
                # Update only if documents are different from current
                if rec.document_ids != new_documents:
                    rec.document_ids = new_documents


    def open_create_activity_popup(self):
        return {
            'res_model': 'files.activity.wizard',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            # 'context': {'default_sub_folder_file_id': self.id},
            'view_id': self.env.ref("cabinet_directory.cabinet_meeting_form_view").id,
            'target': 'new'
        }

    def send_email_activity(self):
        self.ensure_one()  # Ensure it's called on a single record
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_model': self._name,  # The model of the current record
                'default_res_id': self.id,  # The ID of the current record
                'default_subject': self.name,  # Pass subject from the current record
                'default_partner_ids': [self.partner_id.id],  # Pass subject from the current record
                'default_composition_mode': 'comment',
            }
        }

    def action_schedule_meeting(self, smart_calendar=True):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("calendar.action_calendar_event")
        partner_ids = self.env.user.partner_id.ids
        if self.partner_id:
            partner_ids.append(self.partner_id.id)
        current_opportunity_id = self.lead_id.id or False

        # Add the domain to filter events by the document_share_id
        action['domain'] = [('document_share_id', '=', self.id)]

        action['context'] = {
            'search_default_opportunity_id': current_opportunity_id,
            'default_opportunity_id': current_opportunity_id,
            'default_partner_id': self.partner_id.id,
            'default_partner_ids': partner_ids,
            'default_name': self.name,
            'default_document_share_id': self.id,  # Pass the document_share_id to the new event
        }
        # 'Smart' calendar view: get the most relevant time period to display to the user.
        if current_opportunity_id and smart_calendar:
            mode, initial_date = self._get_opportunity_meeting_view_parameters()
            action['context'].update({'default_mode': mode, 'initial_date': initial_date})
        return action


    def _get_share_popup(self, context, vals):
        # Use the FULL form view (not popup)
        view_id = self.env.ref('freezoner_custom.share_view_form_new_popup').id  # Changed from 'share_view_form_popup'
        return {
            'type': 'ir.actions.act_window',
            'name': _('Share selected files') if vals.get('type') == 'ids' else _('Share selected workspace'),
            'res_model': 'documents.share',
            'res_id': self.id if self else False,
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'current',  # Changed from 'new'
            'context': context,
        }

    @api.model
    def open_share_popup(self, vals):
        new_context = dict(self.env.context)
        new_context.update({
            'default_owner_id': self.env.uid,
            'default_folder_id': vals.get('folder_id'),
            'default_tag_ids': vals.get('tag_ids'),
            'default_type': vals.get('type', 'domain'),
            'default_domain': vals.get('domain') if vals.get('type', 'domain') == 'domain' else False,
            'default_document_ids': vals.get('document_ids', False),
        })
        return self.create(vals)._get_share_popup(new_context, vals)


class Documents(models.Model):
    _inherit = 'documents.document'

    project_id = fields.Many2one('project.project')
    required_project_id = fields.Many2one('project.project')
    deliverable_project_id = fields.Many2one('project.project')
    issue_date = fields.Date(required=1, tracking=True)
    type_id = fields.Many2one(comodel_name='res.partner.document.type', tracking=True)
    expiration_date = fields.Date(tracking=True)
    partner_ids = fields.Many2many("res.partner", relation="project_partner_id1",
                                   column1="project_partner_id2", column2="project_partner_id3",
                                   string="Partners",
                                   compute='get_project_partners' )
    partner_id = fields.Many2one('res.partner')

    @api.depends('project_id', 'required_project_id', 'deliverable_project_id')
    def get_project_partners(self):
        for rec in self:
            project = rec.project_id or rec.required_project_id or rec.deliverable_project_id
            if project:
                partners = project.compliance_shareholder_ids.mapped('contact_id.id')
                project_partner_id = project.partner_id.id if project.partner_id else False
                hand_partner_id = project.hand_partner_id.id if project.hand_partner_id else False
                partner_list = [pid for pid in [project_partner_id, hand_partner_id] if pid] + partners
                rec.partner_ids = [(6, 0, partner_list)]
            else:
                rec.partner_ids = [(6, 0, self.env['res.partner'].search([]).ids)]

