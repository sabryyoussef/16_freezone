/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import field_utils from 'web.field_utils';
import { _t } from "web.core";
import { qweb } from 'web.core';
import utils from 'web.utils';
import session from 'web.session';
const {onWillStart, useState, useRef, onMounted} = owl;
import { FormRenderer } from "@web/views/form/form_renderer";
import ajax from 'web.ajax';
import Widget from "web.Widget";

patch(FormRenderer.prototype,"ks_form_render",{
    setup(){
        this._super();
        this.RootRef = useRef("compiled_view_root");
//        if (this.props.activeActions.type != 'one2many'){
            onWillStart(this.onWillStart);
            onMounted(this._mounted);
//        }
    },
    async onWillStart(){
        var self = this;
        await ajax.jsonRpc("/web/dataset/call","call",{
                model: "ks.global.config",
                method: "ks_get_value_from_scope",
                args: [[ "ks_chatter",  ], ],
            }).then(function (data) {
          self.ks_data = data.ks_chatter;
        });
    },
    _mounted(){
        if(this.ks_data == 'ks_chatter_right'){
            var table = this.RootRef.el;
            if ($(table).hasClass("flex-nowrap")){
            $(table).removeClass("flex-nowrap")
            }
            $(table).addClass("ks-right-content");
            $(table).removeClass("flex-column");
            $('<div class="custom_seperator"></div>').insertAfter($(table).find('.o_form_sheet_bg'));
            if (session['ks_lang_direction'] && session['ks_lang_direction'] == 'rtl'){
            $('.custom_seperator').draggable({
                    axis: 'x',
                    containment: 'parent',
                    helper: 'clone',
                    start: function(event, ui) {
                    $(this).attr('start_offset', $(this).offset().left);
                     $(this).attr('start_next_height', $(this).prev().width());
                     },
                     drag: function(event, ui) {
                     $('.custom_seperator').css({
                      'opacity': '0.2'
                      })
                      var next_element = $(this).prev();
                      var prev_element = $(this).next();
                      var y_difference = $(this).attr('start_offset') - ui.offset.left;
                      prev_element.width(ui.offset.left - prev_element.offset().left);
                      next_element.width(parseInt($(this).attr('start_next_height')) + y_difference);
                      }
                        });
                      } else {
                      $('.custom_seperator').draggable({
                      axis: 'x',
                      containment: 'parent',
                      helper: 'clone',
                      start: function(event, ui) {
                      $(this).attr('start_offset', $(this).offset().left);
                      $(this).attr('start_next_height', $(this).next().width());
                      },
                      drag: function(event, ui) {
                      var prev_element = $(this).prev();
                      $('.custom_seperator').css({
                      'opacity': '0.2'
                      })
                      var next_element = $(this).next();
                      var y_difference = $(this).attr('start_offset') - ui.offset.left;
                       prev_element.width(ui.offset.left - prev_element.offset().left);
                       //                            next_element.width(parseInt($(this).attr('start_next_height'))+y_difference);
                        }
                        });
                        $('.custom_seperator').on("dragstop", function(event, ui) {
                        $('.custom_seperator').css({
                        'opacity': '1'
                        })
                        ajax.jsonRpc("/ks_curved_backend_theme_enter/save/form_width", "call", {
                        val: isNaN(parseFloat($('.o_form_sheet_bg').width())) ? false : parseFloat($('.o_form_sheet_bg').width())
                        });
                        });
                        if (session['ks_form_view_width']) {
                                $(table).find('.o_form_sheet_bg').css({
                                    'width': session['ks_form_view_width']
                                })
                                //                temp_this.$el.find('.o_FormRenderer_chatterContainer').css({'width':Session['ks_form_view_width']})
                            } else {
                                $(table).find('.o_form_sheet_bg').outerWidth('60%');
                            }
                        }

//            $(table).parent().parent().parent().addClass("o_xxl_form_view h-100");
//            $(table).removeClass("flex-column");
//            $(table).addClass("flex-nowrap h-100");
//            $($(table).children()[1]).addClass("o-aside")

            }
        },

    });