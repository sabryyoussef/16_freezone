import logging
from werkzeug import urls
import pprint
from collections import namedtuple
from odoo.addons.payment import utils as payment_utils
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.payment.models.payment_provider import ValidationError
from odoo.tools.float_utils import float_round
from odoo.addons.payment_stripe_checkout.controllers.main import StripeCheckoutController

_logger = logging.getLogger(__name__)
ZERO_DECIMAL_CURRENCIES = [
    'BIF', 'XAF', 'XPF', 'CLP', 'KMF', 'DJF', 'GNF', 'JPY', 'MGA', 'PYGí',
    'RWF', 'KRW', 'VUV', 'VND', 'XOF'
]
STATUS_MAPPING = {
    'draft': ('requires_confirmation', 'requires_action'),
    'pending': ('processing', 'pending'),
    'authorized': ('requires_capture',),
    'done': ('succeeded',),
    'cancel': ('canceled',),
    'error': ('requires_payment_method', 'failed',),
}
PMT = namedtuple('PaymentMethodType', [
                 'name', 'countries', 'currencies', 'recurrence'])
PAYMENT_METHOD_TYPES = [
    PMT('card', [], [], 'recurring'),
    PMT('ideal', ['nl'], ['eur'], 'punctual'),
    PMT('bancontact', ['be'], ['eur'], 'punctual'),
    PMT('eps', ['at'], ['eur'], 'punctual'),
    PMT('giropay', ['de'], ['eur'], 'punctual'),
    PMT('p24', ['pl'], ['eur', 'pln'], 'punctual'),
]


