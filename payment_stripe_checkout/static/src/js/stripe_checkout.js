odoo.define('payment_stripe_checkout.stripe_checkout', function(require) {
    "use strict";
 
    var ajax = require('web.ajax');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var Widget = require('web.Widget');
    const {loadJS} = require('@web/core/assets');
    
    var qweb = core.qweb;

    var _t = core._t;
    if ($.blockUI) {
        $.blockUI.defaults.css.border = '0';
        $.blockUI.defaults.css["background-color"] = '';
        $.blockUI.defaults.overlayCSS["opacity"] = '0.9';
    }

    var StripeCheckoutRedirect = Widget.extend({
        init: function() {
            this.elements = false;
            this.stripe = false
            this.stripe_checkout = undefined;
            this.form = $('form[provider="stripe_checkout"]');
            this._initBlockUI(_t("Loading Stripe JS..."));
            this.willStart();
 
        },
        willStart: async function () {
            this.start();
            // return this._super.apply(this, arguments)
        },
        start: function () {
            this._super.apply(this, arguments)
            var self = this
            self._initBlockUI(_t("Initializing Payment..."));
            self._renderDropinUi();
            $.ajax({url:'https://js.stripe.com/v3/',type:"GET",dataType:"script",success:function(){
                self.initialize(); 
            }})
             
        },
        initialize: async function() {
            var items = {};
            var self = this;
            $('input[type="hidden"]').each(function(){items[this.name]=this.value})
            const stripe = Stripe($('input[name="stripe_checkout_pub_key"]').val());
            self.stripe = stripe;
            const response =ajax.jsonRpc("/create-payment-intent", 'call',items).then(function(data){
                var data = JSON.parse(data)
                const clientSecret  =  data['clientSecret']
                const appearance = {
                theme: 'stripe',
                };
                self.elements = stripe.elements({ appearance, clientSecret });
                const paymentElement = self.elements.create("payment");
                paymentElement.mount("#payment-element");

            });

            $("#payment-form").on("submit",function(){
                this.handleSubmit();
            } );
            
            $('#stripe_dropin_modal').ready(function(){
              $('#close-modal').on("click",function(){
                console.log('-----Close Stripe Modal---------');
                location.reload();
              }) 
            });  
        },

        handleSubmit: async function(e) {
            var self = this
            e.preventDefault();
            self.setLoading(true);
            var self= this;
            var elements = self.elements;
            const error = await self.stripe.confirmPayment({
              elements,
              confirmParams: {
                // Make sure to change this to your payment completion page
                return_url: window.location.origin+"/stripe/payment/status",
              },
            });
            if (error.type === "card_error" || error.type === "validation_error") {
                self.showMessage(error.message);
              } else {
                self.showMessage("An unexpected error occurred.");
              }
            
              self.setLoading(false);

        },

        setLoading:function (isLoading) {
            if (isLoading) {
              // Disable the button and show a spinner
              document.querySelector("#submit").disabled = true;
              $("#spinner").removeClass("hidden");
              $("#button-text").addClass("hidden");
            } else {
              document.querySelector("#submit").disabled = false;
              $("#spinner").addClass("hidden");
              $("#button-text").removeClass("hidden");
            }
          },

          showMessage: function(messageText) {
            const messageContainer = $("#payment-message");
          
            messageContainer.removeClass("hidden");
            messageContainer.val(messageText);
          
            setTimeout(function () {
              messageContainer.addClass("hidden");
              messageContainer.val = '';
            }, 4000);
          },
          
          checkStatus:async function () {
            var self = this;
            const clientSecret = new URLSearchParams(window.location.search).get(
              "payment_intent_client_secret"
            );
          
            if (!clientSecret) {
              return;
            }
          
            const { paymentIntent } = await stripe.retrievePaymentIntent(clientSecret);
          
            switch (paymentIntent.status) {
              case "succeeded":
                self.showMessage("Payment succeeded!");
                break;
              case "processing":
                self.showMessage("Your payment is processing.");
                break;
              case "requires_payment_method":
                self.showMessage("Your payment was not successful, please try again.");
                break;
              default:
                self.showMessage("Something went wrong.");
                break;
            }
          },
        _renderDropinUi: function() {
            var self = this;
            self._initBlockUI(_t("Processing..."));
            var $modal_html = $($('.stripe_dropin_modal').get()[0]);
            $modal_html.appendTo($('body')).modal({keyboard: false, backdrop: 'static'});
            $(".stripe_dropin_modal").modal('show');
            $(".stripe_same_page").on('click', function (e) {
                self.handleSubmit(e);
            });
           
        },


      
        _showErrorMessage: function(title, message) {
            this._revokeBlockUI();
            return new Dialog(null, {
                title: _t('Error: ') + _.str.escapeHTML(title),
                size: 'medium',
                $content: "<p>" + (_.str.escapeHTML(message) || "") + "</p>" ,
                buttons: [
                {text: _t('Ok'), close: true}]}).open();
        },
        _getFormData: function() {
            var data = {}               
            this.form.find('input').each(function() {
                data[$(this).attr('name')] = $(this).val();
            });
            return data
        },
        _initBlockUI: function(message) {
            if ($.blockUI) {
                $.blockUI({
                    'message': '<h2 class="text-white"><img src="/payment_stripe_checkout/static/src/img/spinner.gif" class="fa-pulse" style="height:100px;"/>' +
                            '    <br />' + message +
                            '</h2>'
                });
            }
            $("#o_payment_form_pay").attr('disabled', 'disabled');
        },
        _revokeBlockUI: function() {
            if ($.blockUI) {
                $.unblockUI();
            }
            $("#o_payment_form_pay").removeAttr('disabled');
        },
    });
    new StripeCheckoutRedirect();

});
