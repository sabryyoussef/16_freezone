/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";
const { onMounted } = owl;

patch(FormController.prototype, "ks_arc_form_controller",{
    setup(){
        this._super();
        onMounted(this._mounted);
    },

     _mounted(){
        if (document.querySelector('.reload_form_view') !== null){
            document.querySelector('.reload_form_view').addEventListener('click', this.ks_reload_view.bind(this));
        }
    },
    ks_reload_view: function () {
        this.ks_update();
   },

   async ks_update(params) {
       const form = this.model.root
       await form.load();
       this.render(true);
   },

});