class TransactionStripeCheckout(models.Model):
    _inherit = 'payment.transaction'

    stripe_checkout_payment_intent = fields.Char(
        string='Payment Intent ID', readonly=True)

    """Default methode of the core"""

    def _get_specific_rendering_values(self, processing_values):
        """ Override of payment to return transaction-specific rendering values.
        Note: self.ensure_one() from `_get_processing_values`
        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of provider-specific processing values
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)

        # if self.fees:
        #     # Similarly to what is done in `payment::payment.transaction.create`, we need to round
        #     # the sum of the amount and of the fees to avoid inconsistent string representations.
        #     # E.g., str(1111.11 + 7.09) == '1118.1999999999998'
        #     total_fee = self.currency_id.round(self.amount + self.fees)
        # else:
        #     total_fee = self.amount

        if self.provider_code != 'stripe_checkout':
            return res
        else:
            record_currency = self.env['res.currency'].browse(
                processing_values.get('currency_id'))
            invoice_num = processing_values.get('reference')
            partner_id = processing_values.get('partner_id')
            partner_obj = self.env['res.partner'].browse(int(partner_id))
            acquirer_obj = self.provider_id

            processing_values.update({'acquirer': acquirer_obj, 'currency_name': record_currency.name, 'invoice_num': invoice_num,
                                     'partner_email': partner_obj.email, 'partner_name': partner_obj.name,'line1':partner_obj.contact_address,'city':partner_obj.city,'country':partner_obj.country_code,'postal_code':partner_obj.zip,'return_url': 'payment/status'})
            rendering_values = processing_values
            txValues = self._create_checkout_session(rendering_values)
            if txValues.get("response", {}):
                rendering_values.update({
                    "api_url": txValues.get("response", {}).get('url', '')})
        return rendering_values

    @api.model
    def _get_tx_from_notification_data(self, provider_code, data):
        tx = super()._get_tx_from_notification_data(provider_code, data)
        if provider_code != 'stripe_checkout':
            return tx
        """ Given a data dict coming from stripe checkout, verify it and find the related
        transaction record. """
        reference = data.get('reference')
        if not reference:
            stripe_checkout_error = data.get('error', {}).get('message', '')
            _logger.error('Stripe Checkout: invalid reply received from stripe checkout API, looks like '
                          'the transaction failed. (error: %s)', stripe_checkout_error or 'n/a')
            error_msg = _(
                "We're sorry to report that the transaction has failed.")
            if stripe_checkout_error:
                error_msg += " " + (_("Stripe checkout gave us the following info about the problem: '%s'") %
                                    stripe_checkout_error)
            error_msg += " " + _("Perhaps the problem can be solved by double-checking your "
                                 "credit card details, or contacting your bank?")
            raise ValidationError(error_msg)

        tx = self.search([('reference', '=', reference)])
        if not tx:
            error_msg = (
                _('Stripe Checkout: no order found for reference %s') % reference)
            _logger.error(error_msg)
            raise ValidationError(error_msg)
        elif len(tx) > 1:
            error_msg = (_('Stripe Checkout: %s orders found for reference %s') % (
                len(tx), reference))
            _logger.error(error_msg)
            raise ValidationError(error_msg)
        return tx[0]

    def _stripe_checkout_form_get_invalid_parameters(self, data):
        invalid_parameters = []
        if data.get('amount') != int(self.amount if str(self.currency_id.name) in ZERO_DECIMAL_CURRENCIES else float_round(self.amount * 100, 2)):
            invalid_parameters.append(
                ('Amount', data.get('amount'), self.amount * 100))
        if data.get('currency').upper() != self.currency_id.name:
            invalid_parameters.append(
                ('Currency', data.get('currency'), self.currency_id.name))
        if data.get('payment_intent') and data.get('payment_intent') != self.stripe_checkout_payment_intent:
            invalid_parameters.append(('Payment Intent', data.get(
                'payment_intent'), self.stripe_checkout_payment_intent))
        return invalid_parameters

    def _stripe_checkout_payment_process(self, tree):
        self.ensure_one()
        if self.state != 'draft':
            _logger.info(
                'Stripe Checkout: trying to validate an already validated tx (ref %s)', self.reference)
            return True
        if capture:=tree.get('charges',{}).get('data',[{}]):
            capture = capture[0].get('captured')
        status, tx_id, captured = tree.get(
            'status'), tree.get('id'), tree.get('captured') or capture
        vals = {
            'provider_reference': tx_id,
        }
        if status == 'succeeded':
            self.write(vals)
            if captured:
                extra_message = self._get_extra_message(tree)
                self.with_context(extra_msg=extra_message)._set_done(state_message=extra_message)
            else:
                self._set_authorized()
            self._execute_callback()
            # if not self.token_id and self.type in ['form_save', 'server2server']:
          
            if not self.token_id and self.tokenize:
                s2s_data = {
                    'provider_ref': tree.get('customer'),
                    'payment_method': tree.get('payment_method'),
                    'card': tree.get('payment_method_details',{}).get('card') or tree.get('charges').get('data',[{}])[0].get('payment_method_details',{}).get('card'),
                    'provider_id': self.provider_id.id,
                    'partner_id': self.partner_id.id,
                    'verified': True,
                    'cc_name': tree.get('billing_details', {}).get('name'),
                }
                if not s2s_data['cc_name']:
                    s2s_data['cc_name'] = self.partner_id.name
                token = self.provider_id.stripe_checkout_s2s_form_process(
                    s2s_data)
                self.update({
                    'token_id': token,
                    'tokenize': False,
                })
            return True
        if status in ('processing', 'requires_action'):
            self.write(vals)
            self._set_pending()
            return True
        else:
            error = tree.get('failure_message')
            _logger.warning(error)
            vals.update({'state_message': error})
            self.write(vals)
            self._set_canceled()
            return False

    def _get_extra_message(self,tree):
        msg = _('''Related payment response recieved as  
    Transaction ID = %s,
     Payment Type = %s, 
     Card Type = %s,
     Last 4 digits = %s, 
     Status Message = %s''')%(tree.get('id'),tree.get('type'),tree.get('payment_method_details').get('card').brand,tree.get('payment_method_details').get('card').last4,tree.get('status'))
        return msg
    
    def _get_received_message(self):
        message = super()._get_received_message()
        if self.provider_code =="stripe_checkout":
            message += self._context.get('extra_msg','')
        return message
    
    def _process_notification_data(self, notification_data):
        super()._process_notification_data(notification_data)
        if self.provider_code != 'stripe_checkout':
            return
        return self._stripe_checkout_payment_process(notification_data)

    def _stripe_create_customer(self):
        customer = self.provider_id._stripe_make_request(
            'customers', payload={
                'address[city]': self.partner_city or None,
                'address[country]': self.partner_country_id.code or None,
                'address[line1]': self.partner_address or None,
                'address[postal_code]': self.partner_zip or None,
                'address[state]': self.partner_state_id.name or None,
                'description': f'Odoo Partner: {self.partner_id.name} (id: {self.partner_id.id})',
                'email': self.partner_email or None,
                'name': self.partner_name,
                'phone': self.partner_phone or None,
            }
        )
        return customer

    def _create_checkout_session(self, tx_data):
        # Filter payment method types by available payment method
        existing_pms = [pm.name.lower()
                        for pm in self.env['payment.icon'].search([])]
        linked_pms = [pm.name.lower()
                      for pm in self.provider_id.payment_icon_ids]
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
        payment_method_types = {}
        for pmt_id, pmt_name in enumerate(map(lambda pmt: pmt.name, recurrence_filtered_pmts)):
            payment_method_types[f'payment_method_types[{pmt_id}]'] = pmt_name
        reference = tx_data['invoice_num']
        website_domain = self.env['sale.order'].search([('name','=',reference)],limit=1).website_id.domain
        base_url = website_domain or self.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        partner = self.env['res.partner'].sudo().browse(
            int(tx_data.get('partner_id', 0)))
        customer_id = partner.stripe_checkout_create_customer(
            self.provider_id.id)
        stripe_session_values = self._get_common_payment_session_values(
            payment_method_types, customer_id)
        amount = float(tx_data.get('amount'))
        _logger.error('Stripe Amount: ===============>>>>  ', amount)
        success_url = StripeCheckoutController._checkout_success_url
        cancel_url = StripeCheckoutController._checkout_cancel_url
        future_usage = 'off_session' if self.tokenize else None
        session_dict = {
            **stripe_session_values,
            'line_items[][amount]': int(amount if str(tx_data['currency_name']) in ZERO_DECIMAL_CURRENCIES else float_round(amount * 100, 2)),
            'line_items[][currency]': tx_data['currency_name'],
            'line_items[][quantity]': 1,
            'line_items[][name]': reference,
            'success_url': urls.url_join(base_url, success_url) + '?reference=%s' % reference,
            'cancel_url': urls.url_join(base_url, cancel_url) + '?reference=%s' % reference,
            'payment_intent_data[description]': reference,
            'payment_intent_data[setup_future_usage]': future_usage,
        }
        _logger.error('session_dict: ===============>>>>  ', session_dict)
        if self.provider_id.capture_manually:
            session_dict['payment_intent_data[capture_method]'] = 'manual'

        res = self.provider_id._create_payment_checkout_session(session_dict)
        if res['status'] and res['response'].get('payment_intent') and reference:
            tx = self.env['payment.transaction'].sudo().search(
                [('reference', '=', reference)])
            tx.stripe_checkout_payment_intent = res['response']['payment_intent']
        _logger.error('resssssssss : ===============>>>>  ', res)
        return res

    def _send_payment_request(self):
        """ Override of payment to send a payment request to Stripe Checkout with a confirmed PaymentIntent.

        Note: self.ensure_one()

        :return: None
        :raise: UserError if the transaction is not linked to a token
        """
        super()._send_payment_request()
        if self.provider_code != 'stripe_checkout':
            return

        if not self.token_id:
            raise UserError("Stripe Checkout: " +
                            _("The transaction is not linked to a token."))
        notification_data = {'reference': self.reference}
        payload = self._stripe_checkout_token_payment_payload()
        payment_intent = self.provider_id._stripe_checkout_token_payment_intent(
            payload)
        _logger.info(
            "payment request response for transaction with reference %s:\n%s",
            self.reference, pprint.pformat(payment_intent)
        )

        if payment_intent['status'] and payment_intent['response'].get('charges') and payment_intent['response'].get('charges').get('total_count'):
            payment_intent = payment_intent['response'].get(
                'charges').get('data')[0]

        notification_data.update(payment_intent)
        _logger.info('Stripe Checkout: entering form_feedback with post data using token %s' %
                     pprint.pformat(notification_data))
        self._handle_notification_data('stripe_checkout', notification_data)

    def _get_common_payment_session_values(self, payment_method_values, customer):
        return {
            **payment_method_values,
            'customer': customer,
        }

    def _stripe_checkout_token_payment_payload(self):
        payload = {
            'amount': payment_utils.to_minor_currency_units(self.amount, self.currency_id),
            'currency': self.currency_id.name.lower(),
            'description': self.reference,
            'confirm': True,
            'customer': self.partner_id.stripe_checkout_customer_id,
            'off_session': True,
            'payment_method': self.token_id.stripe_checkout_payment_method,
        }
        if self.provider_id.capture_manually:
            payload['capture_method'] = 'manual'
        return payload
