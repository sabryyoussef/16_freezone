# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
#################################################################################
import werkzeug
from werkzeug.urls import url_encode
import pprint
import logging
import json
import stripe


from odoo import http, _
from odoo.http import request
from odoo.addons.web.controllers import main
from odoo.exceptions import ValidationError
from odoo.addons.portal.controllers.portal import _build_url_w_params
# from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing

_logger = logging.getLogger(__name__)


class StripeCheckoutController(http.Controller):
    _checkout_success_url = '/payment/stripe_checkout/success'
    _checkout_cancel_url = '/payment/stripe_checkout/cancel'

    @http.route('/payment/stripe_checkout/create_checkout_session', type='json', auth='public', csrf=False)
    def stripe_create_checkout_session(self, acquirer_id, **kwargs):
        acquirer = request.env['payment.provider'].browse(int(acquirer_id))
        res = acquirer._create_checkout_session(kwargs)
        return {
            'status': res['status'],
            'message': res['message'],
            'session_id': res['response']['id'] if res['status'] else False
        }

    @http.route('/payment/stripe_checkout/create_setup_intent', type='json', auth='public', csrf=False)
    def stripe_checkout_create_setup_intent(self, acquirer_id, **kwargs):
        acquirer = request.env['payment.provider'].browse(int(acquirer_id))
        res = acquirer._create_setup_intent(kwargs)
        return {
            'status': res['status'],
            'message': res['message'],
            'client_secret': res['response']['client_secret'] if res['status'] else False
        }

    @http.route([_checkout_success_url, _checkout_cancel_url], type='http', auth='public')
    def stripe_checkout_success(self, **kwargs):
        reference = kwargs.get('reference')
        data = {'reference': reference}

        if reference:
            transaction = request.env['payment.transaction'].sudo().search([('reference', '=', reference)])
            res = transaction.provider_id._stripe_call(
                method='_payment_intent',
                operation='retrieve',
                **{'id': transaction.stripe_checkout_payment_intent}
            )
            if res['status'] and res['response'].get('charges') and res['response'].get('charges').get('total_count'):
                res = res['response'].get('charges').get('data')[0]
            else:
                res = res['response']
            data.update(res)
        _logger.info('Stripe Checkout: entering form_feedback with post data %s' % pprint.pformat(data))

        request.env['payment.transaction'].sudo()._handle_notification_data('stripe_checkout',data)
        return werkzeug.utils.redirect('/payment/status')

    @http.route(['/payment/stripe_checkout/s2s/save_card'], type='json', auth='public', csrf=False)
    def stripe_checkout_s2s_save_card(self, acquirer_id, **kwargs):
        token = request.env['payment.provider'].browse(int(acquirer_id)).s2s_process(kwargs)

        if not token:
            return {'status': False, 'message': _("Some error occured while saving your card data.")}

        return {
            'status': True,
            'id': token.id,
            'short_name': token.short_name,
        }

    def _get_order_tx_vals(self, order_id, **kwargs):
        order = request.env['sale.order'].sudo().browse(order_id)
        if not order or not order.order_line or not order.has_to_be_paid():
            return False, {}
        return order, {'return_url': order.get_portal_url()}

    def _get_invoice_tx_vals(self, invoice_id, **kwargs):
        error_url = kwargs.get('error_url', '/my')
        access_token = kwargs.get('access_token')
        params = {}
        if access_token:
            params['access_token'] = access_token

        invoice_sudo = request.env['account.invoice'].sudo().browse(invoice_id).exists()
        if not invoice_sudo:
            return False, {}
        success_url = kwargs.get(
            'success_url', "%s?%s" % (invoice_sudo.access_url, url_encode({'access_token': access_token}) if access_token else '')
        )
        params['success'] = 'pay_invoice'
        return invoice_sudo, {'return_url': _build_url_w_params(success_url, params)}

    @http.route(['/payment/stripe_checkout/do_payment'], type='json', auth="public", website=True)
    def stripe_checkout_do_payment(self, acquirer_id=None, order_id=None, invoice_id=None, token=None, **kwargs):
        order = request.website.sale_get_order()
        acquirer = request.env['payment.provider'].browse(int(acquirer_id))

        assert order.partner_id.id != request.website.partner_id.id
        # tx_obj => object that will use to create transcation record can be sale order or account invoice
        tx_obj = order
        vals = {
            'payment_token_id': int(token) if token else None,
            'return_url': '/shop/payment/validate',
            'type': 'server2server'
        }

        if not token:
            vals['acquirer_id'] = int(acquirer_id)

        if order_id:
            tx_obj, data = self._get_order_tx_vals(order_id, **kwargs)
            vals.update(data)
        elif invoice_id:
            tx_obj, data = self._get_invoice_tx_vals(invoice_id, **kwargs)
            vals.update(data)
        if not token:
            vals['acquirer_id'] = int(acquirer_id)
        if not tx_obj:
            return {'status': False, 'message': _("Error occurred while processing your transaction.")}

        transaction = tx_obj._create_payment_transaction(vals)

        last_tx_id = request.session.get('__website_sale_last_tx_id')
        last_tx = request.env['payment.transaction'].browse(last_tx_id).sudo().exists()
        # if last_tx:
        #     PaymentProcessing.remove_payment_transaction(last_tx)
        # PaymentProcessing.add_payment_transaction(transaction)
        if last_tx:
            PaymentPostProcessing.remove_transactions(last_tx)
        PaymentPostProcessing.monitor_transactions(transaction)
        request.session['__website_sale_last_tx_id'] = transaction.id

        res = transaction.create_payment(kwargs)
        return res
    
    def get_order_info(self,data):
        order_info = {}
        if data:
            order_info.update({'customer_info':{'name':data.get('partner_name') or 'Public User','address':{'line1':data.get('line1'),'postal_code':data.get('postal_code'),'city':data.get('city'),'state':data.get('city'),'country':data.get('country')}},'order_amount':int(eval(data.get('amount'))),'order_currency':data.get('currency_name'),'invoice_num':data.get('invoice_num')})
            return order_info
        raise ValidationError('Sale Order not found')

    @http.route('/create-payment-intent', methods=['POST'],auth="public",type='json')
    def create_payment(self,**kw):
        try:
            # Create a PaymentIntent with the order amount and currency
            order_info = self.get_order_info(kw)
            intent = stripe.PaymentIntent.create(
                amount = order_info.get('order_amount'),
                currency = order_info.get('order_currency'),
                automatic_payment_methods={
                    'enabled': True,
                },
                description=order_info.get('invoice_num'),
                shipping= order_info.get('customer_info'),
            )
            return json.dumps({
                'clientSecret': intent['client_secret']
            })
        except Exception as e:
            return e

    @http.route('/stripe/payment/status',type="http",auth="public",methods=["POST","GET"],csrf=False,save_session=False)
    def stripe_payment_status(self,**kw):
        acquirer_id = request.env['payment.provider'].sudo().search([('code','=','stripe_checkout')])
        if kw:
            stripe.api_key = acquirer_id.stripe_checkout_client_secret_key
            paymentIntent_data = stripe.PaymentIntent.retrieve(kw.get('payment_intent'))
            paymentIntent_data.update({'reference':paymentIntent_data.get('description')})
            request.env['payment.transaction'].sudo()._handle_notification_data('stripe_checkout',paymentIntent_data)
            return werkzeug.utils.redirect('/payment/status')
            
   