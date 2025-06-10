odoo.define("ks_curved_backend_theme_enter.ks_appsmenu", function (require) {
  "use strict";

  var session = require("web.session");
  var config = require("web.config");
  var core = require("web.core");
  var QWeb = core.qweb;
//    var { NavBar } = require("@web/webclient/navbar/navbar");
    var { EnterpriseNavBar } =  require("@web_enterprise/webclient/navbar/navbar");
  var { patch } = require("web.utils");
  const { useListener } = require("@web/core/utils/hooks");
  var { onWillStart,onWillPatch } = owl;
  var ksAppSidebar = require("ks_curved_backend_theme_enter.ks_app_sidebar");
  const ajax = require("web.ajax");

  function ks_GetReducedMenuData(memo, menu) {
    if (menu.actionID) {
      var key = menu.ks_parent_name ? menu.ks_parent_name : "";
      menu["ks_title"] = (key + menu.name).toLowerCase();
      memo[key + menu.name] = menu;
    }
    if (menu.children.length) {
      var child_menus = this.menuService.getMenuAsTree(menu.id).childrenTree;
      child_menus.forEach((child_menu) => {
        child_menu["ks_parent_id"] = menu.id;
        if (menu["ks_parent_name"]) {
          child_menu["ks_parent_name"] =
            menu["ks_parent_name"] + "/" + menu.name;
        } else {
          child_menu["ks_parent_name"] = menu.name;
        }
      });
      _.reduce(child_menus, ks_GetReducedMenuData.bind(this), memo);
    }
    return memo;
  }

  // todo: Resolve the commented code inside the patch (make compatible with v15)

  patch(EnterpriseNavBar.prototype, "ks_curved_backend_theme_enter.ks_appsmenu", {
    setup() {
      this._super();
//
//      useListener("shown.bs.dropdown", this._ksSearchFocus);
//      useListener("hidden.bs.dropdown", this._ksSearchResetvalues);
//      useListener("hide.bs.dropdown", this._ksHideAppsMenuList);

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
      this.props["ks_user_id"] = session.uid;
      this.props["ks_user_name"] = message + session.name;
      this._ks_fuzzysearchableMenus = _.reduce(
        this.menuService.getApps(),
        ks_GetReducedMenuData.bind(this),
        {}
      );
      onWillStart(async () => {
                await this.willStart()
      });
    },

    willStart: async function () {
      var apps = this.menuService.getApps();
      var ks_fav_apps = false;
      var data = false;

      await ajax
        .jsonRpc("/ks_app_frequency/render", "call", {})
        .then(function (app_frequency) {
          data = app_frequency;
        });
      await ajax
        .jsonRpc("/ks_curved_theme/get_fav_icons", "call", {
          ks_app_icons: apps,
        })
        .then(function (data) {
          ks_fav_apps = data;
        });

      this.apps = ks_fav_apps;
      this.ks_fav_apps = ks_fav_apps;
      this.props["_ks_frequent_apps"] = [];

      data.forEach((item, index) => {
        var frequent_app = apps.filter((app) => {
          if (app.id == item) return app;
        });
        this.props._ks_frequent_apps.push(frequent_app[0]);
      });

    },

//    mounted: function () {
//      this.$search_container = $(this.el).find(".ks_menu_search");
//      this.$search_input = $(this.el).find(".ks_menu_search_box input");
//      this.$search_results = $(this.el).find(".ks-search-values");
//      return this._super.apply(this, arguments);
//    },

    /**
     * To split the object into chunks of 12
     * @returns {Object[]}
     */
    _getSplittedApps: function () {
      var apps = this.ks_fav_apps;
      var i,
        j,
        app_list = [],
        chunk = 12;
      for (i = 0, j = apps.length; i < j; i += chunk) {
        app_list.push(apps.slice(i, i + chunk));
      }
      return app_list;
    },

    /**
     * To get frequent apps of current user
     * @returns {Object[]}
     */
    _getFrequentApps: function () {
      return this.props["_ks_frequent_apps"];
    },

    _ksHideFavIcons: function (ev) {
      ev.preventDefault();
      var self = this;
      document.body.classList.remove("ks_appsmenu_edit");

      $("div.ks_appdrawer_inner_app_div")
        .find("span.ks_fav_icon")
        .addClass("d-none");
      $("div.ks_appdrawer_div")
        .find("div.ks-app-drawer-close")
        .addClass("d-none");
    },

    //--------------------------------------------------------------------------
    // Searching
    //--------------------------------------------------------------------------
    // FixMe: Optimize the code and correct Naming (Copied)

    _ksSearchFocus: function () {
      // ToDo: Only for mobile, check its usage
      if (!config.device.isMobile) {
        this.$search_input.focus();
      }
    },

    _ksSearchMenuListTime: function () {
      this._ks_search_def = new Promise((resolve) => {
        setTimeout(resolve, 50);
      });
      this._ks_search_def.then(this._ksSearchMenusList.bind(this));
    },

    _ksSearchResetvalues: function () {
      this.$search_container.removeClass("ks-find-values");
      this.$search_results.empty();
      this.$search_input.val("");
    },

    _ksSearchMenusList: function () {
      var query = this.$search_input.val();
      if (query === "") {
        this.$search_container.removeClass("ks-find-values");
        this.$search_results.empty();
        return;
      }
      query = query.toLowerCase();
      var _newdata_app = _.filter(
        this._ks_fuzzysearchableMenus,
        function (menu) {
          return (
            menu.ks_title && !menu.ks_parent_id && menu.ks_title.includes(query)
          );
        }
      );
      var _newdata_items = _.filter(
        this._ks_fuzzysearchableMenus,
        function (menu) {
          return (
            menu.ks_title && menu.ks_parent_id && menu.ks_title.includes(query)
          );
        }
      );
      this.$search_container.toggleClass(
        "ks-find-values",
        Boolean(_newdata_app.length + _newdata_items.length)
      );
      this.$search_results.html(
        QWeb.render("ks_curved_backend_theme_enter.ks_search_menu_items", {
          ks_menu_items: _newdata_items,
          ks_menu_app: _newdata_app,
        })
      );
    },

    _ksSearchValuesSelecter: function (ev) {
      document.body.classList.toggle("o_home_menu_background");
      if (document.body.classList.contains("o_home_menu_background")) {
        document.body.classList.remove("brightness");
        this._ksManagerDrawer("open")
      } else {
        document.body.classList.add("brightness");
        this._ksManagerDrawer("close")
      }
      //      }, 2000);
    },

    _ksSearchValuesMovement: function (ev) {
      var all = this.$search_results.find(".ks-menu-search-value"),
        pre_focused = all.filter(".active") || $(all[0]);
      var offset = all.index(pre_focused),
        key = ev.key;
      if (!all.length) {
        return;
      }
      if (key === "Tab") {
        ev.preventDefault();
        key = ev.shiftKey ? "ArrowUp" : "ArrowDown";
      }
      switch (key) {
        case "Enter":
          pre_focused.click();
          break;
        case "ArrowUp":
          offset--;
          break;
        case "ArrowDown":
          offset++;
          break;
        default:
          return;
      }
      if (offset < 0) {
        offset = all.length + offset;
      } else if (offset >= all.length) {
        offset -= all.length;
      }

      const new_focused = $(all[offset]);
      pre_focused.removeClass("active");
      new_focused.addClass("active");
      this.$search_results.scrollTo(new_focused, {
        offset: {
          top: this.$search_results.height() * -0.5,
        },
      });
    },

    _ksHideAppsMenuList: function (ev) {
      return !this.$("input").is(":focus");
    },

    _ksManageFavApps: function (ev) {
      if ($(ev.currentTarget).hasClass("ks_add_fav")) this._ksAddFavApps(ev);
      else this._ksRemoveFavApps(ev);
    },

    _ksAddFavApps: async function (ev) {
      ev.preventDefault();
      var ks_current_target = $(ev.currentTarget);
      let result = await this.env.services.rpc(
        "/ks_curved_theme/set_fav_icons",
        {
          ks_app_id:
            ev.currentTarget.previousElementSibling.getAttribute(
              "data-menu-id"
            ),
        }
      );
      if (result) {
        // this.trigger("ks_update_fav_icon");
        this.ks_update_fav_icon();
        this._ksRemFromFav(ev, ks_current_target);
      }
    },

    _ksRemoveFavApps: async function (ev) {
      ev.preventDefault();
      var ks_current_target = $(ev.currentTarget);
      const result = await this.env.services.rpc(
        "/ks_curved_theme/rmv_fav_icons",
        {
          ks_app_id:
            ev.currentTarget.previousElementSibling.getAttribute(
              "data-menu-id"
            ),
        }
      );
      if (result) {
        // this.trigger("ks_update_fav_icon");
        this.ks_update_fav_icon();
        this._ksAddToFav(ev, ks_current_target);
      }
    },

    ks_update_fav_icon: function () {
      this._appsBar = new ksAppSidebar(this, this.menuService.getApps());
      this.$menu_apps_sidebar = $(".ks_left_sidebar_panel").find(
        ".inner-sidebar"
      );
      $("div.ks_favt_apps").remove();
      this._appsBar.prependTo(this.$menu_apps_sidebar);
    },

    _ksAddToFav: function (ev, ks_current_target) {
      // Change Class.
      $(ks_current_target).removeClass("ks_rmv_fav");
      $(ks_current_target).addClass("ks_add_fav");

      // Change icon
      $(ks_current_target)
        .find("img")
        .attr("src", "ks_curved_backend_theme_enter/static/src/images/star.svg");

      // Deactive app
      // $(ev.currentTarget.parentElement).removeClass('ks_add_visible');
    },

    _ksRemFromFav: function (ev, ks_current_target) {
      // Change Class.
      $(ks_current_target).removeClass("ks_add_fav");
      $(ks_current_target).addClass("ks_rmv_fav");

      // Change icon
      $(ks_current_target)
        .find("img")
        .attr("src", "ks_curved_backend_theme_enter/static/src/images/fav_ic.svg");

    },

      /**
     * Open the first app in the list of apps
     */


    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Called when clicking on an item in the apps menu
     * To hide the App drawer on clicking apps
     * @override
     * @param {MouseEvent} ev
     */
    _onKsAppsMenuItemClicked: function (ev) {
      document.body.classList.toggle("o_home_menu_background");
      if (document.body.classList.contains("o_home_menu_background")) {
        document.body.classList.remove("brightness");
        this._ksManagerDrawer("open")
      } else {
        document.body.classList.add("brightness");
        this._ksManagerDrawer("close")
      }
    },
    //
    //        /**
    //         * @private
    //         * @param {Object} app
    //         */
    //        _setActiveApp: function(app) {
    //            var $oldActiveApp = this.$(".o_app.active");
    //            $oldActiveApp.removeClass("active");
    //            var $newActiveApp = this.$(
    //                '.o_app[data-action-id="' + app.actionID + '"]'
    //            );
    //            //Do not set active on frequent apps menu
    //            //$newActiveApp.addClass('active');
    //        },

    /**
     * @override this method to update the app frequency counter.
     */
//    render: function(){
//      this._super();
//      if (this.menuService.getCurrentApp()){
//        let ks_update_app = ajax
//          .jsonRpc("/ks_app_frequency/update", "call", {
//            menu_id: this.menuService.getCurrentApp().id,
//          });
//      }
//    }
  });
});
