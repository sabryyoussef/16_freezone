# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _

class EquipmentRequest(models.Model):
    _name = "equipment.request"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "equipment request"


    name = fields.Char('Request No', default=lambda self: _('New'),copy=False, readonly=True, required=True)
    employee_id = fields.Many2one('hr.employee', string='Requested by', required=True)
    note = fields.Html('Comments', translate=True)
    request_date = fields.Datetime(string='Request Date', default=fields.Date.today)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submit To Manager'),
        ('approved', 'Approved'),
        ('reject','Rejected'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Stage', default='draft', tracking=True)

    def _create_equipment_request_sequence(self):
        company_id = self.env.company.id
        seq = self.env['ir.sequence'].search([('code', '=', 'equipment.request'), ('company_id', '=', company_id)], limit=1)
        if not seq:
            seq = self.env['ir.sequence'].create({
            'name': 'Hr Equipment Sequence %s' % company_id,
            'code': 'equipment.request',
            'prefix': 'HE%s' % company_id,
            'padding': 5,
            'company_id': company_id,
            })
        return seq

    @api.model_create_multi
    def create(self, vals):
        res = super(EquipmentRequest, self).create(vals)
        seq = self._create_equipment_request_sequence()
        res.write({'name':seq.next_by_id()})
        return res
    
    def action_submit(self):
        self.write({'state':'submitted'})

    def action_cancel(self):
        self.write({'state':'cancelled'})

    def action_approve(self):
        self.write({'state':'approved'})
        template_id = self.env.ref('bi_hr_equipment_asset_management.email_template_equipment_request_APPROVED').id
        template = self.env['mail.template'].browse(template_id)
        template.send_mail(self.id, force_send=True)
        
        template_id_manager=self.env.ref('bi_hr_equipment_asset_management.email_template_equipment_request_APPROVED_manager').id
        template_manager=self.env['mail.template'].browse(template_id_manager)
        template_id_user=self.env.ref('bi_hr_equipment_asset_management.email_template_equipment_request_APPROVED_user').id
        print(self.employee_id.parent_id)
        template_user=self.env['mail.template'].browse(template_id_user)
        if self.employee_id.parent_id:
            template_manager.send_mail(self.id, force_send=True)
        else:
            template_user.send_mail(self.id, force_send=True)



    def action_reject(self):
        self.write({'state':'reject'})
        template_id = self.env.ref('bi_hr_equipment_asset_management.email_template_equipment_request_REJECTED').id
        template = self.env['mail.template'].browse(template_id)
        template.send_mail(self.id, force_send=True)
        template_id_manager=self.env.ref('bi_hr_equipment_asset_management.email_template_equipment_request_REJECTED_manager').id
        template_manager=self.env['mail.template'].browse(template_id_manager)
        template_id_user=self.env.ref('bi_hr_equipment_asset_management.email_template_equipment_request_REJECTED_user').id
        print(self.employee_id.parent_id)
        template_user=self.env['mail.template'].browse(template_id_user)
        if self.employee_id.parent_id:
            template_manager.send_mail(self.id, force_send=True)
        else:
            template_user.send_mail(self.id, force_send=True)

























    



    
