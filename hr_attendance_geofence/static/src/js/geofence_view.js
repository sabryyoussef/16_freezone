odoo.define('hr_attendance_geofence.GeofenceView', function (require) {
    'use strict';

    var BasicView = require('web.BasicView');
    var GeofenceCommon = require('hr_attendance_geofence.GeofenceCommon');
    var core = require('web.core');

    var GeofenceModel = require('hr_attendance_geofence.GeofenceModel');
    var GeofenceRenderer = require('hr_attendance_geofence.GeofenceRenderer');
    var GeofenceController = require('hr_attendance_geofence.GeofenceController');

    var view_registry = require('web.view_registry');

    var _lt = core._lt;

    var GeofenceView = BasicView.extend(GeofenceCommon.GeofenceCommon,{
        accesskey: 'm',
        display_name: _lt('Attendance Geofence'),
        icon: 'fa fa-map-o',
        config: _.extend({}, BasicView.prototype.config, {
            Model: GeofenceModel,
            Renderer: GeofenceRenderer,
            Controller: GeofenceController,
        }),
        viewType: 'geofence_view',
        mobile_friendly: true,
        searchMenuTypes: [],
        withSearchBar: false,

        init: function (viewInfo, params) {
            this._super.apply(this, arguments);

            var arch = this.arch;
            var attrs = arch.attrs;

            var activeActions = this.controllerParams.activeActions;
            var mode = arch.attrs.editable && !params.readonly ? "edit" : "readonly";

            this.loadParams.limit = this.loadParams.limit || 80;
            this.loadParams.openGroupByDefault = true;
            this.loadParams.type = 'list';

            this.loadParams.groupBy = arch.attrs.default_group_by ? [arch.attrs.default_group_by] : (params.groupBy || []);

            this.rendererParams.arch = arch;
            this.rendererParams.drawingPath = attrs.drawing_path;

            this.rendererParams.record_options = {
                editable: activeActions.edit,
                deletable: activeActions.delete,
                read_only_mode: params.readOnlyMode || true,
            };

            this.controllerParams.mode = mode;
            this.controllerParams.hasButtons = true;
        }
    });
    view_registry.add('geofence_view', GeofenceView);
    return GeofenceView;
});