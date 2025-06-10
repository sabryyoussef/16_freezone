# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PayrollDeductions(models.Model):
    _inherit = 'hr.payslip'

    deduction_ids = fields.Many2many('hr.deductions')
    deduction_count = fields.Integer(readonly=1, compute="_compute_deductions_count")

    @api.depends('deduction_ids')
    def _compute_deductions_count(self):
        for rec in self:
            rec.deduction_count = len(rec.deduction_ids)

    def action_deductions(self):
        return {
            'name': f'{self.employee_id.name}:This Month Deductions',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.deductions',
            'view_mode': 'tree,form',
            'target': 'self',
            'domain': [('id', 'in', self.deduction_ids.ids)],
        }

    @api.onchange("employee_id", "date_from", "date_to")
    def onchange_employee(self):
        self.deduction_ids = [(5, 0, 0)]
        self.input_line_ids = [(5, 0, 0)]
        # res = super(PayrollDeductions, self).onchange_employee()
        employee_id = self.employee_id
        date_from = self.date_from
        date_to = self.date_to
        deductions_reasons = self.env['hr.deductions'].read_group(
            [('employee_id', '=', employee_id.id), ('deduction_date', '>=', date_from),
             ('deduction_date', '<=', date_to), ('state', '=', 'Accepted')], fields=['id', 'reason'],
            groupby=['reason'])
        for deduction_reason in deductions_reasons:
            reason = self.env['hr.deductions.reasons'].search([('id', '=', deduction_reason['reason'][0])])
            deductions = self.env['hr.deductions'].search(
                [('employee_id', '=', employee_id.id), ('deduction_date', '>=', date_from),
                 ('deduction_date', '<=', date_to), ('state', '=', 'Accepted'),
                 ('reason', '=', reason.id)])
            deductions_total = 0.0
            for deduction in deductions:
                deductions_total = deductions_total + deduction.rate
                self.deduction_ids = [(4, deduction.id)]
            self.input_line_ids = [(0, 0, {
                'input_type_id': reason.input_type.id,
                'name': reason.reason,
                'amount': deductions_total,
                'contract_id': employee_id.contract_id.id,
            })]
        # return res

    @api.model
    def create(self, vals_list):
        res = super(PayrollDeductions, self).create(vals_list)
        res.onchange_employee()
        return res
