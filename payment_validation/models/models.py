# -*- coding: utf-8 -*-

from odoo import models, fields, api
from ast import literal_eval


class PaymentValidation(models.TransientModel):
    _inherit = 'account.payment.register'

    def action_create_payments(self):
        res = super(PaymentValidation, self).action_create_payments()
        invoice_model = self.env['account.move']
        invoices = invoice_model.search([('amount_residual', '=', 0), ('move_type', '=', 'out_invoice')])
        sale_orders = self.env['sale.order'].search([('invoice_ids', 'in', invoices.ids)])
        for order in sale_orders:
            projects = order.project_ids
            if projects:
                for project in projects:
                    if not project.payment_valid:
                        project.payment_valid = True
                        project._notify()
        return res


class PaymentValidationProjectManual(models.Model):
    _inherit = 'project.project'

    payment_valid = fields.Boolean(default=False)

    def _notify(self):
        for rec in self:
            try:
                operation_team_ids = self.env['ir.config_parameter'].sudo().get_param(
                    'payment_validation.operation_team_ids')
                operation_team_ids = literal_eval(operation_team_ids)
                notifies = self.env['res.users'].search([('id', 'in', operation_team_ids)])
                notifies_mail = []
                for notify in notifies:
                    notifies_mail.append(notify.login)
                notifies_mail = ', '.join([str(item) for item in notifies_mail])
                ctx = {'email_cc': notifies_mail}
                mail_template = self.env.ref('payment_validation.project_payment_notification_mail')
                mail_template.with_context(ctx).send_mail(rec.id, force_send=True, email_values=ctx)
            except Exception as e:
                print(e)

    def change_payment_status(self):
        for rec in self:
            if rec.payment_valid:
                rec.payment_valid = False
            else:
                rec.payment_valid = True


class ProjectOperationsConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    operation_team_ids = fields.Many2many('res.users')

    def set_values(self):
        res = super(ProjectOperationsConfig, self).set_values()
        self.env['ir.config_parameter'].set_param('payment_validation.operation_team_ids',
                                                  self.operation_team_ids.ids)
        return res

    @api.model
    def get_values(self):
        res = super(ProjectOperationsConfig, self).get_values()
        try:
            operation_team_ids = self.env['ir.config_parameter'].sudo().get_param(
                'payment_validation.operation_team_ids')
            operation_team_ids = literal_eval(operation_team_ids)
            res.update(
                operation_team_ids=[(6, 0, operation_team_ids)]
            )
        except Exception:
            pass
        return res
