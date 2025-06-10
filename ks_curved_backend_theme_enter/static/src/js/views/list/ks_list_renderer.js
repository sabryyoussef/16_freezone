odoo.define("ks_curved_backend_theme_enter.ks_list_renderer", function (require) {
  "use strict";

  var ajax = require("web.ajax");
  var ListRenderer = require("web.ListRenderer");
  var KsListDocumentViewer = require("ks_curved_backend_theme_enter.KsListDocumentViewer");
  var core = require("web.core");
  var session = require("web.session");
  var view_registry = require("web.view_registry");
  var dom = require("web.dom");
  var _t = core._t;

  var Ks_ListRenderer = ListRenderer.include({
    events: _.extend({}, ListRenderer.prototype.events, {
      "click .ks_attachment_id": "_onksViewAttachment",
      "click tbody .ks_attachment_data": "_onksAttachmentDivClicked",
      "change input": "_onksInputChange",
    }),

     init: function (parent, model, renderer, params) {
        this._super.apply(this, arguments);
        this.list_split_mode = renderer.list_split_mode || false;
        this.split_view_data = {active: false};
    },

    // Showing preview of attachments
    _onksViewAttachment: function (ev) {
      var att_id = parseInt($(ev.currentTarget).data("id"));
      var att_mime = $(ev.currentTarget).data("mime");
      var att_name = $(ev.currentTarget).data("name");
      var rec_id = parseInt($(ev.currentTarget).data("ks-rec-id"));
      var att_data = this.ks_data;

      var match = att_mime.match("(image|video|application/pdf|text)");
      if (match) {
        var ks_attachment = [];
        att_data[rec_id].forEach((attachment) => {
          if (attachment.att_mime.match("(image|video|application/pdf|text)")) {
            ks_attachment.push({
              filename: attachment.att_name,
              id: attachment.att_id,
              is_main: false,
              mimetype: attachment.att_mime,
              name: attachment.att_name,
              type: attachment.att_mime,
              url: "/web/content/" + attachment.att_id + "?download=true",
            });
          }
        });
        var ks_activeAttachmentID = att_id;
        var ks_attachmentViewer = new KsListDocumentViewer(
          self,
          ks_attachment,
          ks_activeAttachmentID
        );
        ks_attachmentViewer.appendTo($("body"));
      } else
        this.call("notification", "notify", {
          title: _t("File Type Not Supported"),
          message: _t("This file type can not be previewed"),
          sticky: false,
        });
    },

    willStart: async function () {
      const _super = this._super.bind(this);
      var self = this;
      // getting the attachments data
      await ajax
        .jsonRpc("/ks_list_renderer/attachments", "call", {
          res_ids: this.state.res_ids,
          model: this.state.model,
          domain: this.state.domain,
        })
        .then(function (data) {
          self.ks_data = data[0];
          self.ks_list_ = data[1];
        });
      return _super(...arguments);
    },

    updateState: async function (state, params) {
        const _super = this._super.bind(this);
        var self = this;
          await ajax
            .jsonRpc("/ks_list_renderer/attachments", "call", {
              res_ids: state.res_ids,
              model: state.model,
              domain: state.domain,
            })
            .then(function (data) {
              self.ks_data = data[0];
              self.ks_list_ = data[1];
            });
        return _super.apply(this, arguments);
    },

    _renderRow: function (record) {
      var self = this;
      var ks_attachment_limit = 5;
      var $tr = this._super.apply(this, arguments);
      if (self.ks_list_["ks_list_density"] == "Comfortable")
        $tr.addClass("ks_comfortable_list");
      else if (self.ks_list_["ks_list_density"] == "Attachment") {
        var att_data = this.ks_data;
        // adding div below the row having attachments
        if (att_data[record.data.id]) {
          var $outer_div = $("<div>", {
            class: "ks_attachment_data_outer",
          });
          var $inner_div = $("<div>", {
            class: "ks_attachment_data",
            id: record.id,
          });

          att_data[record.data.id].every((attachment, index, arr) => {
            if (index < ks_attachment_limit) {
              var $att_div = $("<div>", {
                class: "ks_attachment_id",
                "data-id": attachment.att_id,
                "data-name": attachment.att_name,
                "data-mime": attachment.att_mime,
                "data-ks-rec-id": record.data.id,
              });

              // attachment mimetype for image
              $att_div = $att_div.append(
                $("<div/>", {
                  "data-mimetype": attachment.att_mime,
                  class: "o_image",
                })
              );

              // attachment name div
              var $div_att_name = $("<div>", {
                class: "ks_attachment_name",
              }).append($("<span>").html(attachment.att_name));

              $att_div = $att_div.append($div_att_name);
              //appending both mimetype and name to the inner div
              $inner_div = $inner_div.append($att_div);
              return true;
            } else {
              var $att_div = $("<div>", {
                class: "ks_attach_counter ks_attachment_id",
                "data-id": attachment.att_id,
                "data-name": attachment.att_name,
                "data-mime": attachment.att_mime,
                "data-ks-rec-id": record.data.id,
              });
              // attachment counter div
              var $div_att_name = $("<div>", {
                class: "ks_attachment_name",
              }).append(
                $("<span>").html("+" + (arr.length - ks_attachment_limit))
              );
              $att_div = $att_div.append($div_att_name);
              //appending both mimetype and name to the inner div
              $inner_div = $inner_div.append($att_div);
              return false;
            }
          });
          var $div = $outer_div.append($inner_div);
          $tr = $tr.add($div);
        }
      }

      return $tr;
    },
    /**
     * @private
     * @param {MouseEvent} ev
     */
    _onksAttachmentDivClicked: function (ev) {
      if (ev.target.className == "ks_attachment_data") {
        var id = $(ev.currentTarget.parentElement.previousElementSibling).data(
          "id"
        );
        if (id) {
          this.trigger_up("open_record", {
            id: id,
            target: ev.target,
          });
        }
      }
    },
    /**
     * To toggle class for adding bgcolor on selecetd rows
     * @private
     * @param {MouseEvent} ev
     */
    _onksInputChange: function (ev) {
      var self = this;
      var $ksrow = ev.currentTarget.closest("tr");
      var $ksparent = $ksrow.parentElement.localName;
      if ($ksparent == "thead") {
        var $ksrows = ev.delegateTarget.querySelector("tbody").children;
        _.each($ksrows, function (row) {
            if ($(row).find('td').length > 1){
                row.classList.toggle("ks_row_selected", ev.currentTarget.checked);
                self._ksApplyBgColorRow(row, ev.currentTarget.checked);
            }
        });
      } else if ($ksparent == "tbody"){
        $ksrow.classList.toggle("ks_row_selected", ev.currentTarget.checked);
        self._ksApplyBgColorRow($ksrow, ev.currentTarget.checked);
      }
    },

    _ksApplyBgColorRow(ksRow, status){
        var self = this;
        var ks_primary = document.body.style.getPropertyValue('--primary');
        ks_primary = self._ksHexToRGB(ks_primary);
        // Apply color.
        if (status){
            $(ksRow).css({'background-color': `rgba(${ks_primary.r},${ks_primary.g},${ks_primary.b}, 0.3)`});
            if ($(ksRow).attr('data-id')){
                $(".ks_attachment_data[id='"+$(ksRow).attr('data-id')+"']").css({'background-color': `rgba(${ks_primary.r},${ks_primary.g},${ks_primary.b}, 0.3)`});
            }
        }
        // Remove color.
        else{
            $(ksRow).css({'background-color': 'transparent'});
            if ($(ksRow).attr('data-id')){
                $(".ks_attachment_data[id='"+$(ksRow).attr('data-id')+"']").css({'background-color': 'transparent'});
            }
        }
    },

    _ksHexToRGB: function (hex) {
        var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result
          ? {
              r: parseInt(result[1], 16),
              g: parseInt(result[2], 16),
              b: parseInt(result[3], 16),
            }
          : null;
      },

    _onRowClicked: function (ev) {
        var self = this;

        var event_rec_id = $(ev.currentTarget).data('id');
        if(self.getParent().getParent().actionService && event_rec_id && this.list_split_mode && this.list_split_mode != 'no_split' && $(".split-dropdown").length > 0){
            if (!ev.target.closest('.o_list_record_selector') && !$(ev.target).prop('special_click') && !this.no_open) {
                if (this.split_view_data.active && this.split_view_data.event_rec_id === event_rec_id) return;
                this._create_split_form_view(this.list_split_mode, event_rec_id);
            }
        } else {
            return this._super.apply(this, arguments);
        }
    },

    _create_split_form_view: function(split_mode, event_rec_id) {
        var self = this;
        let form_view_controller = this._create_custom_form_controller(event_rec_id);
        self.split_view_data.event_rec_id = event_rec_id;
        return form_view_controller.then(function (formView) {
              let old_form_view = self.split_view_data.split_form_view;
              self.split_view_data.split_form_view = formView;
              var fragment = document.createDocumentFragment();

              if (!self.split_view_data.active)
                    self._create_separator_for_split_window(fragment, split_mode);

              return self.split_view_data.split_form_view.appendTo(fragment)
                  .then(function () {
                        $(".list_split_mode").addClass('split_active');
                        self.split_view_data.active = true;
                        if (old_form_view) old_form_view.destroy();
                        dom.append(self.$el.parent(), fragment, {
                            callbacks: [{widget: self.split_view_data.split_form_view}],
                            in_DOM: true,
                        })
                  });
        });
    },

    _create_custom_form_controller: function(event_rec_id){
        var self = this;
        var FormView = view_registry.get('form');
        var list_controller = this.getParent();
        var view_adapt = list_controller.getParent();
        var current_controller = view_adapt.actionService.currentController;

        const params = {
            resModel: current_controller.props.resModel,
            views: current_controller.props.views,
            context: current_controller.props.context,
        };
        const options = {
            actionId: current_controller.action.id,
            loadActionMenus: current_controller.props.loadActionMenus,
            loadIrFilters: current_controller.props.loadIrFilters,
        };
        var fields_view_def = view_adapt.vm.loadViews(params, options);
        var rec_id = list_controller.model.get(event_rec_id, {raw: true});
        self.split_view_data.res_id = rec_id.res_id;

        return fields_view_def.then(function (viewInfo) {
             viewInfo['form'].toolbar = {}
            var formview = new FormView(viewInfo['form'], {
                modelName: list_controller.modelName,
                context: current_controller.props.context,
                ids: rec_id.res_id ? [rec_id.res_id] : [],
                currentId: rec_id.res_id || undefined,
                index: 0,
                mode: 'readonly',
                footerToButtons: true,
                default_buttons: true,
                withControlPanel: true,
                model: list_controller.model,
                parentID: self.parentID,
                recordID: self.recordID,
                isKsSplitFormView: true,

            });
            return formview.getController(view_adapt);
        })
    },

    _create_separator_for_split_window: function(fragment, split_mode){
        var self = this;
        var separator_class = '';
        var separator_options = {
            containment: 'parent',
            helper: 'clone'
        }
        if(split_mode === 'vertical') {
            separator_class = 'resize-vr';
            if (session['ks_splitted_vertical_width'])
                this.$el.outerWidth(session['ks_splitted_vertical_width'])
            if (session['ks_lang_direction'] && session['ks_lang_direction'] == 'rtl') {
                Object.assign(separator_options, {
                    axis: 'x',
                    start: function(event, ui) {
                        $(this).attr('start_offset', $(this).offset().left);
                        $(this).attr('start_next_height', $(this).prev().width());
                    },
                    drag: function(event, ui) {
                        $('.resize-vr').css({
                            'opacity': '0.2'
                        })
                        var next_element = $(this).prev();
                        var prev_element = $(this).next();
                        var y_difference = $(this).attr('start_offset') - ui.offset.left;
                        prev_element.width(ui.offset.left - prev_element.offset().left);
                        next_element.width(parseInt($(this).attr('start_next_height')) + y_difference);
                    }
                })
            } else {
                Object.assign(separator_options, {
                    axis: 'x',
                    start: function(event, ui) {
                        $(this).attr('start_offset', $(this).offset().left);
                        $(this).attr('start_next_height', $(this).next().width());
                    },
                    drag: function(event, ui) {
                        $('.resize-vr').css({
                            'opacity': '0.2'
                        })
                        var prev_element = $(this).prev();
                        var next_element = $(this).next();
                        var y_difference = $(this).attr('start_offset') - ui.offset.left;
                        prev_element.width(ui.offset.left - prev_element.offset().left);
                    }
                })
            }
        } else {
            separator_class = 'resize-hr';
            if (session['ks_splitted_horizontal_height'])
                this.$el.outerHeight(session['ks_splitted_horizontal_height'])
            Object.assign(separator_options, {
                axis: 'y',
                start: function(event, ui) {
                    $(this).attr('start_offset', $(this).offset().top);
                    $(this).attr('start_next_height', $(this).next().height());
                },
                drag: function(event, ui) {
                    var prev_element = $(this).prev();
                    var next_element = $(this).next();
                    var y_difference = $(this).attr('start_offset') - ui.offset.top;
                    prev_element.height(ui.offset.top - prev_element.offset().top);
                    next_element.height(parseInt($(this).attr('start_next_height')) + y_difference);
                    $('.resize-hr').css({
                        'opacity': '0.2'
                    })
                }
            });
        }

        self.split_view_data.$split_separator = $('<div id="separator"></div>').addClass(separator_class);
        self.split_view_data.$split_separator.appendTo(fragment);
        self.split_view_data.$split_separator.draggable(separator_options);
        self.split_view_data.$split_separator.on("dragstop", function(event, ui) {
          if (session['ks_split_view'] == 'vertical') {
              var val = {
                  'ks_split_vertical_list_width': isNaN(parseFloat(self.$el.outerWidth(true))) ? false : parseFloat(self.$el.outerWidth(true)),
              }
          } else {
              var val = {
                  'ks_split_horizontal_list_height': isNaN(parseFloat(self.$el.outerHeight(true))) ? false : parseFloat(self.$el.outerHeight(true)),
              }
          }
          self._rpc({
            route: "/ks_curved_backend_theme_enter/save/ks_splitted_form_width",
            params: {
              'data': val
            }
          });
        });
    },


  });
  return Ks_ListRenderer;
});
