from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError

class SalesWizard(models.TransientModel):
    _name = "res.partner.document.merge"
    _description = 'Merge Document Wizard'

    item_ids = fields.One2many('res.partner.document.merge.items', 'wizard_id')

    @api.model
    def _prepare_item_lines(self, line):
        return {
            'type_id': line.type_id.id,
            'partner_id': line.partner_id.id,
            'issue_date': line.issue_date,
            'attachment_ids': [(6, 0, line.attachment_ids.ids)],
            'name': line.name,
        }

    @api.model
    def default_get(self, fields_list):
        res = super(SalesWizard, self).default_get(fields_list)
        request_line_obj = self.env['res.partner.document']
        request_line_ids = self.env.context.get('active_ids', False)
        active_model = self.env.context.get('active_model', False)
        if not request_line_ids:
            return res
        assert active_model == 'res.partner.document', 'Bad context propagation'
        items = []
        request_lines = request_line_obj.browse(request_line_ids)
        for line in request_lines:
            items.append([0, 0, self._prepare_item_lines(line)])
        res['item_ids'] = items
        return res

    def action_merge(self):
        selected_lines = self.env['res.partner.document'].with_context(bypass_duplicate_check=True).browse(
            self.env.context.get('active_ids', []))

        if not selected_lines:
            raise UserError(_("No records selected for merging."))

        # Validate that all selected lines have the same issue_date, type_id, and partner_id
        issue_dates = selected_lines.mapped('issue_date')
        type_ids = selected_lines.mapped('type_id.id')
        partner_ids = selected_lines.mapped('partner_id.id')

        if len(set(issue_dates)) > 1 or len(set(type_ids)) > 1 or len(set(partner_ids)) > 1:
            raise UserError(_("All selected records must have the same Issue Date, Type, and Partner."))

        # Get unique names
        unique_names = list(set(selected_lines.mapped('name')))
        # Get unique document IDs

        attachments_by_name = {}
        for line in selected_lines:
            for attachment in line.attachment_ids:
                if attachment.name not in attachments_by_name:
                    attachments_by_name[attachment.name] = attachment.id

        # Get unique document IDs based on unique attachment names
        unique_attachment_ids = list(attachments_by_name.values())
        all_task_ids = list(set(selected_lines.mapped('task_id.id')))
        # Choose one record to keep
        main_record = selected_lines[0]
        # Update the main record with the merged data
        main_record.write({
            'name': ', '.join(unique_names),
            'type_id': main_record.type_id.id,
            'partner_id': main_record.partner_id.id,
            'issue_date': main_record.issue_date,
            'expiration_reminder': main_record.expiration_reminder,
            'is_verify': main_record.is_verify,
            'expiration_reminder_sent': main_record.expiration_reminder_sent,
            'task_id': main_record.task_id.id,
            'task_ids': [(6, 0, all_task_ids)],
            'attachment_ids': [(6, 0, unique_attachment_ids)]
        })

        # Unlink the other records
        (selected_lines - main_record).unlink()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Merged Documents'),
            'res_model': 'res.partner.document',
            'res_id': main_record.id,
            'view_mode': 'form',
            'view_type': 'form',
            'context': self.env.context,
        }




class WizardItems(models.TransientModel):
    _name = "res.partner.document.merge.items"
    _description = "res.partner.document Items"

    wizard_id = fields.Many2one('res.partner.document.merge')
    type_id = fields.Many2one('res.partner.document.type')
    partner_id = fields.Many2one('res.partner')
    issue_date = fields.Date(string='Issue Date')
    attachment_ids = fields.Many2many('ir.attachment', string='Document', required=True, )
    name = fields.Char()
