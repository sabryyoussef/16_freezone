
from odoo import api, fields, models,_
from odoo.exceptions import UserError, ValidationError

class Approval(models.Model):
    _inherit = 'approval.category'

    is_sale = fields.Boolean('Is Sale')

class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    sale_id = fields.Many2one('sale.order','Sale Order')

    def action_confirm(self):
        # make sure that the manager is present in the list if he is required
        self.ensure_one()
        if self.category_id.manager_approval == 'required':
            employee = self.env['hr.employee'].search([('user_id', '=', self.request_owner_id.id)], limit=1)
            if not employee.parent_id:
                raise UserError(_('This request needs to be approved by your manager. There is no manager linked to your employee profile.'))
            if not employee.parent_id.user_id:
                raise UserError(_('This request needs to be approved by your manager. There is no user linked to your manager.'))
            if not self.approver_ids.filtered(lambda a: a.user_id.id == employee.parent_id.user_id.id):
                raise UserError(_('This request needs to be approved by your manager. Your manager is not in the approvers list.'))
        if len(self.approver_ids) < self.approval_minimum:
            raise UserError(_("You have to add at least %s approvers to confirm your request.", self.approval_minimum))
        if self.requirer_document == 'required' and not self.attachment_number:
            raise UserError(_("You have to attach at least one document."))

        approvers = self.approver_ids
        if self.approver_sequence:
            approvers = approvers.filtered(lambda a: a.status in ['new', 'pending', 'waiting'])

            approvers[1:].sudo().write({'status': 'waiting'})
            approvers = approvers[0] if approvers and approvers[0].status != 'pending' else self.env['approval.approver']
        else:
            approvers = approvers.filtered(lambda a: a.status == 'new')

        if self.category_id.is_sale:
            template_id = self.env.ref('freezoner_sale_approval.email_template_sale_approval_request').id
            template = self.env['mail.template'].browse(template_id)
            template.with_context(mail_post_log=False).send_mail(self.id, force_send=True)
            self.message_post(body="Email sent to request approval")
        else:
            approvers._create_activity()
        approvers.sudo().write({'status': 'pending'})
        self.sudo().write({'date_confirmed': fields.Datetime.now()})

    def action_sale_confirm(self):
        for rec in self:
            rec.sale_id.sudo().action_confirm()
            project = self.env['project.project'].sudo().search([('sale_id', '=', rec.sale_id.id)], limit=1)
            project.sudo().write({'is_approval_request': True})
            rec.request_status = 'approved'

    @api.model
    def get_email_to(self):
        for rec in self:
            email_list = []
            email_list.append(rec.approver_ids[0].user_id.email)
            return ",".join(email_list)

    def action_reject(self):
        for rec in self:
            if rec.sale_id:
                rec.sale_id.sudo().action_cancel()
            rec.action_cancel()