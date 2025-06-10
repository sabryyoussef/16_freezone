# -*- coding: utf-8 -*-

from werkzeug import urls

from odoo import models, _
from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_stripe.const import PAYMENT_METHOD_TYPES
from odoo.addons.payment_stripe.controllers.main import StripeController


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _stripe_prepare_payment_intent_payload(self, payment_by_token=False):
        """ Prepare the payload for the creation of a payment intent in Stripe format.

        Note: This method serves as a hook for modules that would fully implement Stripe Connect.
        Note: self.ensure_one()

        :return: The Stripe-formatted payload for the payment intent request
        :rtype: dict
        """

        res = super(PaymentTransaction, self)._stripe_prepare_payment_intent_payload(payment_by_token=payment_by_token)
        res.update({
            'amount': payment_utils.to_minor_currency_units(
                self.amount + self.fees, self.currency_id),
        })
        return res

    def _get_specific_processing_values(self, processing_values):
        """ Override of payment to return Stripe-specific processing values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic processing values of the transaction
        :return: The dict of provider-specific processing values
        :rtype: dict
        """
        res = super()._get_specific_processing_values(processing_values)
        if self.provider_code != 'stripe' or self.operation == 'online_token':
            return res

        res.update({
            'amount': self.amount + self.fees
        })
        return res

    def _stripe_create_checkout_session(self):
        """ Create and return a Checkout Session.

        :return: The Checkout Session
        :rtype: dict
        """
        # Filter payment method types by available payment method
        existing_pms = [pm.name.lower() for pm in self.env['payment.icon'].search([])]
        linked_pms = [pm.name.lower() for pm in self.provider_id.payment_icon_ids]
        pm_filtered_pmts = filter(
            lambda pmt: pmt.name == 'card'
            # If the PM (payment.icon) record related to a PMT doesn't exist, don't filter out the
            # PMT because the user couldn't even have linked it to the provider in the first place.
            or (pmt.name in linked_pms or pmt.name not in existing_pms),
            PAYMENT_METHOD_TYPES
        )
        # Filter payment method types by country code
        country_code = self.partner_country_id and self.partner_country_id.code.lower()
        country_filtered_pmts = filter(
            lambda pmt: not pmt.countries or country_code in pmt.countries, pm_filtered_pmts
        )
        # Filter payment method types by currency name
        currency_name = self.currency_id.name.lower()
        currency_filtered_pmts = filter(
            lambda pmt: not pmt.currencies or currency_name in pmt.currencies, country_filtered_pmts
        )
        # Filter payment method types by recurrence if the transaction must be tokenized
        if self.tokenize:
            recurrence_filtered_pmts = filter(
                lambda pmt: pmt.recurrence == 'recurring', currency_filtered_pmts
            )
        else:
            recurrence_filtered_pmts = currency_filtered_pmts
        # Build the session values related to payment method types
        pmt_values = {}
        for pmt_id, pmt_name in enumerate(map(lambda pmt: pmt.name, recurrence_filtered_pmts)):
            pmt_values[f'payment_method_types[{pmt_id}]'] = pmt_name

        # Create the session according to the operation and return it
        customer = self._stripe_create_customer()
        common_session_values = self._get_common_stripe_session_values(pmt_values, customer)
        base_url = self.provider_id.get_base_url()
        if self.operation == 'online_redirect':
            return_url = f'{urls.url_join(base_url, StripeController._checkout_return_url)}' \
                         f'?reference={urls.url_quote_plus(self.reference)}'
            # Specify a future usage for the payment intent to:
            # 1. attach the payment method to the created customer
            # 2. trigger a 3DS check if one if required, while the customer is still present
            future_usage = 'off_session' if self.tokenize else None
            capture_method = 'manual' if self.provider_id.capture_manually else 'automatic'
            checkout_session = self.provider_id._stripe_make_request(
                'checkout/sessions', payload={
                    **common_session_values,
                    'mode': 'payment',
                    'success_url': return_url,
                    'cancel_url': return_url,
                    'line_items[0][price_data][currency]': self.currency_id.name,
                    'line_items[0][price_data][product_data][name]': self.reference,
                    'line_items[0][price_data][unit_amount]': payment_utils.to_minor_currency_units(
                        self.amount + self.fees, self.currency_id
                    ),
                    'line_items[0][quantity]': 1,
                    'payment_intent_data[description]': self.reference,
                    'payment_intent_data[setup_future_usage]': future_usage,
                    'payment_intent_data[capture_method]': capture_method,
                }
            )
            self.stripe_payment_intent = checkout_session['payment_intent']
        else:  # 'validation'
            # {CHECKOUT_SESSION_ID} is a template filled by Stripe when the Session is created
            return_url = f'{urls.url_join(base_url, StripeController._validation_return_url)}' \
                         f'?reference={urls.url_quote_plus(self.reference)}' \
                         f'&checkout_session_id={{CHECKOUT_SESSION_ID}}'
            checkout_session = self.provider_id._stripe_make_request(
                'checkout/sessions', payload={
                    **common_session_values,
                    'mode': 'setup',
                    'success_url': return_url,
                    'cancel_url': return_url,
                    'setup_intent_data[description]': self.reference,
                }
            )
        return checkout_session
