from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class SalesWizard(models.TransientModel):
    _name = "res.partner.document.type.merge"
    _description = 'Merge Wizard'

    item_ids = fields.One2many('res.partner.document.type.merge.items', 'wizard_id')

    @api.model
    def _prepare_item_lines(self, line):
        return {
            'category_id': line.category_id.id,
            'name': line.name,
        }

    @api.model
    def default_get(self, fields_list):
        res = super(SalesWizard, self).default_get(fields_list)
        request_line_obj = self.env['res.partner.document.type']
        request_line_ids = self.env.context.get('active_ids', False)
        active_model = self.env.context.get('active_model', False)
        if not request_line_ids:
            return res
        assert active_model == 'res.partner.document.type', 'Bad context propagation'
        items = []
        request_lines = request_line_obj.browse(request_line_ids)
        for line in request_lines:
            items.append([0, 0, self._prepare_item_lines(line)])
        res['item_ids'] = items
        return res

    def action_merge(self):
        selected_lines = self.env['res.partner.document.type'].browse(self.env.context.get('active_ids', []))

        if not selected_lines:
            raise UserError(_("No records selected for merging."))

        # Ensure all selected records have the same category_id
        category_ids = selected_lines.mapped('category_id')
        if len(category_ids) > 1:
            raise UserError(_("Selected records must have the same Category."))

        # Get unique names
        unique_names = list(set(selected_lines.mapped('name')))
        # Get unique document IDs
        document_ids = list(set(selected_lines.mapped('document_ids.id')))

        # Choose one record to keep
        main_record = selected_lines[0]

        # Update the main record with the merged data
        main_record.write({
            'name': ', '.join(unique_names),
            'document_ids': [(6, 0, document_ids)]
        })

        # Unlink the other records
        (selected_lines - main_record).unlink()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Merged Document Type'),
            'res_model': 'res.partner.document.type',
            'res_id': main_record.id,
            'view_mode': 'form',
            'view_type': 'form',
            'context': self.env.context,
        }


class WizardItems(models.TransientModel):
    _name = "res.partner.document.type.merge.items"
    _description = "res.partner.document.type Items"

    wizard_id = fields.Many2one('res.partner.document.type.merge')
    category_id = fields.Many2one('res.partner.document.category')
    name = fields.Char()
