odoo.define("ks_curved_backend_theme_enter.ks_form_renderer", function (require) {
  "use strict";

  var FormRenderer = require("web.FormRenderer");
  var session = require("web.session");

  var Ks_FormRenderer = FormRenderer.include({
    // FixMe: Remove before in case of no events
//    events: _.extend({}, FormRenderer.prototype.events, {
//        'click tbody tr': '_onRowClicked',
//    }),
    /**
     * @override
     * To bind this with ks_form_resize
     */
    init: function () {
      this._super.apply(this, arguments);
      this.ks_from_resize = _.debounce(this.ks_from_resize.bind(this), 200);
    },
    /**
     * @override
     */
    start() {
      window.addEventListener("resize", this.ks_from_resize);
      return this._super(...arguments);
    },
    /**
     * @override
     */
     _renderView: function() {
        var rec = this._super.apply(this, arguments);
        if (session['ks_split_view'] == 'vertical' || session['ks_split_view'] == 'horizontal') {
            $('.o_view_controller').find('.o_cp_action_menus').addClass('d-none');
            if (this.__parentedParent && this.__parentedParent.ControlPanel && this.__parentedParent.ControlPanel.props) {
                this.__parentedParent.ControlPanel.props.cp_content = {}
                this.__parentedParent.ControlPanel.props.actionMenus = {}
                this.__parentedParent.controlPanelProps.view.toolbar = {}
                this.__parentedParent.archiveEnabled = false
            }
        }
        return rec

    },
    destroy() {
      window.removeEventListener("resize", this.ks_from_resize);
      return this._super(...arguments);
    },
    /**
     * @override
     */
    _applyFormSizeClass: function () {
      this.ks_from_resize();
      return this._super(...arguments);
    },
    /**
     * ## Already Handled in ENTERPRISE
     * To add and remove classes for chatter position
     */
    ks_from_resize() {
      if (
        window.matchMedia("(min-width: 1400px)").matches &&
        this?.$el[0].classList.contains("o_form_view")
      )
        this?.$el[0].classList.add("ks_large_screen");
      else if (this?.$el[0].classList.contains("ks_large_screen"))
        this?.$el[0].classList.remove("ks_large_screen");
    },

//      _onRowClicked: function(ev) {
//          var id = $(ev.currentTarget).data('id');
//                if (id) {
//                    this.trigger_up('open_record', { id: id, target: ev.target });
//                }
//        // Created this event to stop triggering of list view row click event when form view is appended in list view.
//        ev.stopPropagation();
//      },

  });


  return Ks_FormRenderer;
});
