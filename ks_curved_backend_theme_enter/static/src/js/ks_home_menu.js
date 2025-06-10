odoo.define("ks_curved_backend_theme_enter.StudioHomeMenu", function (require) {
    "use strict";

//    const StudioHomeMenu = require("web_studio.StudioHomeMenu");
//    const patchMixin = require('web.patchMixin');
//    const HomeMenuPatched = patchMixin(StudioHomeMenu);

    var session = require("web.session");
    const { patch } = require('web.utils');
    const {HomeMenu} = require("@web_enterprise/webclient/home_menu/home_menu");
    var { onWillStart, onMounted, onWillUnmount } = owl;
    const ajax = require("web.ajax");
    const { useListener } = require("@web/core/utils/hooks");
    var session = require("web.session");
    var ksAppSidebar = require("ks_curved_backend_theme_enter.ks_app_sidebar");
    var { menuService } = require("@web/webclient/menus/menu_service");
    patch(HomeMenu.prototype, 'HomeMenu', {
        setup() {
            this._super();
            onWillStart(async () => {
                await this.willStart()
            });
            onMounted(() => {
                this._updateClassList(true);
            });
            onWillUnmount(() => {
                this._updateClassList(false);
            });
//            useListener("click", ".ks_close_app_drawer", this._ksHideFavIcons);
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
        willStart: async function () {
            // Get Favorite app list.
//            const ks_fav_apps = await this.env.services.rpc({
//                route: "/ks_curved_theme/get_fav_icons",
//                params: { ks_app_icons: this.props.apps },
//            });

            // Get Frequent Apps.
//            const ks_frequent_apps_prom = await this.env.services.rpc({
//                route: "/ks_app_frequency/render",
//            });
            this._ks_frequent_apps = [];
//            ks_fav_apps.forEach((app)=>{
//                if(ks_frequent_apps_prom.includes(app.id))
//                    this._ks_frequent_apps.push(app);
//            });
//            this.props.apps = ks_fav_apps;
//            this.availableApps = ks_fav_apps;
            this.ks_favorite_bar=session.ks_curved_backend_theme_enter_data.ks_favorite_bar
            this.menuService=this.menus
            var today = new Date();
            var curHr = today.getHours();
            var message = "Hi, ";
            if (curHr < 12) {
              message = "Good Morning, ";
            } else if (curHr < 18) {
               message = "Good Afternoon, ";
              } else {
                message = "Good Evening, ";
            }
            this["ks_user_id"] = session.uid;
            this["ks_user_name"] = message + session.name;
            var ks_fav_apps = false;
            var data = false;
            var apps=this.menus.getApps()
            this.availableApps=this.props.apps
            await ajax
                .jsonRpc("/ks_app_frequency/render", "call", {})
                .then(function (app_frequency) {
                  data = app_frequency;
                });
            await ajax
                .jsonRpc("/ks_curved_theme/get_fav_icons", "call", {
                  ks_app_icons: this.displayedApps,
                })
                .then(function (data) {
                  ks_fav_apps = data;
                });

            this.availableApps = ks_fav_apps;
            this.ks_fav_apps = ks_fav_apps;
            this._ks_frequent_app_ids=data
            this._ks_frequent_apps=[]

            this._ks_frequent_app_ids.forEach((item, index) => {
                var frequent_app=[]
                var frequent_app = this.availableApps.filter((app) => {
                  if (app.id == item) return app;
                });
                if (frequent_app.length !=0){
                    this._ks_frequent_apps.push(frequent_app[0]);
                }
              });
        },

        _ksHideFavIcons(ev) {
            ev.preventDefault();
            var self = this;
            document.body.classList.remove("ks_appsmenu_edit");

            $("div.ks_appdrawer_inner_app_div")
                .find("span.ks_fav_icon")
                .addClass("d-none");
            $("div.o_home_menu")
                .find("div.ks-app-drawer-close")
                .addClass("d-none");
        },

        async _onFavoriteClick(app){
            if($(event.currentTarget).hasClass('ks_add_fav')){
                // Add app to favorite app.
                event.preventDefault();
                var ev = event;
                const result = await ajax
                .jsonRpc("/ks_curved_theme/set_fav_icons", "call", {
                  ks_app_id: app.id
                })
                if (result) {
                    this._ksAddToFav(ev);
                    this.ks_update_fav_icon();
                }
            }
            else{
                // Remove app from favorite app.
                event.preventDefault();
                var ev = event;
                await ajax
                .jsonRpc("/ks_curved_theme/rmv_fav_icons", "call", {
                  ks_app_id: app.id
                })
                const result = await ajax
                .jsonRpc("/ks_curved_theme/rmv_fav_icons", "call", {
                  ks_app_id: app.id
                })
                if (result) {
                    this._ksRemFromFav(ev);
                    this.ks_update_fav_icon();
                }
            }
        },

        _ksAddToFav: function(ev) {
            // Change Class.
            $(ev.target).parent().removeClass("ks_add_fav");
            $(ev.target).parent().addClass("ks_rmv_fav");

            // Change icon
            $(ev.target).parent()
                .find("img")
                .attr("src", "ks_curved_backend_theme_enter/static/src/images/fav_ic.svg");
        },
        _onAppClick: async function(app){
            if(session.ks_current_color_mode=='ks-light'){
                if (session.ks_color_theme.ks_header_icon_clr) {
                if (document.querySelector('.o_menu_systray')){
                    document.querySelector('.o_menu_systray').classList.add('ks_color_theme_dark_header')
                    }
                    if(document.querySelector('.ks-menu-systray')){
                        document.querySelector('.ks-menu-systray').classList.add('ks_color_theme_dark_header')
                    }
                }
            }
            this._super(app);
            await ajax
                .jsonRpc("/ks_app_frequency/update", "call", {menu_id: app.id})
        },
        ks_update_fav_icon: function () {
          this._appsBar = new ksAppSidebar(this, this.menus.getApps());
          this.$menu_apps_sidebar = $(".ks_left_sidebar_panel").find(
            ".inner-sidebar"
          );
          $("div.ks_favt_apps").remove();
          this._appsBar.prependTo(this.$menu_apps_sidebar);
        },

        _ksRemFromFav: function(ev) {
            // Change Class.
            $(ev.target).parent().removeClass("ks_rmv_fav");
            $(ev.target).parent().addClass("ks_add_fav");

            // Change icon
            $(ev.target).parent()
                .find("img")
                .attr("src", "ks_curved_backend_theme_enter/static/src/images/star.svg");
        },

        _getFrequentApps: function() {
            if(this._ks_frequent_apps[0]==undefined){
                return []
            }
            return this._ks_frequent_apps;
        },
        _getFavApps: function() {
            return this.ks_fav_apps;
        },
        _updateQuery(query) {
        // Update input and search state
        this._super(query);
        this._ks_frequent_apps=[]
        this._ks_frequent_app_ids.forEach((item, index) => {
                var frequent_app = this.availableApps.filter((app) => {
                  if (app.id == item) return app;
                });
                if (frequent_app[0] != undefined) this._ks_frequent_apps.push(frequent_app[0]);
              });

    }

    });
});