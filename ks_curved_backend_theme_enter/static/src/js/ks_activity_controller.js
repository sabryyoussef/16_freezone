/** @odoo-module **/

import ActivityController from '@mail/js/views/activity/activity_controller';
const { patch } = require('web.utils');

patch(ActivityController.prototype, 'ks_curved_backend_theme_enter/static/src/js/ks_activity_controller.js', {

    events: _.extend({}, ActivityController.prototype.events, {
            "click button.reload_view": "_KsReloadView",
        }),


    _KsReloadView: function() {
         this.reload();
    },



});

