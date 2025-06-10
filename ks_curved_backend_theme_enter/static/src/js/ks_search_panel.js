/** @odoo-module **/

const SearchPanel = require("web.searchPanel");
import { patch } from 'web.utils';

patch(SearchPanel.prototype, '/ks_curved_backend_theme_enter/static/src/js/ks_search_panel.js', {
    _ksSearchPanelClose(){
        $(".ks_search_panel").removeClass("show");
    }

});