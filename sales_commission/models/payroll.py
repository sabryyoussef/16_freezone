# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleTeam(models.Model):
    _inherit = 'hr.payslip'

    def has_commissions(self, payslip):
        employee = self.env['hr.employee'].search([('id', '=', payslip.employee_id)])
        start_date = payslip.date_from
        end_date = payslip.date_to
        has_commissions = self.env['crm.commission'].search_count(
            [('member_id', '=', employee.user_id.id), ('payment_date', '>=', start_date),
             ('payment_date', '<=', end_date)])
        return has_commissions

    def commissions(self, payslip):
        employee = self.env['hr.employee'].search([('id', '=', payslip.employee_id)])
        start_date = payslip.date_from
        end_date = payslip.date_to
        commission_obj = self.env['crm.commission'].search(
            [('member_id', '=', employee.user_id.id), ('payment_date', '>=', start_date),
             ('payment_date', '<=', end_date)], limit=1)

        return commission_obj.target_percentage, commission_obj.type, commission_obj.achievement_net
