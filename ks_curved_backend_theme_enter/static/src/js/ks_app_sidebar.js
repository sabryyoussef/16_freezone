odoo.define("ks_curved_backend_theme_enter.ks_app_sidebar", function (require) {
  "use strict";

  var Widget = require("web.Widget");
  const ajax = require("web.ajax");

  var ksAppsBar = Widget.extend({
    template: "ks_curved_backend_theme_enter.side_appbar",
    events: _.extend({}, Widget.prototype.events, {
      "click .ks_app": "_ksAppClicked",
      "click .left_sidebar_arrow": "_ksToggleVerticalMenus",
    }),
    /**
     * @override
     * @param {web.Widget} parent
     * @param {Object} menuData
     * @param {Object[]} menuData.children
     */
    init: function (parent, menuData) {
      this._super.apply(this, arguments);
      this._activeApp = undefined;
      this._ks_fav_bar = parent.ks_favorite_bar;
      this.parent = parent;
      this._apps = menuData;
    },

    willStart: async function () {
      const _super = this._super.bind(this);
      var ks_fav_apps = [];
      await ajax
        .jsonRpc("/ks_curved_theme/get_fav_icons", "call", {
          ks_app_icons: this._apps,
        })
        .then(function (data) {
          ks_fav_apps = data;
        });
      this._apps = ks_fav_apps;
    },

    start: function () {
      var temp_this = this;
      if(this.parent.menuService.getCurrentApp()!== undefined){
        this._setActiveApp(this.parent.menuService.getCurrentApp());
      }
      return this._super.apply(this, arguments).then(function () {
        // if (
        //   !document.body.classList.contains("ks_vertical_body_panel") &&
        //   !temp_this.$el.children(".ks_app_sidebar_menu").children().length
        // ) {
        //   temp_this.$el.parents(".ks_left_sidebar_panel").addClass("d-none");
        // } else {
        //   temp_this.$el.parents(".ks_left_sidebar_panel").removeClass("d-none");
        // }
      });
    },

    /**
     * @returns {Object[]}
     */
    getApps: function () {
      return this._apps;
    },

    fav_bar_menu: function () {
      return this._ks_fav_bar;
    },
    /**
     * @private
     * @param {Object} app
     */
    _openApp: function (app) {
      this._setActiveApp(app);
      this.parent.menuService.selectMenu(app.id);
    },
    /**
     * @private
     * @param {Object} app
     */
    _setActiveApp: function (menuID) {
      if (this.$el){
        var $oldActiveApp = this.$(".ks_app.active");
        $oldActiveApp.removeClass("active");
        var $newActiveApp = this.$('.ks_app[data-menu-id="' + menuID.id + '"]');
        $newActiveApp.addClass("active");
      }
    },
    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Called when clicking on an item in the apps menu.
     *
     * @private
     * @param {MouseEvent} ev
     */
    _ksAppClicked: function (ev) {
      var $target = $(ev.currentTarget);
      var actionID = $target.data("action-id");
      var menuID = $target.data("menu-id");
      var app = _.findWhere(this._apps, {
        actionID: actionID,
        id: menuID,
      });
      this._openApp(app);
      ev.preventDefault();
      $target.blur();
    },
    _ksToggleVerticalMenus: function () {
      document.body.classList.toggle("ks_verticalmenus_expanded");
    },
  });

  return ksAppsBar;
});
