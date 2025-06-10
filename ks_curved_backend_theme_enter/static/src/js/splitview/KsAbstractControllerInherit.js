odoo.define('ks_curved_backend_theme_enter.KsAbstractControllerInherit', function (require) {
"use strict";

var AbstractController = require('web.AbstractController');
const { ComponentWrapper } = require('web.OwlCompatibility');
var session = require("web.session");

AbstractController.include({

    init: function (parent, model, renderer, params) {
        this._super.apply(this, arguments);
        if(this.controlPanelProps && this.controlPanelProps.view)
            this.controlPanelProps.view.isKsSplitFormView = params.isKsSplitFormView || false;
        this.list_split_mode = params.list_split_mode || false;
    },

    on_attach_callback: function() {
            if($('.o_technical_modal').length >1 && $('.o_legacy_dialog').length===0){
                $($('.o_technical_modal')[1]).parent().remove();
            }
            return this._super.apply(this, arguments);
        },
});
return AbstractController;
});