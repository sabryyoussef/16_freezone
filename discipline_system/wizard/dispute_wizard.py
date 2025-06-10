from odoo import models, fields, api
from datetime import date
from lxml import etree


class DeductionsDisputeWizard(models.TransientModel):
    _name = 'hr.deductions.dispute.wizard'
    _description = 'Disciplinary Dispute'

    dispute = fields.Text(required=1)
    dispute_to = fields.Many2one('res.users', required=1)
    deduction_id = fields.Many2one('hr.deductions', readonly=1)

    def submit(self):
        self.sudo().deduction_id.state = 'Disputed'
        self.deduction_id.activity_ids.action_feedback()
        activity_id = self.sudo().env['mail.activity'].create({
            'summary': 'Disciplinary Disputed',
            'activity_type_id': self.env['mail.activity.type'].search([('name', '=', 'Email')]).id,
            'res_model_id': self.env['ir.model']._get(self.deduction_id._name).id,
            'res_id': self.deduction_id.id,
            'user_id': self.dispute_to.id,
            'note': f"Dear {self.dispute_to.name} Kindly Note that {self.deduction_id.employee_id.name} Disputed a Disciplinary \n {self.dispute}",
        })
        self.sudo().deduction_id.needed_activity.action_feedback()
        self.sudo().deduction_id.needed_activity = activity_id.id

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        ret_val = super(DeductionsDisputeWizard, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        doc = etree.XML(ret_val['arch'])
        group_managers = self.env.ref('discipline_system.group_deductions_manager').users.ids
        disputers = doc.xpath("//field[@name='dispute_to']")
        for disputer in disputers:
            disputer.set('domain', f"[('id', 'in', {group_managers})]")
        ret_val['arch'] = etree.tostring(doc)
        return ret_val
