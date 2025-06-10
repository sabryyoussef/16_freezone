from odoo import api, fields, models
from datetime import datetime, timedelta, date, time

class HrLeave(models.Model):
    _inherit = 'hr.leave'

    backup_employee_id = fields.Many2one('hr.employee', 'Back-up Employee')
    is_submitted = fields.Boolean('Is Submitted', copy=False)
    email_sent = fields.Boolean(string='Email Sent', default=False,copy=False)

    @api.model
    def get_email_to(self):
        employees = self.env["hr.employee"].search([("work_email", "!=", False)])
        email_list = [emp.work_email for emp in employees]
        return ",".join(email_list)

    def action_submit(self):
        for rec in self:
            rec.is_submitted = True
            today = fields.Date.today()
            from_date = rec.date_from.date() if rec.date_from else None
            if from_date == today:
                self._send_leave_email()
            elif from_date and from_date < today:
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'hr.leave.past.date.wizard',
                    'view_mode': 'form',
                    'view_id': self.env.ref('hr_leave_custom.view_hr_leave_past_date_wizard_form').id,
                    'target': 'new',
                    'context': {'default_leave_id': rec.id},
                }
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'hr.leave',
                'view_mode': 'form',
                'res_id': self.id,
                'views': [(False, 'form')],
                'target': 'current',
            }

    # @api.model
    # def create(self, vals):
    #     res = super(HrLeave, self).create(vals)
    #     if not vals.get('is_submitted'):
    #         res.action_submit()
    #     return res

    def _send_leave_email(self):
        template = self.env.ref('hr_leave_custom.email_template_leave_backup_hr', False)
        if template:
            template.send_mail(self.id, force_send=True)
            self.email_sent = True

    def _send_scheduled_emails(self):
        today = fields.Date.today()
        today_start = fields.Datetime.to_datetime(today)
        today_end = today_start + timedelta(days=1)
        leaves = self.search([
            ('date_from', '>=', today_start),
            ('date_from', '<', today_end),
            ('email_sent', '=', False)
        ])
        for leave in leaves:
            leave._send_leave_email()

    def action_view_leave(self):
        leave_form_id = self.env.ref('hr_holidays.hr_leave_view_form').id
        return {
            'name': 'Leave Form',  # Optional, the name of the action
            'type': 'ir.actions.act_window',
            'res_model': 'hr.leave',  # Model related to the form view
            'res_id': self.id,  # ID of the record you want to view
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(leave_form_id, 'form')],
            'target': 'new',
        }
