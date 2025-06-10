# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#################################################################################
import logging
from werkzeug import urls
import pprint
from werkzeug.urls import url_encode, url_join, url_parse
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
from odoo.tools.float_utils import float_round
from ..models.stripe_connector import StripeConnector

_logger = logging.getLogger(__name__)


class AcquirerStripeCheckout(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(selection_add=[('stripe_checkout', 'Stripe Checkout')], ondelete={
                            'stripe_checkout': 'set default'})
    stripe_checkout_client_secret_key = fields.Char(
        string='Secret Key ', required_if_provider='stripe_checkout', groups='base.group_user')
    stripe_checkout_publishable_key = fields.Char(
        string='Publishable Key', required_if_provider='stripe_checkout', groups='base.group_user')
    tx_do = fields.Selection([('on_redirect_page','Redirection on the acquirer website'),('on_same_page','Payment from Odoo')], default='on_redirect_page',required=True,string="Payment Flow") 

    @api.depends('code')
    def _compute_view_configuration_fields(self):
        """ Override of payment to hide the credentials page.
            :return: None
        """
        super()._compute_view_configuration_fields()
        self.filtered(lambda acq: acq.code == 'stripe_checkout').update({
            'show_credentials_page': True,
            'show_allow_tokenization': True,
            'show_payment_icon_ids': True,
            'show_pre_msg': True,
            'show_done_msg': True,
            'show_cancel_msg': True,
        })

    def _compute_feature_support_fields(self):
        """ Override of `payment` to enable additional features. """
        super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == 'stripe_checkout').update({
            'support_fees': True,
            'support_manual_capture': False,
            # 'support_refund': 'partial',
            'support_tokenization': True,
        })

    def _stripe_call(self, method, operation='create', **params):
        self.ensure_one()
        StripeConn = StripeConnector(
            api_key=self.sudo().stripe_checkout_client_secret_key
        )
        if hasattr(StripeConn, method):
            return getattr(StripeConn, method)(operation, **params)
        return {
            'status': False,
            'message': _('Error: Please contact your service provider.'),
            'response': False
        }

    def _create_payment_checkout_session(self, session_dict):
        # session_dict['payment_method_types[0]'] = 'acss_debit'
        # _logger.info(f'=====================\n{session_dict}')
        
        res = self._stripe_call(
            method='_checkout_session',
            operation='create',
            **session_dict
        )
        return res

    def _stripe_checkout_token_payment_intent(self, payload):
        response = {}
        response = self._stripe_call(
            method='_payment_intent',
            operation='create',
            **payload
        )

        return response

    def _create_setup_intent(self, kwargs):
        self.ensure_one()
        vals = {
            'usage': 'off_session',
            'payment_method_options[card][request_three_d_secure]': 'any'
        }
        res = self._stripe_call(
            method='_setup_intent',
            operation='create',
            **vals
        )
        return res

    @api.model
    def stripe_checkout_s2s_form_process(self, data):
        last4 = data.get('card', {}).get('last4')
        cc_name = data.get('cc_name')
        if not last4:
            res = self._stripe_call(
                method='_payment_method',
                operation='retrieve',
                **{'id': data.get('payment_method')}
            )
            last4 = res['response'].get('card', {}).get('last4', '****')
            cc_name = res.get('billing_details', {}).get('name')

        if not cc_name:
            partner = self.env['res.partner'].sudo().browse(
                int(data['partner_id']))
            cc_name = partner.name

        payment_token = self.env['payment.token'].sudo().create({
            'provider_id': self.id,
            'partner_id': int(data['partner_id']),
            'stripe_checkout_payment_method': data.get('payment_method'),
            'payment_details': 'XXXXXXXXXXXX%s - %s' % (last4, cc_name),
            'provider_ref': data.get('provider_ref') or self.code,
            'verified': True,
        })
        return payment_token

    def _get_feature_support(self):
        """Get advanced feature support by provider.

        Each provider should add its technical in the corresponding
        key for the following features:
            * fees: support payment fees computations
            * authorize: support authorizing payment (separates
                         authorization and capture)
            * tokenize: support saving payment data in a payment.tokenize
                        object
        """
        res = super(AcquirerStripeCheckout, self)._get_feature_support()
        res['authorize'].append('stripe_checkout')
        res['tokenize'].append('stripe_checkout')
        res['fee'].append('stripe_checkout')
        return res
    
    @api.constrains('tx_do')
    def reset_allow_tokenize(self):
        if self and self.tx_do=='on_same_page':
            self.allow_tokenization = False

            


class ResPartner(models.Model):
    _inherit = 'res.partner'

    stripe_checkout_customer_id = fields.Char('Stripe Customer ID')

    def stripe_checkout_create_customer(self, acquirer_id=None):
        self.ensure_one()
        acquirer = self.env['payment.provider'].browse(acquirer_id)
        customer_id = self.stripe_checkout_customer_id
        is_exist = True

        if customer_id:
            # check customer exist on stripe
            resp = acquirer._stripe_call(
                method='_customers',
                operation='retrieve',
                **{'id': customer_id}
            )
            if not resp['status'] and resp.get('response_code') == 404:
                is_exist = False

        if not (is_exist and customer_id) and acquirer_id:
            customer_data = {
                'address[city]': self.city or None,
                'address[country]': self.country_id.code or None,
                'address[line1]': self.street or None,
                'address[postal_code]': self.zip or None,
                'address[state]': self.state_id.name or None,
                'description': f'Odoo Partner: {self.name} (id: {self.id})',
                'email': self.email or None,
                'name': self.name,
                'phone': self.phone or None,
            }
            cust_resp = acquirer._stripe_call(
                method='_customers',
                operation='create',
                **customer_data
            )

            if cust_resp['status']:
                customer_id = cust_resp['response'].get('id')
                self.stripe_checkout_customer_id = customer_id
        return customer_id
