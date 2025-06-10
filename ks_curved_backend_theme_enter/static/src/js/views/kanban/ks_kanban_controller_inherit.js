/** @odoo-module **/

import { KanbanController } from "@web/views/kanban/kanban_controller";
import { patch } from "@web/core/utils/patch";
const { onMounted } = owl;

patch(KanbanController.prototype, "ks_arc_kanban_controller",{
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
       const kanban = this.model.root
       await kanban.load();
       this.render(true);
   },

});