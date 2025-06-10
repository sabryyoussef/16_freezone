
from odoo import models, fields, api

class CrmCompliance(models.Model):
    _inherit = 'crm.lead'

    is_compliance = fields.Selection(string="Is Compliance", selection=[('compliance', 'Compliance')])
    compliance_name = fields.Char(required=True)
    compliance_state = fields.Selection(selection=[('draft', 'Pro-forma Invoice'),('submit', 'Submit'), ('sent', 'Pro-forma Invoice Sent'), ('confirm', 'Pro-forma Confirm'), ('cancel', 'Cancel'), ], default='draft' )
    current_address = fields.Char(string="Current Address")
    passport_copy = fields.Binary(string="Passport Copy")
    uae_resident = fields.Binary(string="UAE Resident")
    with_hit = fields.Binary(string="With Hit")
    document_type_ids = fields.One2many("compliance.document.lines","compliance_id")

    def action_view_compliance(self):
        action = self.env.ref('compliance_cycle.compliance_compliance_action').read()[0]
        action['domain'] = [('id', '=', self.id)]
        action['views'] = [(
            self.env.ref('compliance_cycle.compliance_compliance_form').id, 'form'
        )]
        action['res_id'] = self.id
        return action

    def action_compliance(self):
        self.ensure_one()
        self.write({
                    'compliance_name': str(self.lead_ref) + ' ' + str(self.name),
                })
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Compliance Form',
            'res_model': 'crm.lead',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',  # Open in a popup
            'res_id': self.id,  # Open the existing record
            'view_id': self.env.ref("compliance_cycle.compliance_compliance_wizard_form").id,
            'context': {
                'default_compliance_name': str(self.lead_ref) + ' ' + str(self.name),
                'default_is_compliance': True,
                'default_partner_id': self.partner_id.id,
                'default_country_id': self.partner_id.country_id.id,
                'form_view_initial_mode': 'edit',  # Open the form in edit mode
            }
        }
        return action

    # def action_compliance(self):
    #     self.ensure_one()
    #     action = self.env.ref("compliance_cycle.compliance_compliance_action").read()[0]
    #     action['context'] = {
    #         'form_view_initial_mode': 'edit',
    #     }
    #     action['views'] = [(self.env.ref('compliance_cycle.compliance_compliance_form').id, 'form')]
    #     action['res_id'] = self.id  # Open the existing record
    #     action['target'] = 'new'  # Open in a popup
    #
    #     # Fetch the record and update its fields with context values
    #     record = self.env['crm.lead'].browse(self.id)
    #     record.write({
    #         'compliance_name': str(self.lead_ref) + ' ' + str(self.name),
    #         'is_compliance': True,
    #         'country_id': self.partner_id.country_id.id,
    #     })
    #     return action

    def action_draft(self):
        for rec in self:
            rec.compliance_state = 'draft'

    def action_send(self):
        for rec in self:
            rec.compliance_state = 'sent'

    def action_submit(self):
        for rec in self:
            rec.compliance_state = 'submit'

    def action_cancel(self):
        for rec in self:
            rec.compliance_state = 'cancel'

    def action_confirm(self):
        for rec in self:
            rec.compliance_state = 'confirm'


