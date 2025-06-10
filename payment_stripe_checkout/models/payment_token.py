# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#################################################################################


import logging
import pprint
from odoo import api, fields, models, _



class TokenStripeCheckout(models.Model):
    _inherit = 'payment.token'

    stripe_checkout_payment_method = fields.Char('Payment Method ID')

