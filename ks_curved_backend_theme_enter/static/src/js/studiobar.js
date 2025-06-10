/** @odoo-module **/

import { StudioNavbar } from "@web_studio/client_action/navbar/navbar";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import session from 'web.session';
const {onWillStart, useState, useRef, onMounted, onWillUnmount} = owl;

patch(StudioNavbar.prototype,"studiobar",{
 setup() {
  this._super();
   onMounted(() => {
   this._updateClassList(false);
   });
   onWillUnmount(() => {
   this._updateClassList(true);
    });

},
           _updateClassList(inHomeMenu) {
            if(inHomeMenu){
                $('body').removeClass('ks_menubar_autohide')
                $('body').removeClass('brightness')
                if ($("html").attr("data-drawer-font-style") == "dark")
                      $("html").attr("data-color-mode", "ks-dark");
                    else if ($("html").attr("data-drawer-font-style") == "light")
                      $("html").attr("data-color-mode", "ks-light");

                // Manage App drawer theme color.
                document.body.style.removeProperty("--body-background");
                document.body.style.removeProperty("--nav-link-color");
                document.body.style.removeProperty("--ks-over-link");


                $(".o_menu_systray").removeClass("ks_color_theme_dark_header");
                if(document.querySelector('.ks-menu-systray')){
                    document.querySelector('.ks-menu-systray').classList.remove('ks_color_theme_dark_header')
                }
                $('.o_main_navbar button.phone-menu-btn').removeClass("ks_color_theme_dark_header");
                $('.ks_left_sidebar_panel .ks_app_sidebar .inner-sidebar button.phone-menu-btn').removeClass("ks_color_theme_dark_header");
            }
            else{
                 $("html").attr("data-color-mode", session.ks_current_color_mode);
                 $('body').addClass('brightness')
                 if(session.ks_curved_backend_theme_enter_data && session.ks_curved_backend_theme_enter_data.ks_menubar_autohide)
                  $('body').addClass('ks_menubar_autohide')
                if (session.ks_current_color_mode == "ks-light") {
                  // Apply Color theme back.
                  document.body.style.setProperty(
                    "--body-background",
                    session.ks_color_theme["body-background"]
                  );

                  document.body.style.setProperty(
                    "--nav-link-color",
                    session.ks_color_theme["nav-link-color"]
                  );

                  document.body.style.setProperty(
                    "--ks-over-link",
                    session.ks_color_theme["ks-over-link"]
                  );
                }

                if (session.ks_color_theme.ks_header_icon_clr) {
                  $(".o_menu_systray").addClass("ks_color_theme_dark_header");
                  $('.o_main_navbar button.phone-menu-btn').addClass("ks_color_theme_dark_header");
                  $('.ks_left_sidebar_panel .ks_app_sidebar .inner-sidebar button.phone-menu-btn').addClass("ks_color_theme_dark_header");
                }
            }

        },


});