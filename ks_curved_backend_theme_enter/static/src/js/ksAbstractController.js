odoo.define('ks_curved_backend_theme_enter.ksAbstractController', function(require) {
    "use strict";

    var AbstractController = require('web.AbstractController');
    AbstractController.include({
        reload: async function(params={}, KsReloadAnotherView=true) {
            if (params.controllerState) {
                this.importState(params.controllerState);
                Object.assign(params, this.searchModel.get('query'));
            }
            return this.update(params, {}, KsReloadAnotherView);
        },
    });
});
