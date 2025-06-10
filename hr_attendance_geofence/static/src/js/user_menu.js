odoo.define("hr_attendance_geofence.user_menu", function (require) {
    "use strict";

    let __exports = {};
    const { registry } = require("@web/core/registry");

    function HrAttendanceGeofence(env)  {
        return {
            type: "item",
            id: "hr_attendance_geofence",
            description: env._t("HrAttendanceGeofence"),
            callback: async function () {
                const actionDescription = await env.services.orm.call("res.users", "action_get_attendance_geofence");
                actionDescription.res_id = env.services.user.userId;
                env.services.action.doAction(actionDescription);
            },
            sequence: 5,
        };
    }

    registry.category("user_menuitems").add('hr_attendance_geofence', HrAttendanceGeofence, { force: true })
    return __exports;

});