from odoo import models, fields, api
from datetime import date


class PayrollDeductionsReasons(models.Model):
    _name = 'hr.deductions.reasons'
    _description = 'Disciplinary Reasons'
    _rec_name = 'reason'

    reason = fields.Char(required=1, )
    rate = fields.Float(string="Days Deduction Rate", required=1, )
    input_type = fields.Many2one(comodel_name='hr.payslip.input.type')

    # @api.model
    # def create(self, vals_list):
    #     res = super(PayrollDeductionsReasons, self).create(vals_list)
    #     input_type = self.env['hr.payslip.input.type'].create({
    #         'name': res.reason,
    #         'code': self.env.ref('discipline_system.deduction_salary_rule').code,
    #         'country_id': False
    #     })
    #     res.input_type = input_type
    #     return res

    def write(self, vals):
        res = super(PayrollDeductionsReasons, self).write(vals)
        self.input_type.name = self.reason
        return res


class PayrollDeductions(models.Model):
    _name = 'hr.deductions'
    _description = 'Disciplinary'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(compute='_compute_name', store=True)

    @api.depends('employee_id', 'deduction_date', 'reason')
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.employee_id.name} - {rec.deduction_date} - {rec.reason.reason}"

    state = fields.Selection(selection=[
        ('Draft', 'Draft'), ('Confirmed', 'Pending Employee'), ('Accepted', 'Accepted'), ('Disputed', 'Disputed'),
        ('Cancel', 'Cancel'), ],
        default='Draft', required=1, tracking=1)
    active = fields.Boolean(string="Active", default=True)
    reason = fields.Many2one(string="Reason", required=1, comodel_name='hr.deductions.reasons')
    rate = fields.Float(string="Days Deduction Rate", required=1, readonly=0, tracking=1)
    deduction_date = fields.Date(string="Disciplinary Date", required=1, default=date.today())
    manager = fields.Boolean(compute='_compute_is_manager')

    def _compute_is_manager(self):
        for rec in self:
            if not self.user_has_groups(
                    'discipline_system.group_deductions_manager') and self.env.user.id != rec.employee_id.user_id.id:
                rec.manager = False
            else:
                rec.manager = True

    @api.onchange('reason')
    def _onchange_reason(self):
        for rec in self:
            rec.rate = rec.reason.rate

    @api.model
    def _deduction_creator(self):
        return self.env.uid

    creator = fields.Many2one(comodel_name='res.users', default=_deduction_creator, readonly=1)
    employee_id = fields.Many2one(comodel_name='hr.employee', required=1, )
    needed_activity = fields.Many2one('mail.activity')

    def write(self, values):
        res = super(PayrollDeductions, self).write(values)
        if values.get('state') == 'Confirmed':
            self.activity_ids.action_feedback()
            activity_id = self.env['mail.activity'].create({
                'summary': 'Disciplinary Created',
                'activity_type_id': self.env['mail.activity.type'].search([('name', '=', 'To Do')]).id,
                'res_model_id': self.env['ir.model']._get(self._name).id,
                'res_id': self.id,
                'user_id': self.employee_id.user_id.id or self.create_uid.id,
                'note': f"Dear {self.employee_id.name} Kindly Note that a Disciplinary has been created for you kindly Confirm or Dispute if you think that something is wrong",
            })
            self.needed_activity = activity_id.id
        return res

    @api.model
    def create(self, values):
        res = super(PayrollDeductions, self).create(values)
        if not values.get('create_uid'): values['create_uid'] = 1
        if values.get('state') == 'Confirmed':
            activity_id = self.env['mail.activity'].create({
                'summary': 'Disciplinary Created',
                'activity_type_id': self.env['mail.activity.type'].search([('name', '=', 'To Do')]).id,
                'res_model_id': self.env['ir.model']._get(self._name).id,
                'res_id': res.id,
                'user_id': res.employee_id.user_id.id or values.get('create_uid'),
                'note': f"Dear {res.employee_id.name} Kindly Note that a Disciplinary has been created for you kindly Confirm or Dispute if you think that something is wrong",
            })
            res.needed_activity = activity_id.id
        return res

    def dispute(self):
        return {
            'name': 'Disciplinary Dispute',
            'view_mode': 'form',
            'res_model': 'hr.deductions.dispute.wizard',
            'view_id': False,
            'context': {'default_deduction_id': self.id},
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def accept(self):
        for rec in self:
            rec.activity_ids.action_feedback()
            rec.sudo().state = 'Accepted'

    def reset(self):
        for rec in self:
            rec.activity_ids.action_feedback()
            rec.sudo().state = 'Draft'

    def cancel(self):
        for rec in self:
            rec.activity_ids.action_feedback()
            rec.sudo().state = 'Cancel'

    def confirm(self):
        self.sudo().state = 'Confirmed'
