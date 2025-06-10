/** @odoo-module **/

import { CalendarController } from "@web/views/calendar/calendar_controller";
import { patch } from "@web/core/utils/patch";
const { onMounted } = owl;

patch(CalendarController.prototype, "ks_arc_calendar_controller",{
    setup(){
        this._super();
        onMounted(this._mounted);
    },

     _mounted(){
        if (document.querySelector('.reload_view') !== null){
            document.querySelector('.reload_view').addEventListener('click', this.ks_reload_view.bind(this));
        }
    },
    ks_reload_view: function () {
        this.ks_update();
   },

   async ks_update() {
       const scale = this.model.meta.scale
       await this.model.load({ scale });
       this.render(true);
   },

});