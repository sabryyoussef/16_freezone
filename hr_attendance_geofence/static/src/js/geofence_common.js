odoo.define('hr_attendance_geofence.GeofenceCommon', function () {
    "use strict";
    var GeofenceCommon = {
        cssLibs: [
            '/hr_attendance_geofence/static/src/js/lib/ol-6.12.0/ol.css',
            '/hr_attendance_geofence/static/src/js/lib/ol-ext/ol-ext.css',
        ],
        jsLibs: [
            '/hr_attendance_geofence/static/src/js/lib/ol-6.12.0/ol.js',
            '/hr_attendance_geofence/static/src/js/lib/ol-ext/ol-ext.js',
        ],
    };

    return {
        GeofenceCommon: GeofenceCommon,
    };
});