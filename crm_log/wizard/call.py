
from odoo import models, fields, api , _
from odoo.exceptions import ValidationError

class CrmWizard(models.TransientModel):
    _name = 'crm.call.wizard'

    crm_id = fields.Many2one("crm.lead",string="CRM")
    desc = fields.Text('Description')


    def submit(self):
        activity_type = self.env.ref('mail.mail_activity_data_call')  # Built-in Call activity
        self.env['mail.activity'].sudo().create({
            'res_model_id': self.env['ir.model']._get_id('crm.lead'),
            'res_id': self.crm_id.id,
            'activity_type_id': activity_type.id,
            'active': True,
            'type': 'done',
            'summary': '',
            'note': self.desc or '',
            'user_id': self.crm_id.user_id.id or self.env.uid,
            'date_deadline': fields.Date.context_today(self),
        }).action_feedback(feedback='')
