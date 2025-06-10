/** @odoo-module **/

import { PivotController } from "@web/views/pivot/pivot_controller";
import { patch } from "@web/core/utils/patch";
const { onMounted } = owl;

patch(PivotController.prototype, "ks_arc_pivot_controller",{
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
        const metaData = this.model._buildMetaData();
        const config = { metaData, data: this.model.data };
        await this.model._loadData(config);
        this.render(true);
   },

});