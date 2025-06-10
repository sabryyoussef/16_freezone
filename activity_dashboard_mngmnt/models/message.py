
from odoo import api, fields, models

class Message(models.Model):
    _inherit = 'mail.message'

    user_id = fields.Many2one(
        'res.users',
        related='employee_id.user_id',
        store=True
    )
    parent_user_id = fields.Many2one(
        'res.users',
        related='employee_id.parent_id.user_id',
        store=True
    )
    employee_id = fields.Many2one(
        'hr.employee',
        compute='_compute_employee_id',
        readonly=False,
        store=True
    )

    @api.depends('author_id')
    def _compute_employee_id(self):
        for rec in self:
            employee = self.env['hr.employee'].search([('address_home_id', '=', rec.author_id.id)], limit=1)
            rec.employee_id = employee.id if employee else False

