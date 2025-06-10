
from odoo import api, fields, models, _


class DocumentsShareWizard(models.TransientModel):
    _inherit = 'files.activity.wizard'

    document_share_id = fields.Many2one('documents.share', string='Documents Share')

    @api.model
    def default_get(self, fields):
        res = super(DocumentsShareWizard, self).default_get(fields)
        res['document_share_id'] = self.env.context.get('active_id')
        return res

    def create_activity(self):
        partners = [self.document_share_id.document_ids[0].partner_id.id, self.create_uid.partner_id.id]
        partner_commands = [(6, 0, partners)]
        alarm_commands = [(6, 0, [1, 2])]
        calendar_event = self.env['calendar.event'].create({
            'name': self.summary,
            'start': self.date_from,
            'stop': self.date_to,
            'user_id': self.assigned_to_id.id,
            'show_as': 'free',
            'partner_ids': partner_commands,
            'alarm_ids': alarm_commands,
            'document_share_id': self.document_share_id.id,
        })
        self.env['mail.activity'].create({
            'activity_type_id': self.activity_type_id.id,  # Replace with actual activity type ID
            'summary': self.summary,
            'date_deadline': self.date_to,  # Adjust as per your requirement
            'user_id': self.assigned_to_id.id,
            'calendar_event_id': calendar_event.id,
            'res_id': self.document_share_id.id,
            'res_model_id': self.env['ir.model']._get('documents.share').id,
        })
        return calendar_event


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    document_share_id = fields.Many2one('documents.share', string='Documents Share')


class ProjectProduct(models.Model):
    _name = 'project.project.products'

    product_id = fields.Many2one('product.product', required=True)
    project_id = fields.Many2one('project.project')
    partner_id = fields.Many2one('res.partner', related='project_id.partner_id', store=True)
    date_start = fields.Date(related='project_id.date_start', store=True, string='Project Planned Date')
    date_end = fields.Date(related='project_id.date', store=True, string='Project Complete Date')
    remarks_ids = fields.Many2many('project.project.products.remarks')

    def action_add_remarks(self):
        return {
            'name': _('Add Remarks'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'remarks.wizard',
            'context': {'default_line_id': self.id},
            'view_id': self.env.ref('freezoner_custom.remarks_wizard_form_view').id,
            'target': 'new',
        }


class ProjectProductRemarks(models.Model):
    _name = 'project.project.products.remarks'

    name = fields.Char(required=True)

