/** @odoo-module */

var { SearchBar } = require("@web/search/search_bar/search_bar");
import { patch } from 'web.utils';
import Dialog from 'web.Dialog';
import core from 'web.core';
const { useListener } = require("@web/core/utils/hooks");
const _t = core._t;

patch(SearchBar.prototype, 'ks_curved_backend_theme_enter/static/src/js/Ks_searchbar.js', {

    _ksSearchFragmentOpen() {
        $(".ks-phone-filter-modal").addClass("show");
        $('div.ks-item-search-box').removeClass("d-none");
    },

    _ksSearchButtonOpen() {
        $(".ks_search_responsive").addClass("show");
        // Hide breadcrumb text and search icon.
        $(".o_cp_top_left .breadcrumb-item").addClass("d-none");
        $(".o_cp_top_right .ks-phone-sr-btn").addClass("d-none");
    },

    _ksSearchButtonClose() {
        $(".ks_search_responsive").removeClass("show");
        $(".o_cp_top_left .breadcrumb-item").removeClass("d-none");
        $(".o_cp_top_right .ks-phone-sr-btn").removeClass("d-none");
    },


});


