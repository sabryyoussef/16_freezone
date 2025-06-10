odoo.define("ks_curved_backend_theme_enter.AbstractWebClient", function (require) {
  "use strict";

  var { WebClient } = require("@web/webclient/webclient");
  var session = require("web.session");
  var ajax = require("web.ajax");

  const { hooks } = owl;

  var { patch } = require("web.utils");
  patch(WebClient.prototype, "AbstractWebClient", {
    async setup() {
      /**
       * Set webpage title if user has selected.
       */
      this._super();
      const ksTitle = await this.env.services.rpc(
        "/ks_curved_theme/ks_get_website_title"
      );

        const manifest =  await this.env.services.rpc("/ks_curved_backend_theme_enter/get_manifest").then(
        function (result) {
          if (result){
              let encodeData = encodeURIComponent(JSON.stringify(result));
              let manifestURL = "data:application/manifest+json," + encodeData;
              let manifestElement = document.createElement("link");
              manifestElement.setAttribute("rel", "manifest");
              manifestElement.setAttribute("href", manifestURL);
              document.querySelector("head").appendChild(manifestElement);
          }
        }
      )

      if (ksTitle)
        this.title.setParts({ zopenerp: ksTitle });





//      await ajax
//        .jsonRpc({ route: "/ks_curved_backend_theme_enter/get_manifest" }).then(
//        function (result) {
//          if (result){
//              let encodeData = encodeURIComponent(JSON.stringify(result));
//              let manifestURL = "data:application/manifest+json," + encodeData;
//              let manifestElement = document.createElement("link");
//              manifestElement.setAttribute("rel", "manifest");
//              manifestElement.setAttribute("href", manifestURL);
//              document.querySelector("head").appendChild(manifestElement);
//          }
//        }
//      )
    },

    async loadRouterState() {
        if(this.router.current.hash.action_id){
            this.env.services.user.home_action_id = this.router.current.hash.action_id;
        }
        this._super(...arguments);
    },

  });
});
