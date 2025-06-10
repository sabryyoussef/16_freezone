odoo.define("ks_curved_backend_theme.ksCalendarView", function (require) {
  "use strict";

  var CalendarCommonRenderer = require("@web/views/calendar/calendar_common/calendar_common_renderer");
  var config = require('web.config');
  var { patch } = require("web.utils");

  patch(CalendarCommonRenderer.CalendarCommonRenderer.prototype, "ksCalendarView", {
    get options() {
        var res=this._super();
        if (config.device.isMobile) {
           res.columnHeaderFormat = "ddd";
        }

        return res;

    }
  });
});
