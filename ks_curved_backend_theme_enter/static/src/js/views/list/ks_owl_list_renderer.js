/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import field_utils from 'web.field_utils';
import { _t } from "web.core";
import { qweb } from 'web.core';
import utils from 'web.utils';
import session from 'web.session';
const {onWillStart, useState, useRef, onMounted} = owl;
import { ListRenderer } from "@web/views/list/list_renderer";
import ajax from 'web.ajax';
import Widget from "web.Widget";
import KsListDocumentViewer from "ks_curved_backend_theme_enter.KsListDocumentViewer";
import { formView } from "@web/views/form/form_view";
//import { AttachmentViewer } from '@mail/components/attachment_viewer/attachment_viewer'


patch(ListRenderer.prototype,"ks_list_renderer",{
    setup(){
        this._super();
        this.notification = useService("notification");
        this.tableRef = useRef("table");
//        this.split_view_data = {active: false};
//        this.viewservice = useService("view");

//        if (this.props.activeActions.type != 'one2many'){
            onWillStart(this.onWillStart);
            onMounted(this._mounted);
//        }
    },

    _mounted(){
        if(this.ks_list.ks_list_density == 'Comfortable'){
            var table = this.tableRef;
            var table_rows = table.el.getElementsByTagName('tbody')[0].children;
            for (let item of table_rows) {
                $(item).addClass("ks_comfortable_list");
            }
        }
    },

    async onWillStart(){
        var self = this;
        let rec_ids = [];
        for(let i=0;i<this.props.list.records.length;i++){
            rec_ids.push(this.props.list.records[i].resId);
        }
        let model = this.props.list.resModel;
        let limit = this.props.list.limit;
        let offset = this.props.list.offset;
        let domain = this.props.list.domain;
        await ajax.jsonRpc("/ks_list_renderer/attachments", "call", {
          res_ids: rec_ids,
          model: model,
          domain: domain,
          offset: offset,
          limit: limit,
        }).then(function (data) {
          self.ks_data = data[0];
          self.ks_list = data[1];
          self.rec_id = Object.keys(data[0]).map(Number);
        });
    },

    download_attachment(ev){
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
        var ks_attachmentViewer = new KsListDocumentViewer (
          self,
          ks_attachment,
          ks_activeAttachmentID
        );
        ks_attachmentViewer.appendTo($("body"));
      } else
        this.notification.add(_t("This file type can not be previewed"), {
          title: _t("File Type Not Supported"),
          sticky: false,
          type:"info",
        }
        );
    },
    _onksAttachmentDivClicked(ev) {
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
//    async onCellClicked(record, column, ev) {
//    if (session['ks_split_view'] == 'no_split'){
//    return this._super(...arguments)
//    }else{
//    this._create_split_form_view(session['ks_split_view'],record.id,record)
//    }
//    },
//    async _create_split_form_view(split_mode, event_rec_id,record) {
//        var self = this;
////        let form_view_controller = this._create_custom_form_controller(event_rec_id);
////        self.split_view_data.event_rec_id = event_rec_id;
////        return form_view_controller.then(function (formView) {
////              let old_form_view = self.split_view_data.split_form_view;
//              self.split_view_data.split_form_view = await this.viewservice.loadViews(
//                {
//                    context: this.props.list.context,
//                    resModel: this.props.list.resModel,
//                    views: [[record.d, "form"]],
//                }
////                {
////                    actionId: this.env.config.actionId,
////                    loadIrFilters: this.actionService.currentController.props.loadIrFilters || false,
////                }
//            );
//
//              var fragment = document.createDocumentFragment();
//
//              if (!self.split_view_data.active)
//                    self._create_separator_for_split_window(fragment, split_mode);
//
//              return self.split_view_data.split_form_view
//              .appendTo(fragment)
//                  .then(function () {
//                        $(".list_split_mode").addClass('split_active');
//                        self.split_view_data.active = true;
//                        dom.append(self.$el.parent(), fragment, {
//                            callbacks: [{widget: self.split_view_data.split_form_view}],
//                            in_DOM: true,
//                        })
//                  });
////        });
//    },
////    _create_custom_form_controller(event_rec_id){
////        var self = this;
////        var FormView = view_registry.get('form');
////        var list_controller = this.getParent();
////        var view_adapt = list_controller.getParent();
////        var current_controller = view_adapt.actionService.currentController;
////
////        const params = {
////            resModel: current_controller.props.resModel,
////            views: current_controller.props.views,
////            context: current_controller.props.context,
////        };
////        const options = {
////            actionId: current_controller.action.id,
////            loadActionMenus: current_controller.props.loadActionMenus,
////            loadIrFilters: current_controller.props.loadIrFilters,
////        };
////        var fields_view_def = view_adapt.vm.loadViews(params, options);
////        var rec_id = list_controller.model.get(event_rec_id, {raw: true});
////        self.split_view_data.res_id = rec_id.res_id;
////
////        return fields_view_def.then(function (viewInfo) {
////             viewInfo['form'].toolbar = {}
////            var formview = new FormView(viewInfo['form'], {
////                modelName: list_controller.modelName,
////                context: current_controller.props.context,
////                ids: rec_id.res_id ? [rec_id.res_id] : [],
////                currentId: rec_id.res_id || undefined,
////                index: 0,
////                mode: 'readonly',
////                footerToButtons: true,
////                default_buttons: true,
////                withControlPanel: true,
////                model: list_controller.model,
////                parentID: self.parentID,
////                recordID: self.recordID,
////                isKsSplitFormView: true,
////
////            });
////            return formview.getController(view_adapt);
////        })
////    },
//     _create_separator_for_split_window(fragment, split_mode){
//        var self = this;
//        var separator_class = '';
//        var separator_options = {
//            containment: 'parent',
//            helper: 'clone'
//        }
//        if(split_mode === 'vertical') {
//            separator_class = 'resize-vr';
//            if (session['ks_splitted_vertical_width'])
//                $(this.RootRef.el).outerWidth(session['ks_splitted_vertical_width'])
//            if (session['ks_lang_direction'] && session['ks_lang_direction'] == 'rtl') {
//                Object.assign(separator_options, {
//                    axis: 'x',
//                    start: function(event, ui) {
//                        $(this).attr('start_offset', $(this).offset().left);
//                        $(this).attr('start_next_height', $(this).prev().width());
//                    },
//                    drag: function(event, ui) {
//                        $('.resize-vr').css({
//                            'opacity': '0.2'
//                        })
//                        var next_element = $(this).prev();
//                        var prev_element = $(this).next();
//                        var y_difference = $(this).attr('start_offset') - ui.offset.left;
//                        prev_element.width(ui.offset.left - prev_element.offset().left);
//                        next_element.width(parseInt($(this).attr('start_next_height')) + y_difference);
//                    }
//                })
//            } else {
//                Object.assign(separator_options, {
//                    axis: 'x',
//                    start: function(event, ui) {
//                        $(this).attr('start_offset', $(this).offset().left);
//                        $(this).attr('start_next_height', $(this).next().width());
//                    },
//                    drag: function(event, ui) {
//                        $('.resize-vr').css({
//                            'opacity': '0.2'
//                        })
//                        var prev_element = $(this).prev();
//                        var next_element = $(this).next();
//                        var y_difference = $(this).attr('start_offset') - ui.offset.left;
//                        prev_element.width(ui.offset.left - prev_element.offset().left);
//                    }
//                })
//            }
//        } else {
//            separator_class = 'resize-hr';
//            if (session['ks_splitted_horizontal_height'])
//                $(this.RootRef.el).outerHeight(session['ks_splitted_horizontal_height'])
//            Object.assign(separator_options, {
//                axis: 'y',
//                start: function(event, ui) {
//                    $(this).attr('start_offset', $(this).offset().top);
//                    $(this).attr('start_next_height', $(this).next().height());
//                },
//                drag: function(event, ui) {
//                    var prev_element = $(this).prev();
//                    var next_element = $(this).next();
//                    var y_difference = $(this).attr('start_offset') - ui.offset.top;
//                    prev_element.height(ui.offset.top - prev_element.offset().top);
//                    next_element.height(parseInt($(this).attr('start_next_height')) + y_difference);
//                    $('.resize-hr').css({
//                        'opacity': '0.2'
//                    })
//                }
//            });
//        }
//
//        self.split_view_data.$split_separator = $('<div id="separator"></div>').addClass(separator_class);
//        self.split_view_data.$split_separator.appendTo(fragment);
//        self.split_view_data.$split_separator.draggable(separator_options);
//        self.split_view_data.$split_separator.on("dragstop", function(event, ui) {
//          if (session['ks_split_view'] == 'vertical') {
//              var val = {
//                  'ks_split_vertical_list_width': isNaN(parseFloat(self.$el.outerWidth(true))) ? false : parseFloat(self.$el.outerWidth(true)),
//              }
//          } else {
//              var val = {
//                  'ks_split_horizontal_list_height': isNaN(parseFloat(self.$el.outerHeight(true))) ? false : parseFloat(self.$el.outerHeight(true)),
//              }
//          }
//          ajax.jsonRpc("/ks_curved_backend_theme_enter/save/ks_splitted_form_width", "call",{
//            params: {
//              'data': val
//            }
//          });
//        });
//    },

});