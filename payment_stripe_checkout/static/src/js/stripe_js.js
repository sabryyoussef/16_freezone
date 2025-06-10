odoo.define('payment_stripe_checkout.stripe_js', function (require) {
    "use strict";
    
    var ajax = require('web.ajax');
    var core = require('web.core');
    var PaymentForm = require('payment.payment_form');

    var _t = core._t;
    const checkoutForm = require('payment.checkout_form');
    const manageForm = require('payment.manage_form');

    const stripeCheckoutMixin = {

        _processRedirectPayment: function (provider, paymentOptionId, processingValues) {
            if (provider !== 'stripe_checkout') {
                return this._super(...arguments);
            }

            const stripeJS = Stripe(processingValues['publishable_key']);
            stripeJS.redirectToCheckout({
                sessionId: processingValues['session_id']
            });
        },

    };

    checkoutForm.include(stripeCheckoutMixin);
    manageForm.include(stripeCheckoutMixin);

});