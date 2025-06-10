# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ClientCategorisation(models.Model):
    _inherit = 'res.partner'

    partner_category = fields.Selection(selection=[('normal', 'Normal'), ('vip', 'VIP'), ('vvip', 'VVIP')], required=1,
                                        default='normal')
