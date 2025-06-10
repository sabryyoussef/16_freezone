# -*- coding: utf-8 -*-

from odoo import models, _


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    def _compute_feature_support_fields(self):
        """ Override of `payment` to enable additional features. """
        super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == 'stripe').update({
            'support_fees': True,
        })
