# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "Stripe Payment Acquirer (SCA Ready)",
  "summary"              :  """Integrate Stripe Payment gateway with Odoo. The module allows the customers to make payments for their website orders using Stripe payment acquirer.""",
  "category"             :  "Accounting",
  "version"              :  "1.0.0",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "maintainer"           :  "Prakash Kumar",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/Odoo-Website-Stripe-Payment-Acquirer.html",
  "description"          :  """Odoo Website Stripe Payment Acquirer
Odoo Stripe Payment Gateway
Payment Gateway
Stripe
Stripe
Stripe integration
Payment acquirer
Payment processing
Payment processor
Website payments
Sale orders payment
Customer payment
Integrate Stripe payment acquirer in Odoo
Integrate Stripe payment gateway in Odoo
second Payment Services Directive (PSD2)
Strong Customer Authentication (SCA)
PSD2: SCA Ready
3D Secure 2 (3DS2)
3D Secure 1 (3DS)""",
  "live_test_url"        :  "https://odoodemo.webkul.com/?module=payment_stripe_checkout",
  "depends"              :  ['account','payment'],
  "data"                 :  [
                             'views/payment_acquirer.xml',
                             'views/payment_stripe_checkout.xml',
                             'data/stripe_checkout_acquirer_data.xml',
                            ],
  "demo"                 : [],
  "assets"               :{'web.assets_frontend':
                            [
                              '/payment_stripe_checkout/static/src/js/stripe_js.js',
                              ],
                            },
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "price"                :  89.0,
  "currency"             :  "USD",
  "pre_init_hook"        :  "pre_init_check",
  'post_init_hook': 'post_init_hook',
  'uninstall_hook': 'uninstall_hook',
  "external_dependencies":  {'python': ['stripe']},
}
