odoo.define('hr_attendance_geofence.GeofenceController', function (require) {
    'use strict';

    var Context = require('web.Context');
    var core = require('web.core');
    var BasicController = require('web.BasicController');
    var Domain = require('web.Domain');

    var _t = core._t;
    var qweb = core.qweb;

    var GeofenceController = BasicController.extend({});

    return GeofenceController;

});