# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleTeam(models.Model):
    _inherit = 'crm.team.member'

    target_amount = fields.Float()
    user_id = fields.Many2one(
        'res.users',
        string='Salespersons',
        check_company=True,
        index=True,
        ondelete='cascade',
        required=True,
        domain="[('active', 'in', [True, False])]"
    )
