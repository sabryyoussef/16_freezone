# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#################################################################################
from . import controllers
from . import models
from odoo.addons.payment import setup_provider, reset_payment_provider

def pre_init_check(cr):
    from odoo.release import series
    from odoo.exceptions import Warning
    if series != '16.0':
        raise Warning('Module support Odoo series 16.0 found {}'.format(series))
    return True


def setup_stripe_data(cr, registry):
    import stripe
    stripe.set_app_info(
        "ODOO Webkul Stripe Payment Acquirer",
        version=stripe.VERSION,
        url="https://webkul.com/",
        # partner_id='partner_12345'
    )
    
def post_init_hook(cr, registry):
    setup_provider(cr, registry, 'stripe_checkout')
    setup_stripe_data(cr, registry)


def uninstall_hook(cr, registry):
    reset_payment_provider(cr, registry, 'stripe_checkout')
