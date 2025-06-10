# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class project(models.Model):
    _inherit = 'account.analytic.plan'

    is_default = fields.Boolean()


class SaleOrderAnalytical(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        if not self.analytic_account_id:
            for line in self.order_line:
                if not line.analytic_distribution:
                    line.analytic_distribution = {line.order_id.analytic_account_id.id: 100}
            analytical_vals = {
                'name': f"{self.name}",
                'partner_id': self.partner_id.id,
                'plan_id': self.env['account.analytic.plan'].sudo().search([('is_default', '=', True)], limit=1).id
                # self.env.ref("multiproject_saleorder.analytic_plan_projects").id,
            }
            analytical_account_id = self.env['account.analytic.account'].create(analytical_vals)
            self.analytic_account_id = analytical_account_id
        res = super(SaleOrderAnalytical, self).action_confirm()
        return res

    def action_quotation_send(self):
        """ Opens a wizard to compose an email, with relevant mail template loaded by default """
        print(' =================  ', self.order_line)
        for line in self.order_line:
            if not line.analytic_distribution:
                line.analytic_distribution = {line.order_id.analytic_account_id.id: 100}
        self.ensure_one()
        self.order_line._validate_analytic_distribution()
        for line in self.order_line:
            if not line.analytic_distribution:
                line.analytic_distribution = {line.order_id.analytic_account_id.id: 100}
        lang = self.env.context.get('lang')
        mail_template = self._find_mail_template()
        if mail_template and mail_template.lang:
            lang = mail_template._render_lang(self.ids)[self.id]
        ctx = {
            'default_model': 'sale.order',
            'default_res_id': self.id,
            'default_use_template': bool(mail_template),
            'default_template_id': mail_template.id if mail_template else None,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'default_email_layout_xmlid': 'mail.mail_notification_layout_with_responsible_signature',
            'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            'model_description': self.with_context(lang=lang).type_name,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }
