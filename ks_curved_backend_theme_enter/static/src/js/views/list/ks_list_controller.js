/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { patch } from "@web/core/utils/patch";
const { onMounted } = owl;

patch(ListController.prototype, "ks_arc_list_controller",{
    setup(){
        this._super();
        onMounted(this._mounted);
    },

     _mounted(){
        if (document.querySelector('.reload_list_view') !== null){
            document.querySelector('.reload_list_view').addEventListener('click', this.ks_reload_view.bind(this));
        }
    },
    ks_reload_view: function () {
        this.ks_update();
   },

   async ks_update(params) {
       const list = this.model.root
       await list.load();
       this.render(true);
   },

});