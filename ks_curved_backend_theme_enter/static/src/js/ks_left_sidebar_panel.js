odoo.define(
  "ks_curved_backend_theme_enter.ks_left_sidebar_panel",
  function (require) {
    "use strict";

    var config = require("web.config");
    // To check the device

//    var { NavBar } = require("@web/webclient/navbar/navbar");
    var { EnterpriseNavBar } =  require("@web_enterprise/webclient/navbar/navbar");
    var SystrayMenu = require("web.SystrayMenu");
    var dom = require("web.dom");
    var session = require("web.session");
    var UserMenu = require("@web/webclient/user_menu/user_menu");
//import { menuService } from "@web/webclient/menus/menu_service";
//    var { MenusService } = require("@web/webclient/menus/menu_service");
    var ksAppSidebar = require("ks_curved_backend_theme_enter.ks_app_sidebar");
    var ksBookmarks = require("ks_curved_backend_theme_enter.ks_bookmarks");
    var core = require("web.core");
    var QWeb = core.qweb;
    var { patch } = require("web.utils");
    const { useListener } = require("@web/core/utils/hooks");
    var ajax = require("web.ajax");
    var config = require('web.config');

    const { hooks, onWillStart, onMounted, useRef, onWillPatch } = owl;
    // Handle rpc calls.
    var { useService } = require("@web/core/utils/hooks");

    // todo: Patch the remaining methods from the below commented code
    patch(EnterpriseNavBar.prototype, "ks_left_sidebar_panel", {
      async setup(parent, menuData) {
        this._super();
        this.parent = parent;
        this._apps = menuData;
        this.rpc = useService("rpc");
//        useListener("click", "#dropdown", this._ksAppsDrawerClick);
//        useListener("click", "button.phone-menu-btn", this._ksOpenMobileDrawer);
//        useListener("click", "a[data-section]", this._ksSubMenu);
//        useListener("ks_manage_drawer", this._ksManagerDrawer);
//        useListener( "click", ".ks_menusections li .dropdown-menu a", this._ksCloseMobileDrawer);
//        useListener( "click", ".ks_menusections li a[data-action-id]", this._ksCloseMobileDrawer);
//        useListener( "DOMMouseScroll", "#AllApps", this._onPageScroll); // Firefox
//        useListener( "mousewheel", "#AllApps", this._onPageScroll); // Chrome, Safari, IE
        this._ksBookmarks();
        onWillStart(async () => {
            await this.willStart()
      });
      onWillPatch(() => this.willpatch());
      onMounted(() => this._ksUpdateFavIcon());

      },

      async willStart() {
        let self = this;
        const _super = this._super.bind(this, ...arguments);
        let ks_data = await ajax.jsonRpc("/web/dataset/call", "call", {
          model: "ks.global.config",
          method: "ks_get_value_from_scope",
          args: [
            [
              "ks_menu_bar",
              "ks_favorite_bar",
              "ks_company_logo",
              "ks_favtbar_autohide",
              "ks_favtbar_position",
              "ks_show_app_name",
              "ks_user_menu_placement",
              "ks_menubar_autohide",
              "ks_small_company_logo",
            ],
          ],
        });

        // Add menu bar info.
        this.init_menu_data(ks_data);


        if (this.ks_menu_bar == "Vertical")
          document.body.classList.add("ks_vertical_body_panel");

        if (
          self.ks_favtbar_autohide &&
          self.ks_favorite_bar &&
          self.ks_menu_bar == "Horizontal"
        )
          document.body.classList.add("ks_favtbar_autohide");

        if (self.ks_menubar_autohide && screen.width > 1024)
          document.body.classList.add("ks_menubar_autohide");
        if (
          self.ks_favtbar_position == "Bottom" &&
          self.ks_menu_bar == "Horizontal"
        )
          document.body.classList.add("ks_favtbar_bottom");

//        if (
//          self.ks_user_menu_placement == "Top" &&
//          self.ks_menu_bar == "Vertical"
//        )
//        {
//          document.body.classList.add("ks_user_menu_top");
//          let child = document.querySelector(".o_user_menu");
//            let parent = document.querySelector(".inner-sidebar");
//
//            parent.appendChild(child);
//        }
        if (!self.ks_show_app_name && self.ks_favorite_bar)
          document.body.classList.add("ks_hide_app_names");

        if (self.ks_menu_bar == "Horizontal" && !self.ks_favorite_bar)
          document.body.classList.add("ks_hide_leftpanel");

          return _super();

      },

      // mounted() {
      willpatch() {
      if (!config.device.isMobile){
        if(document.querySelector('.o_mobile_menu_toggle')!=null){
            document.querySelector('.o_mobile_menu_toggle').parentElement.classList.add("d-none")
        }
        }

        if(document.querySelector('#AllApps')!=null){
            document.querySelector('#AllApps').addEventListener("DOMMouseScroll",this._onPageScroll)
            document.querySelector('#AllApps').addEventListener("mousewheel",this._onPageScroll)
        }
        var self = this;
        this.$menu_apps = $(".o_menu_apps");
        var base_url = session['web.base.url'];
        var logout_url='<a href='+ base_url+"/web/session/logout "+ 'class="dropdown-item focus" data-menu="logout">Log out</a>'

        if (this.ks_menu_bar == "Horizontal") {
          this.$menu_brand_placeholder = $(".o_menu_brand");
          this.$section_placeholder = $(".o_menu_sections");

          // Remove my-profile and logout buttons for horizontal menu bar on mobile.
          var ks_my_profile = $(".ks_user_action_horizontal").find('a[data-menu="settings"]').remove();
          var ks_logout = $(".ks_user_action_horizontal").find('a[data-menu="logout"]').remove();

          // Add buttons on mobile left navigation.
          if ($('.ks_mobile_nav_bottom').length ===0) {
            $("div.ks-phone-profile").after('<div class="ks_mobile_nav_bottom">'+logout_url+'</div>');
          }
//          $("div.ks_mobile_nav_bottom").append(ks_my_profile);
//          $("div.ks_mobile_nav_bottom").append(ks_logout);
//          $("nav.o_main_navbar .ks-phone-side-menu").on("click",".ks-phone-menu-list .ks_mobile_nav_bottom a[data-menu]",
//            function (ev) {
//              ev.preventDefault();
//              var menu = $(this).data("menu");
//              self.ksMobileUserMenu[
//                "_onMenu" + menu.charAt(0).toUpperCase() + menu.slice(1)
//              ]();
//              self._ksCloseMobileDrawer();
//            }
//          );
        }
        else if (this.ks_menu_bar == "Vertical") {

          if (self.ks_user_menu_placement == "Top")
            {
              document.body.classList.add("ks_user_menu_top");
              let user_button = document.querySelector(".o_user_menu");
              let inner_sidebar = document.querySelector(".inner-sidebar");
              inner_sidebar.appendChild(user_button);
            }

//        let child = document.querySelector(".o_user_menu");
//        let parent = document.querySelector(".inner-sidebar");
//
//        parent.appendChild(child);

          this.$menu_brand_placeholder =
            $(".ks_vertical_menus").find(".o_menu_brand");

          this.$section_placeholder =
            $(".ks_vertical_menus").find(".o_menu_sections");

          this.$menu_icon = $(".ks_vertical_menus").find(
            ".ks_vertical_app_icon"
          );

          // Side bar app menu for vertical menubar.
          if (this.currentApp && this.currentApp.webIconData) {
            this.$menu_icon.attr({
              alt: this.currentApp.name,
              title: this.currentApp.name,
              src: this.currentApp.webIconData,
            });

            $(".ks_menubrand").text(this.currentApp.name);
            $(".ks_menubrand").attr('href', '#menu_id='+this.currentApp.appID);
          }


          // Vertical app menu drawer open.
//          $("div.ks_left_sidebar_panel .ks_app_sidebar .inner-sidebar").on("click","button.phone-menu-btn",
//            self._ksOpenMobileDrawer.bind(self)
//          );

          // Vertical app menu drawer close.
//          $("div.ks_left_sidebar_panel .ks_app_sidebar .inner-sidebar").on("click","div.overlay",
//            self._ksCloseMobileDrawer.bind(self)
//          );

          // Vertical menu binding
//          $("div.ks_left_sidebar_panel .ks_app_sidebar .inner-sidebar").on("click", "a[data-menu]", self._ksMobileDrawerMenu.bind(self));

          // Vertical user data append and binding.
          // var ks_user_action = QWeb.render("UserMenu.Actions");
          // $("div.ks_user_action").html(ks_user_action);

          // Remove my-profile and logout buttons for vertical menu bar on mobile.
          var ks_my_profile = $(".ks_user_action").find('a[data-menu="settings"]').remove();
          var ks_logout = $(".ks_user_action").find('a[data-menu="logout"]').remove();

          // Add buttons on mobile left navigation.
          $("div.ks-phone-profile").after('<div class="ks_mobile_nav_bottom">'+logout_url+'</div>');
//          $("div.ks_mobile_nav_bottom").append(ks_my_profile);
//          $("div.ks_mobile_nav_bottom").append(ks_logout);

          // Handle menu of user action
//          $("div.ks_left_sidebar_panel .ks_app_sidebar .inner-sidebar").on("click",".ks-phone-menu-list .ks-phone-profile a[data-menu]",
//            function (ev) {
//              ev.preventDefault();
//              var menu = $(this).data("menu");
//              self.ksMobileUserMenu[
//                "_onMenu" + menu.charAt(0).toUpperCase() + menu.slice(1)
//              ]();
//              self._ksCloseMobileDrawer();
//            }
//          );

          // Handle my profile and logout button
//          $("div.ks_left_sidebar_panel .ks_app_sidebar .inner-sidebar").on("click",".ks-phone-menu-list .ks_mobile_nav_bottom a[data-menu]",
//            function (ev) {
//              ev.preventDefault();
//              var menu = $(this).data("menu");
//              self.ksMobileUserMenu[
//                "_onMenu" + menu.charAt(0).toUpperCase() + menu.slice(1)
//              ]();
//              self._ksCloseMobileDrawer();
//            }
//          );


        }


        this.$right_sidebar = $(".ks_right_sidebar_panel");

        // Navbar's menus event handlers
//        var on_secondary_menu_click = function (ev) {
//          ev.preventDefault();
//          var menu_id = $(ev.currentTarget).data("menu");
//          var action_id = $(ev.currentTarget).data("action-id");
//           self._on_secondary_menu_click(menu_id, action_id);
//        };
//        var menu_ids = _.keys(this.currentAppSections);
//        var primary_menu_id, $section, secon_menu;
//        for (var i = 0; i < menu_ids.length; i++) {
//          primary_menu_id = menu_ids[i];
//          $section = this.currentAppSections[primary_menu_id]["childrenTree"];
//          for (var i = 0; i < $section.length; i++) {
//            secon_menu = $section[i];
//            $(".dropdown-item").text(secon_menu.name);
//            $(".dropdown-item").attr('href', '#menu_id='+secon_menu.appID & secon_menu.actionID);
//          }
//          $section.on(
//            "click",
//            "a[data-menu]",
//            self,
//            on_secondary_menu_click.bind(this)
//            );
//          }
    if (this.currentApp && this.ks_menu_bar=="Horizontal" && this.currentApp.name=="Website"){
          $(".o_menu_brand").addClass("d-none")
          }
          else{
           $(".o_menu_brand").removeClass("d-none")
          }
    if (this.currentApp && this.currentApp.name=="Discuss"){
    $(".ks-zoom-view").addClass("d-none");
    $(".ks-bookmark-auto").addClass("d-none")
    $(".bookmarks-toggle").addClass("d-none")
    }else{
    $(".ks-zoom-view").removeClass("d-none")
    $(".ks-bookmark-auto").removeClass("d-none")
    $(".bookmarks-toggle").removeClass("d-none")
    }
        this._ksUpdateFavIcon();
        this.fav_app_rendered = true;
      // Apps Menu
        let tabContent = document.querySelectorAll(".tabContent .item");
        let ksTabs = document.querySelectorAll(".ks-tabs li");
        ksTabs.forEach((el, i) => {
          el.addEventListener("click", () => {
            ksTabs.forEach((rm) => {
              rm.classList.remove("active");
            });
            el.classList.add("active");
            tabContent.forEach((tabCont) => {
              tabCont.classList.remove("active");
            });
            tabContent[i].classList.add("active");
          });
        });

      },

//      get systrayItems() {
//          const systray = this._super.apply(this, arguments);
//        return systray
//      },

      _ksOpenMobileDrawer: function () {
        // Append user's info
            var ks_user_name = session['name'];
            var ks_user_img_src = $('.o_menu_systray div.o_user_menu img')[0].src;
            if (ks_user_name) {
              $("div.ks-phone-profile .ks_user_name").text(ks_user_name);
            }
            if (ks_user_img_src) {
              $("div.ks-phone-profile .ks-user-profile-img img").attr(
                "src",
                ks_user_img_src
              );
            }

            if ($("div.ks-phone-side-menu").length){
              $("div.ks-phone-side-menu").addClass("active-menu");
              if((this.ks_menu_bar=='Vertical') &&($("ul.ks_menusections").length))
                $("div.ks-phone-profile").after($("ul.ks_menusections")[0].outerHTML);
              setTimeout(() => {
                $("div.ks-phone-menu-list").addClass("menu-show");
              }, 200);
            }
      },

      _ksCloseMobileDrawer: function () {
        if ($("div.ks-phone-menu-list").hasClass("menu-show")) {
          $("div.ks-phone-menu-list").removeClass("menu-show");
        if(this.ks_menu_bar=='Vertical')
          $("div.ks-phone-menu-list").find("ul.o_menu_sections").remove();
          setTimeout(() => {
            $("div.ks-phone-side-menu").removeClass("active-menu");
          }, 200);
        }
      },

      _ksUpdateFavIcon: function () {
//        if (this.currentApp && !this.fav_app_rendered) {
          this._appsBar = new ksAppSidebar(
            this,
            this.menuService.getApps()
          );
          this.$menu_apps_sidebar = $(".ks_left_sidebar_panel").find(
            ".inner-sidebar"
          );
          $("div.ks_favt_apps").remove();
          this._appsBar.prependTo(this.$menu_apps_sidebar);
//        }
        // Remove active app from left side bar.
        // Active app if app is present in the favorite bar.
        if (this._appsBar && this.menuService)
          this._appsBar._setActiveApp(this.menuService.getCurrentApp());
//        if (document.querySelector(".o_mobile_menu_toggle")){
//        $(document.querySelector(".o_mobile_menu_toggle").parentElement).addClass("d-none");
//        }
        $(".o_menu_systray").removeClass("ks_color_theme_dark_header");
        if(document.querySelector('.ks-menu-systray')){
        document.querySelector('.ks-menu-systray').classList.remove('ks_color_theme_dark_header')
        }
        $('.o_main_navbar button.phone-menu-btn').removeClass("ks_color_theme_dark_header");
        $('.ks_left_sidebar_panel .ks_app_sidebar .inner-sidebar button.phone-menu-btn').removeClass("ks_color_theme_dark_header");
      },

      init_menu_data(ks_data) {
        this.ks_menu_bar = ks_data.ks_menu_bar;
        this.ks_favorite_bar = ks_data.ks_favorite_bar;
        this.ks_favtbar_autohide = ks_data.ks_favtbar_autohide;
        this.ks_menubar_autohide = ks_data.ks_menubar_autohide;
        this.ks_favtbar_position = ks_data.ks_favtbar_position;
        this.ks_company_logo = ks_data.ks_company_logo;
        this.ks_show_app_name = ks_data.ks_show_app_name;
        this.ks_user_menu_placement = ks_data.ks_user_menu_placement;
        this.ks_small_company_logo = ks_data.ks_small_company_logo;
      },

      _ksBookmarks() {
        this.$right_sidebar = $(".ks_right_sidebar_panel");
        this._bookmark_bar = new ksBookmarks();
        this._bookmark_bar.appendTo(this.$right_sidebar);
      },


      _ksSubMenu(event) {
        var dataset = event.target || (event.originalEvent && (event.originalEvent.target || event.originalEvent.originalTarget)) || event.srcElement;
          this.menuService.selectMenu(Number(dataset.dataset.section));
                },

      _onPageScroll: function (event) {

        event.preventDefault();
        // scroll down
        if (event.deltaY > 0 && event.deltaY < 110 && $('#AllApps').hasClass('active')){
           if ($('.ks-tabs li.active').next().length > 0){
              var li = $('.ks-tabs li.active').next();
              $('.ks-tabs li.active').removeClass("active");
              li.addClass("active");
              var ui = $("#AllApps > div.active");
              var mi = $("#AllApps > div.active").next();
              ui.removeClass("active");
              mi.addClass("active");
           }
        }
        // scroll up
        else if (event.deltaY < 0 && event.deltaY > -110 && $('#AllApps').hasClass('active')){
           if ($('.ks-tabs li.active').prev().length > 0){
              var li = $('.ks-tabs li.active').prev();
              $('.ks-tabs li.active').removeClass("active");
              li.addClass("active");
              var ui = $("#AllApps > div.active");
              var mi = $("#AllApps > div.active").prev();
              ui.removeClass("active");
              mi.addClass("active");
           }
        }
      },

      /**
       * Show & hide app drawer
       *
       * @private
       * @param {MouseEvent} event
       */
      _ksAppsDrawerClick(event) {
        // To prevent opening default app
        event.stopPropagation();
        event.preventDefault();
        document.body.classList.toggle("o_home_menu_background");
        if (document.body.classList.contains("o_home_menu_background")) {
          document.body.classList.remove("brightness");
          this._ksManagerDrawer("open")
        } else {
          document.body.classList.add("brightness");
          this._ksManagerDrawer("open")
        }
        var owl = $(".owl-carousel");
        owl.owlCarousel({
          ltr: true,
          dots: true,
          dotsEach: true,
          items: 1,
          animateIn: "fadeIn",
        });
      },

      _ksManagerDrawer(drawer_status) {
        $('#ks_input_text').focus();
        this.$search_container.removeClass("ks-find-values");
        this.$search_results.empty();
        this.$search_input.val("");
        if (drawer_status) {
          if (drawer_status == "open") {
            if ($("html").attr("data-drawer-font-style") == "dark")
              $("html").attr("data-color-mode", "ks-dark");
            else if ($("html").attr("data-drawer-font-style") == "light")
              $("html").attr("data-color-mode", "ks-light");

            // Manage App drawer theme color.
            document.body.style.removeProperty("--body-background");
            document.body.style.removeProperty("--nav-link-color");
            document.body.style.removeProperty("--ks-over-link");
            $("div.o_menu_systray").removeClass("ks_color_theme_dark_header");
            $(".o_main_navbar button.phone-menu-btn").removeClass(
              "ks_color_theme_dark_header"
            );
            $(
              ".ks_left_sidebar_panel .ks_app_sidebar .inner-sidebar button.phone-menu-btn"
            ).removeClass("ks_color_theme_dark_header");
          }
          if (drawer_status == "close") {
            $("html").attr("data-color-mode", session.ks_current_color_mode);

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
              $("div.o_menu_systray").addClass("ks_color_theme_dark_header");
              $(".o_main_navbar button.phone-menu-btn").addClass(
                "ks_color_theme_dark_header"
              );
              $(
                ".ks_left_sidebar_panel .ks_app_sidebar .inner-sidebar button.phone-menu-btn"
              ).addClass("ks_color_theme_dark_header");
            }
          }
        }
      },

      //@Todo: Check this function
      change_menu_section: function (primary_menu_id) {
        if (primary_menu_id && this.ks_favorite_bar)
          this._appsBar._setActiveApp(primary_menu_id);
        this._super.apply(this, arguments);
        if (primary_menu_id && this.ks_menu_bar == "Vertical") {
          var active_menu = this.menu_data.children.find(
            (x) => x.id === primary_menu_id
          );
          var $menu_icon = this.$menu_icon;
          if (active_menu) {
            $menu_icon.attr({
              alt: active_menu.name,
              title: active_menu.name,
              src: active_menu.web_icon_data,
            });
          }
        }
        // For Frequency of Apps 👇
        if (primary_menu_id) {
          this._rpc({
            route: "/ks_app_frequency/update",
            params: {
              menu_id: primary_menu_id,
            },
          });
        }

      },
      _updateMenuAppsIcon() {
        this._super();
        const menuAppsEl = this.menuAppsRef.el;
        menuAppsEl.classList.remove('fa-th');
        menuAppsEl.classList.remove("fa-chevron-left");
        if(document.querySelector('.o_studio')!== null){
            if(this.isInApp){
                document.querySelector('.ks_app_drawer_studio_arrow').classList.add('d-none');
                document.querySelector('.ks_app_drawer_studio_logo').classList.remove('d-none');
            }
            else{
                document.querySelector('.ks_app_drawer_studio_logo').classList.add('d-none');
                document.querySelector('.ks_app_drawer_studio_arrow').classList.remove('d-none');
            }
        }

    },

//      _ksMobileDrawerMenu: function (ev) {
//        var self = this;
//        ev.preventDefault();
//        var menu_id = $(ev.currentTarget).data("menu");
//        var action_id = $(ev.currentTarget).data("action-id");
//        self._on_secondary_menu_click(menu_id, action_id);
//        self._ksCloseMobileDrawer();
//      },
    });
});
