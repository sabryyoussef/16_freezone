
from odoo import api, fields, models
import  base64

class ResCompany(models.Model):
    _inherit = "res.company"

    @api.model
    def action_open_sale_onboarding_sample_quotation(self):
        """ Onboarding step for sending a sample quotation. Open a window to compose an email,
            with the edi_invoice_template message loaded by default. """
        sample_sales_order = self._get_sample_sales_order()
        template = self.env.ref('task_update.email_template_edi_sale_custom', False)

        message_composer = self.env['mail.compose.message'].with_context(
            default_use_template=bool(template),
            mark_so_as_sent=True,
            default_email_layout_xmlid='mail.mail_notification_layout_with_responsible_signature',
            proforma=self.env.context.get('proforma', False),
            force_email=True, mail_notify_author=True
        ).create({
            'res_id': sample_sales_order.id,
            'template_id': template and template.id or False,
            'model': 'sale.order',
            'composition_mode': 'comment'})

        # Simulate the onchange (like trigger in form the view)
        update_values = \
        message_composer._onchange_template_id(template.id, 'comment', 'sale.order', sample_sales_order.id)['value']
        message_composer.write(update_values)

        message_composer._action_send_mail()

        self.set_onboarding_step_done('sale_onboarding_sample_quotation_state')

        self.action_close_sale_quotation_onboarding()

        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_orders")
        action.update({
            'views': [[self.env.ref('sale.view_order_form').id, 'form']],
            'view_mode': 'form',
            'target': 'main',
        })
        return action

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    url = fields.Char(compute='get_url')

    def get_url(self):
        for rec in self:
            rec.url = rec.get_base_url() + '/my/orders/'+str(rec.id)

    def _find_mail_template(self):
        """ Get the appropriate mail template for the current sales order based on its state.

        If the SO is confirmed, we return the mail template for the sale confirmation.
        Otherwise, we return the quotation email template.

        :return: The correct mail template based on the current status
        :rtype: record of `mail.template` or `None` if not found
        """
        self.ensure_one()
        if self.env.context.get('proforma') or self.state not in ('sale', 'done'):
            return self.env.ref('task_update.email_template_edi_sale_custom', raise_if_not_found=False)
        else:
            return self._get_confirmation_template()

    def _get_confirmation_template(self):
        """ Get the mail template sent on SO confirmation (or for confirmed SO's).

        :return: `mail.template` record or None if default template wasn't found
        """
        return self.env.ref('task_update.email_template_edi_sale_custom', raise_if_not_found=False)
