# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#################################################################################
import stripe
import functools
import logging

from odoo import _

_logger = logging.getLogger(__name__)


class StripeConnector(object):

    def __init__(self, api_key, version='2019-08-14'):
        stripe.api_key = api_key
        stripe.api_version = version

    def stripe_exception(function):
        """
        A decorator that wraps the passed in function and return
        exceptions should one occur
        """
        result = {'status': False, 'message': '', 'response': False}

        def _get_exception_message(e):
            message, response_code = "", False
            if e:
                _logger.info("----------------------Stripe Exception=%r", e)
                body = e.json_body
                err = body.get('error', {})
                response_code = e.http_status
                message += "Status is: %s\n" % response_code
                message += "Type is: %s\n" % err.get('type')
                message += "Code is: %s\n" % err.get('code')
                message += "Param is: %s\n" % err.get('param')
                message += "Message is: %s\n" % err.get('message')
                _logger.error(
                    "-----------------Stripe Checkout Exception=%r", message)
                message = "Message is: %s\n" % err.get('message')
            return {'message': message, 'response_code': response_code}

        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except stripe.error.CardError as e:
                # Since it's a decline, stripe.error.CardError will be caught
                result.update(_get_exception_message(e))
            except stripe.error.RateLimitError as e:
                # Too many requests made to the API too quickly
                result.update(_get_exception_message(e))
            except stripe.error.InvalidRequestError as e:
                # Invalid parameters were supplied to Stripe's API
                result.update(_get_exception_message(e))
            except stripe.error.AuthenticationError as e:
                # Authentication with Stripe's API failed
                # (maybe you changed API keys recently)
                result.update(_get_exception_message(e))
            except stripe.error.APIConnectionError as e:
                # Network communication with Stripe failed
                result.update(_get_exception_message(e))
            except stripe.error.StripeError as e:
                # Display a very generic error to the user, and maybe send
                # yourself an email
                result.update(_get_exception_message(e))
            except Exception as e:
                # Something else happened, completely unrelated to Stripe
                result.update(_get_exception_message(e))
            return result
        return wrapper

    @stripe_exception
    def _checkout_session(self, method='create', **params):
        """
            A Checkout Session represents your customer's session as they pay
            for one-time purchases or subscriptions through Checkout.
            method: create and retrieve
        """
        result = {'status': False, 'message': _(
            'Error: Please contact your service provider.'), 'response': False}
        if hasattr(stripe.checkout.Session, method):
            res = getattr(stripe.checkout.Session, method)(**params)
            result.update(
                status=True,
                message='Successful',
                response=res
            )
        return result

    @stripe_exception
    def _setup_intent(self, method='create', **params):
        """
            A SetupIntent guides you through the process of setting up a
            customer's payment credentials for future payments.
            method: create, retrieve, modify, confirm, cancel and list
        """
        result = {'status': False, 'message': _(
            'Error: Please contact your service provider.'), 'response': False}
        if hasattr(stripe.SetupIntent, method):
            res = getattr(stripe.SetupIntent, method)(**params)
            result.update(
                status=True,
                message='Successful',
                response=res
            )
        return result

    @stripe_exception
    def _payment_intent(self, method='create', **params):
        """
            A PaymentIntent guides you through the process of collecting a
            payment from your customer.
            method: create, retrieve, modify, confirm, capture, cancel and list
        """
        result = {'status': False, 'message': _(
            'Error: Please contact your service provider.'), 'response': False}
        if hasattr(stripe.PaymentIntent, method):
            res = getattr(stripe.PaymentIntent, method)(**params)
            result.update(
                status=True,
                message='Successful',
                response=res
            )
        return result

    @stripe_exception
    def _refunds(self, method='create', **params):
        """
            refund a charge that has previously been created but not yet
            refunded. Funds will be refunded to the credit or debit card that
            was originally charged.
            method: create, retrieve, modify and list
        """
        result = {'status': False, 'message': _(
            'Error: Please contact your service provider.'), 'response': False}
        if hasattr(stripe.Refund, method):
            res = getattr(stripe.Refund, method)(**params)
            result.update(
                status=True,
                message='Successful',
                response=res
            )
        return result

    @stripe_exception
    def _customers(self, method='create', **params):
        """
            API allows you to create, delete, and update your customers. You
            can retrieve individual customers as well as a list of all your
            customers.
            method: create, retrieve, modify, delete and list
        """
        result = {'status': False, 'message': _(
            'Error: Please contact your service provider.'), 'response': False}
        if hasattr(stripe.Customer, method):
            res = getattr(stripe.Customer, method)(**params)
            result.update(
                status=True,
                message='Successful',
                response=res
            )
        return result

    @stripe_exception
    def _payment_method(self, method='create', **params):
        """
            Payment Method objects represent your customer's payment
            instruments. They can be used with PaymentIntents to collect
            payments or saved to Customer objects to store instrument details
            for future payments.
            method: create, retrieve, modify, list, attach and detach
        """
        result = {'status': False, 'message': _(
            'Error: Please contact your service provider.'), 'response': False}
        if hasattr(stripe.PaymentMethod, method):
            res = getattr(stripe.PaymentMethod, method)(**params)
            result.update(
                status=True,
                message='Successful',
                response=res
            )
        return result
