/** @odoo-module **/

var core = require("web.core");
var _t = core._t;
var ajax = require("web.ajax");
const config = require("web.config");
var session = require("web.session");

const ControlPanel = require('web.ControlPanel');
import { patch } from 'web.utils';
const components = { ControlPanel };

patch(components.ControlPanel.prototype, '@ks_curved_backend_theme_enter/js/ks_fullscreen.js', {

    setup() {
        this._super();
        this.props['split_view'] = session['ks_split_view'];
        this.display = {
            'bottom_right' : this.props.view ? !this.props.view.isKsSplitFormView : true,
        }
    },

    _onksSplit(ev) {
        ev.preventDefault();
        ajax.jsonRpc("/ks_curved_backend_theme_enter/save/split_data", "call", {
            val: $(ev.currentTarget).data('value')
        }).then(function(res) {
            var url = location.href
//            session.ks_split_view = $(ev.currentTarget).data('value')
            window.location.replace(url.replaceAll('view_type=form','view_type=list'));
            location.reload();
        });
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Called from xml template ks
     */
    _onksFullScreen(ev) {
        var ks_window = document.documentElement;
        var ks_elem_class = ev.currentTarget.classList;
        if (window.innerHeight == screen.height) {
            if ($("button.ks_fullscreen").hasClass("fa-expand")) {
                alert(_t("Browser is in fullscreen mode."));
            } else {
                try {
                    ks_elem_class.remove("fa-compress");
                    ks_elem_class.add("fa-expand");
                    if (document.exitFullscreen) {
                        document.exitFullscreen();
                    } else if (document.webkitExitFullscreen) {
                        /* Safari */
                        document.webkitExitFullscreen();
                    } else if (document.msExitFullscreen) {
                        /* IE11 */
                        document.msExitFullscreen();
                    }
                } catch (err) {
                    alert(_t("Unable to perform this operation."));
                }
            }
        }

        else if (window.innerHeight < screen.height && ($("button.ks_fullscreen").hasClass("fa-compress"))) {
               try {
                    ks_elem_class.remove("fa-compress");
                    ks_elem_class.add("fa-expand");
                    if (document.exitFullscreen) {
                        document.exitFullscreen();
                    } else if (document.webkitExitFullscreen) {
                        /* Safari */
                        document.webkitExitFullscreen();
                    } else if (document.msExitFullscreen) {
                        /* IE11 */
                        document.msExitFullscreen();
                    }
                } catch (err) {
                    alert(_t("Unable to perform this operation."));
                }

        }

        else if (window.innerHeight > screen.height && ($("button.ks_fullscreen").hasClass("fa-compress"))) {
               try {
                    ks_elem_class.remove("fa-compress");
                    ks_elem_class.add("fa-expand");
                    if (document.exitFullscreen) {
                        document.exitFullscreen();
                    } else if (document.webkitExitFullscreen) {
                        /* Safari */
                        document.webkitExitFullscreen();
                    } else if (document.msExitFullscreen) {
                        /* IE11 */
                        document.msExitFullscreen();
                    }
                } catch (err) {
                    alert(_t("Unable to perform this operation."));
                }

         }
        else {
            ks_elem_class.remove("fa-expand");
            ks_elem_class.add("fa-compress");
            if (ks_window.requestFullscreen) {
                ks_window.requestFullscreen();
            } else if (ks_window.webkitRequestFullscreen) {
                /* Safari */
                ks_window.webkitRequestFullscreen();
            } else if (ks_window.msRequestFullscreen) {
                /* IE11 */
                ks_window.msRequestFullscreen();
            }
        }

        document.addEventListener("fullscreenchange", (event)=>{
            if (document.fullscreenElement) {
                $("button.ks_fullscreen").removeClass("fa-expand");
                $("button.ks_fullscreen").addClass("fa-compress");
            } else {
                $("button.ks_fullscreen").removeClass("fa-compress");
                $("button.ks_fullscreen").addClass("fa-expand");
            }
        });
    },

    /*
     * To add FontAwesome class conditionally
     */
    _ksScreenStatus() {
        var ks_status = "Compressed";
        if (window.innerHeight == screen.height)
            ks_status = "Expanded";
        return ks_status;
    },

    _ksMobileViewSwitcher() {
        $(".o_cp_switch_buttons").toggleClass("show");
    },

    _ksSearchPanelOpen() {
           $('.o_search_panel').toggle();
           if($('.o_search_panel').is(":visible")){
                $('button.ks-phone-category-btn i').removeClass('fa-filter');
                $('button.ks-phone-category-btn i').addClass('fa-arrow-left');
            }else{
            $('button.ks-phone-category-btn i').removeClass('fa-arrow-left');
                $('button.ks-phone-category-btn i').addClass('fa-filter');
                }
          // $('.o_search_panel').toggleClass('');

      //  $(".ks_search_panel").addClass("show");
//        $(".ks_search_panel").removeClass("none");
    },

    _ksActiveSearchFilter() {
        var ks_all_sections = this.model.get("sections");
        var ks_result = [];
        if (ks_all_sections) {
            ks_all_sections.forEach((element,index)=>{
                if (element.type == "filter") {
                    var ks_display = false
                    element.values.forEach((values,index)=>{
                        if (values.checked) {
                            if (!ks_display)
                                ks_display = values.display_name;
                            else
                                ks_display += ', ' + values.display_name;
                        }
                    }
                    );
                    if (ks_display) {
                        ks_result.push({
                            icon: element.icon,
                            display_name: ks_display,
                        });
                    }
                }
                if (element.activeValueId) {
                    let ks_active_id = element.activeValueId;
                    element.values.forEach((values,index)=>{
                        if (values.id == ks_active_id) {
                            ks_result.push({
                                icon: element.icon,
                                display_name: values.display_name,
                            });
                        }
                    }
                    );
                }
            }
            );
        }
        return ks_result;
    },

    _ksCheckMobileView() {
        if (screen.width > 1024)
            return false;
        return true;
    },

    _ksCheckSearchPanel() {
        var ks_search_data = this.model.get("sections");
        if (ks_search_data)
            return true;
        return false;
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

    _ksSearchFragmentOpen() {
        $(".ks-phone-filter-modal").addClass("show");
        $('div.ks-item-search-box').removeClass("d-none");
    },

    _ksSearchFragmentClose() {
        $(".ks-phone-filter-modal").removeClass("show");
        $('div.ks-item-search-box').addClass("d-none");
    },

    _ksSearchReset() {
        this.model.dispatch("clearQuery");
    },

    _ksViewSwitcher(ev) {
        $(".o_cp_switch_buttons").removeClass("show");
        this.trigger("switch-view", {
            view_type: $(ev.currentTarget).attr("ksView"),
        });
    },
});
