
from odoo import api, fields, models


class HrLeavePastDateWizard(models.TransientModel):
    _name = 'hr.leave.past.date.wizard'
    _description = 'Past Date Leave Confirmation Wizard'

    leave_id = fields.Many2one('hr.leave', required=True)
    message = fields.Char(compute='get_message')

    @api.depends('leave_id')
    def get_message(self):
        for rec in self:
            if rec.leave_id and rec.leave_id.holiday_status_id:
                rec.message = (
                    f"Your {rec.leave_id.holiday_status_id.name} application is past dated. "
                    f"Do you still want to send the email notification to all employees?"
                )
            else:
                rec.message = "Leave information is incomplete."

    def action_send_notification(self):
        self.leave_id._send_leave_email()
        return self.action_close()

    def action_save_only(self):
        return self.action_close()

    def action_close(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.leave',
            'view_mode': 'form',
            'res_id': self.leave_id.id,
            'views': [(False, 'form')],
            'target': 'current',
        }