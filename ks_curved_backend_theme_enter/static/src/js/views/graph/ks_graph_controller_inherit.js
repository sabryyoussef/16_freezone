/** @odoo-module **/

import { GraphController } from "@web/views/graph/graph_controller";
import { patch } from "@web/core/utils/patch";
const { onMounted } = owl;

patch(GraphController.prototype, "ks_arc_graph_controller",{
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
       var measure = this.model.metaData.measure;
       this.model.updateMetaData({ measure });
       this.render(true);
   },

});