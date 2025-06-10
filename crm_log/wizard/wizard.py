
from odoo import models, fields, api,_
from odoo.exceptions import ValidationError
from datetime import datetime

class CrmWizard(models.TransientModel):
    _name = 'crm.wizard'

    current_stage_id = fields.Many2one('crm.stage',string='Current Stage', related='crm_id.stage_id')
    move_to_stage_id = fields.Many2one('crm.stage',string='Move To Stage',required=True)
    crm_id = fields.Many2one("crm.lead",string="CRM")

    def submit(self):
        for rec in self:
            mails = self.env['mail.mail'].sudo().search([('model', '=', 'crm.lead'), ('res_id', '=', rec.crm_id.id)])
            attachments = self.env['ir.attachment'].sudo().search(
                [('res_model', '=', 'crm.lead'), ('res_id', '=', rec.crm_id.id)])
            call = self.env['mail.activity'].sudo().search(
                [('res_model', '=', 'crm.lead'), ('activity_type_id.name', '=', 'Call'),
                 ('res_id', '=', rec.crm_id.id)])
            stage_name = rec.current_stage_id.name
            move_to_stage_name = rec.move_to_stage_id.name

            if stage_name == 'New':
                if move_to_stage_name == 'Proposal Sent':
                    self._validate_requirements(mails, call, attachments)
                elif move_to_stage_name in ['Invoice Sent', 'Full Payment', 'Partial Payment Collected']:
                    self._validate_requirements(mails, call, attachments)
                    if move_to_stage_name != 'Proposal Sent' and rec.crm_id.quotation_count == 0:
                        err_msg = _("Please Create Min One Pro-forma Invoice")
                        raise ValidationError(_(err_msg))
            if move_to_stage_name == 'Negotiation':
                rec.crm_id.write({'date_conversion': datetime.today()})
            rec.crm_id.stage_id = rec.move_to_stage_id.id

    def _validate_requirements(self, mails, call, attachments):
        if not mails:
            raise ValidationError(_("Please Send Mail To Customer"))
        if not call:
            raise ValidationError(_("Please Add Call"))
        if not attachments:
            raise ValidationError(_("Please Add Attachments"))

