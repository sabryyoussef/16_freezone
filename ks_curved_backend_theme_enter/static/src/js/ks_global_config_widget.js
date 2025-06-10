/** @odoo-module **/

import "web.dom_ready";
import { useService } from "@web/core/utils/hooks";
import utils from "web.utils";

import { registry } from "@web/core/registry";
import ajax from 'web.ajax';
import session from "web.session";
import core from 'web.core';
import Dialog from 'web.Dialog';
import { qweb } from 'web.core';
import { useAutofocus } from "@web/core/utils/hooks"
import { standardFieldProps } from "@web/views/fields/standard_field_props";
const { useListener } = require("@web/core/utils/hooks");
const { Component,useState,onWillStart,onWillUnmount, onMounted} = owl;


export class KsGlobalConfigWidget extends Component{
        setup(){
        var self=this
            this.file_type_magic_word= {
                "/": "jpg",
                R: "gif",
                i: "png",
                P: "svg+xml",
            };
            this.rpc = useService("rpc");
            var self=this.props;
            this.ks_unsaved_data = {};
            this.ks_unsaved_theme_global_data = {};
            this.ks_dirty_data = {}
            this.ks_global_theme_fields = ["ks_body_background", "ks_menu", "ks_menu_hover", "ks_button", "ks_border", "ks_heading", "ks_link", "ks_primary_color", "ks_tooltip", "name", ];
            onWillStart(async () => {
                await this.willStart()
            });


        }


        async willStart() {
            const data = await this.rpc("/web/dataset/call", {
              model: "ks.global.config",
              method: "ks_get_config_values",
              args: [],
            });
            const ks_theme_global_data = await this.rpc("/render/theme/view/data", { ks_setting_scope: 'Global' });
            if (data) {
                this.data = data;
            }
            if (ks_theme_global_data) {
                this.ks_color_theme_scope = ks_theme_global_data.ks_color_theme_scope == "Global" ? true : false;
                this.ks_theme_global_data = ks_theme_global_data;
            }
        }

         _ksAttachImageZoom(){
            $(".ks_image_hover").attr("data-zoom", 1);
            $(".ks_image_hover").zoomOdoo({
                event: "mouseenter",
                attach: ".ks_back_img_hover",
                zoom: true,
                attachToTarget: true,
                beforeAttach() {
                    this.$flyout.css({
                        width: "125px",
                        height: "125px"
                    });
                },
            });
        }

        _ksColorThemeResetToDefault() {
            this.ks_unsaved_data = {}
            var default_color_theme = this.ks_theme_global_data.ks_color_theme.predefined.filter(x=>x.ks_default)
            if (default_color_theme.length) {
                this.ks_unsaved_theme_global_data['ks_theme_color'] = default_color_theme[0]['id'];
                this._ksSaveGlobalData();
            }
        }

        _ksApplyScope() {
            var self = this;
            if (this.ks_unsaved_data) {
                this.rpc("/web/dataset/call", {
                    args: [this.ks_unsaved_data],
                    method: "ks_save_apply_scope",
                    model: "ks.global.config",
                }).then(function() {
                    self.env.model.actionService.doAction("reload_context");
                });
            }
        }

        _onInputChange(ev) {
            var self = this;
            if (!$(ev.currentTarget).parents('#global_theme_edit_section').length) {
                if (ev.currentTarget.name && ev.currentTarget.dataset.value != this.data[ev.currentTarget.name] && ev.currentTarget.hasAttribute("ks_curve_scope_input")) {
                    this.ks_unsaved_data[ev.currentTarget.name] = ev.currentTarget.dataset.value;
                    self.ks_dirty_data[ev.currentTarget.name] = $(ev.currentTarget);
                } else if (ev.currentTarget.name) {
                    delete this.ks_unsaved_data[ev.currentTarget.name];
                }

                // Condition to change global setting fields and boolean fields.
                if (ev.currentTarget.name.split("scope").length < 2 && !$(ev.currentTarget).hasClass("ks_binary_field")) {
                    this.ks_unsaved_theme_global_data[ev.currentTarget.name] = ev.currentTarget.dataset.value ? ev.currentTarget.dataset.value : ev.currentTarget.checked;
                    self.ks_dirty_data[ev.currentTarget.name] = $(ev.currentTarget);
                }
                if ($(ev.currentTarget).attr("class") && $(ev.currentTarget).attr("class").includes("slider")) {
                    $(ev.currentTarget).siblings(".ks_opacity_value_max").html(ev.currentTarget.value);
                    this.ks_unsaved_theme_global_data[ev.currentTarget.name] = ev.currentTarget.value;
                    self.ks_dirty_data[ev.currentTarget.name] = $(ev.currentTarget);
                }
                if(ev.currentTarget.value<=0.3){
                    document.getElementById("ks-drawer-global-slider").classList.remove("d-none");
                  }
                  else{
                    if(document.getElementById("ks-drawer-global-slider")){
                        document.getElementById("ks-drawer-global-slider").classList.add("d-none");
                    }
                  }
                // Manage data for text fields.
                if (ev.currentTarget.name && ev.currentTarget.dataset.type == "ks-char") {
                    this.ks_unsaved_theme_global_data[ev.currentTarget.name] = ev.currentTarget.value;
                    self.ks_dirty_data[ev.currentTarget.name] = $(ev.target);
                }

                // Handle binary field fields.
                // Set background image active true.
                if ($(ev.target).hasClass("ks_binary_field")) {
                    var file_node = ev.target;
                    // Handle body background input change.
                    if (file_node.getAttribute("data-model")) {
                        var ks_img_src = $(file_node.nextElementSibling).find("img").attr("src");
                        var ks_value = self._ksDecodeURLToString(ks_img_src);
                        if (file_node.id.split("#")[1] && parseInt(file_node.id.split("#")[1])) {
                            ks_value = parseInt(file_node.id.split("#")[1]);
                        }
                        this.ks_unsaved_theme_global_data[file_node.name] = false;
                        this.ks_unsaved_theme_global_data[file_node.getAttribute("data-field-save")] = ks_value;
                        self.ks_dirty_data[file_node.name] = $(ev.target);
                        self.ks_dirty_data[file_node.getAttribute("data-field-save")] = $(ev.target);
                    } else {
                        // create background image data.
                        var file = file_node.files[0];
                        var field_name = ev.target.name;
                        utils.getDataURLFromFile(file).then(function(data) {
                            data = data.split(",")[1];
                            // Create url for file
                            var url = "data:image/" + (self.file_type_magic_word[data[0]] || "png") + ";base64," + data;
                            $("." + field_name + "_preview").prop("src", url);
                            // self.ks_unsaved_theme_global_data[field_name] = data;
                            if ($(ev.target).hasClass("ks_background_image")) {
                                ajax.jsonRpc("/ks_curved_backend_theme_enter/add/images", "call", {
                                    image_info: {
                                        key: field_name,
                                        value: data
                                    },
                                    scope: "global",
                                }).then(function(res) {
                                    var ks_template_data = {};
                                    self._KsGetImageDict(field_name, ks_template_data);
                                    ks_template_data["ks_image_data"] = res;

                                    var ks_image_container = qweb.render("ks_theme_image_template", ks_template_data);

                                    if (field_name == "ks_body_background_img") {
                                        $("div.ks_body_background_global_container").html(ks_image_container);
                                    }
                                    if (field_name == "ks_app_drawer_background_img") {
                                        $("div.ks_app_drawer_background_global_container").html(ks_image_container);
                                    }
                                    // function to reattach zoom functionality on image.
                                    self._ksAttachImageZoom();
                                    self.env.model.actionService.doAction("reload_context");
                                });
                            }

                            if($(ev.target).hasClass("ks_login_background_image")){
                                field_name="ks_login_background_image"
                                ajax.jsonRpc("/ks_curved_backend_theme_enter/add/login/images", "call", {
                                    image_info: {
                                        key: field_name,
                                        value: data
                                    }
                                }).then(function(res) {
                                    var ks_template_data = {};
                                    self._KsGetImageDict(field_name, ks_template_data);
                                    ks_template_data["ks_login_image"] = res;

                                    var ks_image_container = qweb.render("ks_login_background_image_template", ks_template_data);
                                    if (field_name == "ks_login_background_image") {
                                        $("div.ks_login_background_img_container").html(ks_image_container);
                                        }
//                                    Object.values(document.querySelectorAll(".ks_login_background_image_non_owl")).map((item)=>{
//                                        item.childNodes[0].addEventListener("change",(ev) =>{this._onInputChange(ev)})
//                                        item.childNodes[2].addEventListener("click",(ev) =>{this._ksDelLoginBackgroundImage(ev)})
//                                        })
//                                        document.querySelectorAll(".ks_login_background_image_1").addEventListener("change",(ev) =>{this._onInputChange(ev)})


                                    // function to reattach zoom functionality on image.
                                    self._ksAttachImageZoom();
                                    self.env.model.actionService.doAction("reload_context");
                                });
                            }
                            else {
                                $("." + field_name + "_preview").prop("src", url);
                                self.ks_unsaved_theme_global_data[field_name] = data;
                            }
                        });
                    }
                }
            } else {
                // Handle color theme input
                var ks_color_theme_fields = ["ks_body_background_global", "ks_menu_global", "ks_menu_hover_global", "ks_button_global", "ks_border_global", "ks_heading_global", "ks_link_global", "ks_primary_color_global", "ks_tooltip_global", ];

                if (ks_color_theme_fields.includes(ev.target.name)) {
                    this._ksApplyTempColorTheme(ev.target.name, ev.target.value);
                }
            }
        }

        _KsGetImageDict(field_name, ks_template_data) {
            if (field_name == "ks_body_background_img") {
                ks_template_data["ks_image_for"] = "ks_body_background_global";
                ks_template_data["ks_image_save"] = "ks_body_background_img";
                ks_template_data["ks_image_del"] = "ks_body_background_del_global";
                ks_template_data["ks_image_add"] = "ks_body_background_img_global";
            }

            if (field_name == "ks_app_drawer_background_img") {
                ks_template_data["ks_image_for"] = "ks_app_drawer_background_global";
                ks_template_data["ks_image_save"] = "ks_app_drawer_background_img";
                ks_template_data["ks_image_del"] = "ks_drawer_background_global_del";
                ks_template_data["ks_image_add"] = "ks_app_drawer_background_global";
            }
        }

        _ksApplyTempColorTheme(field_name, field_val) {
            var ks_color_field_dict = {
                ks_body_background_global: "--body-background",
                ks_menu_global: "--nav-link-color",
                ks_menu_hover_global: "--ks-over-link",
                ks_button_global: "--primary-btn",
                ks_border_global: "--tab-bg",
                ks_heading_global: "--heading-color",
                ks_link_global: "--link-color",
                ks_primary_color_global: "--primary",
                ks_tooltip_global: "--tooltip-heading-bg",
            };

            if (document.body.style.getPropertyValue(ks_color_field_dict[field_name])) {
                document.body.style.setProperty(ks_color_field_dict[field_name], field_val);
            }
        }

        _ksDecodeURLToString(URL) {
            return URL.split(",")[1];
        }

        _ksSaveGlobalData(ev) {
            var self = this;
            if (Object.keys(this.ks_unsaved_theme_global_data).length) {
                ajax.jsonRpc("/save/theme/settings", "call", {
                    ks_unsaved_setting: this.ks_unsaved_theme_global_data,
                    ks_origin_scope: "global",
                }).then(function() {
                    var x
                    self.env.model.actionService.doAction("reload_context");
                });
            }
        }

        _ksDelBackgroundImage(ev) {
            var self = this;
            var ks_image_id = ev.target.getAttribute("data-id");
            ks_image_id = ks_image_id.split("#")[1];
            if (ev.target.classList.contains("ks_drawer_background_global_del")) {
                var ks_model = "ks.drawer.background";
            } else {
                var ks_model = "ks.body.background";
            }
            if (ks_image_id) {
                Dialog.confirm(this, this.env._t("Are you sure you want to delete this record ?"), {
                    confirm_callback() {
                        ajax.jsonRpc("/web/dataset/call","call", {
                            model: ks_model,
                            method: "unlink",
                            args: [ks_image_id],
                        }).then(function() {
                            $(ev.target.parentElement.parentElement).remove();
                            // self.do_action("reload_context");
                        });
                    },
                });
            }
        }

        _ksDelLoginBackgroundImage(ev){
            var self = this;
            var ks_image_id = event.target.getAttribute("data-id");
            ks_image_id = ks_image_id.split("#")[1];
            if (ks_image_id) {
                Dialog.confirm(this, this.env._t("Are you sure you want to delete this record ?"), {
                    confirm_callback() {
                        ajax.jsonRpc("/web/dataset/call","call",{
                            model: "ks.login.background.image",
                            method: "unlink",
                            args: [ks_image_id],
                        }).then(function() {
                            $(ev.target.parentElement.parentElement).remove();
                            // self.do_action("reload_context");
                        });
                    },
                });
            }
        }

        _ksDelLoginBackgroundColor(ev){
            var self = this;
            var ks_color_id = ev.target.getAttribute("data-id");
            ks_color_id = ks_color_id.split("#")[1];
            if (ks_color_id) {
                Dialog.confirm(this, this.env._t("Are you sure you want to delete this record ?"), {
                    confirm_callback() {
                        var x
                        this.__parentedParent.rpc("/web/dataset/call", {
                            model: "ks.login.background.color",
                            method: "unlink",
                            args: [ks_color_id],
                        }).then(function(res) {
                            $(ev.target.parentElement.parentElement).remove();
                        });
                    },
                });
            }
        }

        _ksBackgroundDefault(ev) {
            var self = this;
            ajax.jsonRpc("/kstheme/background/default","call",{

                    ks_setting_scope: "Global",
                    ks_default_info: {
                        field: "ks_body_background",
                        model: "ks.body.background",
                },
            }).then(function() {
                self.env.model.actionService.doAction("reload_context");
            });
        }

        _ksDrawerDefault(ev) {
            var self = this;
            ajax.jsonRpc("/kstheme/background/default","call",{

                    ks_setting_scope: "Global",
                    ks_default_info: {
                        field: "ks_app_drawer_background",
                        model: "ks.drawer.background",
                    },

            }).then(function() {
                self.env.model.actionService.doAction("reload_context");
            });
        }

        _ksSettingCancel() {
            this._ksResetValues();
            this._ksColorThemeCancel();
        }

        _ksResetValues() {
            var self = this;
            var ks_session = this.ks_theme_global_data;
            var ks_splitter = "_global";
            for (var index in this.ks_unsaved_theme_global_data) {
                let ks_index = index.split(ks_splitter)[0];
                // Ignore unsupported fields.
                if (!["ks_app_drawer_background_img", "ks_app_drawer_background_opacity", "ks_body_background_img", "ks_body_background_opacity", "ks_company_logo", "ks_login_background_image", "ks_small_company_logo", "ks_website_title", ].includes(ks_index)) {
                    if (typeof ks_session[ks_index] == "boolean") {
                        $(`input#${ks_index}${ks_splitter}`).prop("checked", ks_session[ks_index]);
                    } else if (!["ks_app_drawer_background", "ks_body_background"].includes(ks_index)) {
                        $(`input#${ks_session[ks_index]}${ks_splitter}`).prop("checked", true);
                    }
                } else if (["ks_body_background_img", "ks_app_drawer_background_img"].includes(index)) {
                    $(`p.${index}_global`).addClass("d-none");
                }
                delete this.ks_unsaved_theme_global_data[index];
            }
            // Reset background image and color for background and app drawer.
            ["ks_body_background_global", "ks_app_drawer_background_global", ].forEach((element)=>{
                $(`input[name=${element}]:checked`).prop("checked", false);
                $(`input[name=${element}][checked=checked]`).prop("checked", true);
            }
            );
            // function called to revert view changes  body background and color theme
            self._KsResetDirtyData(ks_session, ks_splitter);
        }
        _KsResetDirtyData(ks_session, ks_splitter) {
            var self = this;
            for (var index in self.ks_dirty_data) {
                if (index && self.ks_dirty_data[index] && (index.split(ks_splitter)[0]in ks_session) && self.ks_dirty_data[index].attr('type') == 'range') {
                    //Handled toggle button case
                    self.ks_dirty_data[index].val(ks_session[index.split(ks_splitter)[0]])
                } else if (index && self.ks_dirty_data[index] && (self.ks_dirty_data[index].data('field-save')in ks_session) && self.ks_dirty_data[index].data('field-save') && self.ks_dirty_data[index].hasClass('ks_radio_list')) {
                    //Handled color theme and body background case
                    var active_rec = [];
                    if (Array.isArray(ks_session[self.ks_dirty_data[index].data('field-save')])) {
                        var active_rec = ks_session[self.ks_dirty_data[index].data('field-save')].filter(x=>x.ks_active)
                    } else {
                        for (var key in ks_session[self.ks_dirty_data[index].data('field-save')]) {
                            active_rec = ks_session[self.ks_dirty_data[index].data('field-save')][key].filter(x=>x.ks_active);
                            if (active_rec && active_rec.length)
                                break;
                        }
                    }
                    if (active_rec && active_rec.length) {
                        $('input[name=' + self.ks_dirty_data[index].attr('name') + '][data-value="' + active_rec[0]['id'] + '"]').prop('checked', true);
                    } else {
                        $.each($('input[name=' + self.ks_dirty_data[index].attr('name') + ']'), function(e) {
                            $(this).prop('checked', false);
                        });
                    }
                }else if (index && self.ks_dirty_data[index] && (self.ks_dirty_data[index].data('field-save')in ks_session) && self.ks_dirty_data[index].data('field-save') && self.ks_dirty_data[index].hasClass('ks_cancel_radio')) {
                    $('input[name=' + self.ks_dirty_data[index].attr('name') + '][data-value="' + ks_session[self.ks_dirty_data[index].data('field-save')] + '"]').prop('checked', true);
                }
            }
            self.ks_dirty_data = {}

        }

        async _ksColorThemeEdit(ev) {
            var self = this;
            $("div.ks_theme_selected").removeClass("ks_theme_selected");
            $(ev.currentTarget.parentElement.parentElement).addClass("ks_theme_selected");
            var arg1=await this.rpc("/web/dataset/call", {
                model: "ks.color.theme",
                method: "search_read",
                args:[],
                kwargs: {},
            })
            var ks_them_id=parseInt($(ev.target).attr("data-theme-id"));
            var arg=[arg1.find((item)=>item.id==ks_them_id)]
            if (arg[0].ks_template_id.length) {
                    arg[0].id = false;
            }
            var ks_edit_section = qweb.render("ks_theme_edit_section_global", {
                    ks_theme_data:arg[0],
            });
            $("div#global_theme_edit_section").html(ks_edit_section);

            this._ks_addEventListener_color_section_theme()
            if(arg[0].id){
                document.querySelector(".ks_theme_edit_update").addEventListener("click",(ev) =>{this._ksColorThemeUpdate(ev)})
            }
            self._scrollToDown();
        }
        _ks_addEventListener_color_section_theme(){
            document.querySelector("#name_global").addEventListener("change",(ev) =>{this._onInputChange(ev)})
            document.querySelector("#ks_body_background_global").addEventListener("change",(ev) =>{this._onInputChange(ev)})
            document.querySelector("#ks_menu_global").addEventListener("change",(ev) =>{this._onInputChange(ev)})
            document.querySelector("#ks_menu_hover_global").addEventListener("change",(ev) =>{this._onInputChange(ev)})
            document.querySelector("#ks_button_global").addEventListener("change",(ev) =>{this._onInputChange(ev)})
            document.querySelector("#ks_border_global").addEventListener("change",(ev) =>{this._onInputChange(ev)})
            document.querySelector("#ks_heading_global").addEventListener("change",(ev) =>{this._onInputChange(ev)})
            document.querySelector("#ks_link_global").addEventListener("change",(ev) =>{this._onInputChange(ev)})
            document.querySelector("#ks_tooltip_global").addEventListener("change",(ev) =>{this._onInputChange(ev)})

            document.querySelector(".ks_new_theme_save").addEventListener("click",(ev) =>{this._ksColorThemeSave(ev)})
            document.querySelector(".ks_theme_edit_cancel").addEventListener("click",(ev) =>{this._ksColorThemeCancel(ev)})
        }
        _ks_addEventListener_color_theme(){
            Object.values(document.querySelectorAll(".ks_color_theme_non_owl_input")).map((item)=>{
                item.childNodes[1].childNodes[1].addEventListener("click",(ev) =>{this._onInputChange(ev)})
                item.childNodes[3].childNodes[1].addEventListener("click",(ev) =>{this._ksColorThemeEdit(ev)})
                if(item.childNodes[3].childNodes.length==5){
                    item.childNodes[3].childNodes[3].addEventListener("click",(ev) =>{this._ksColorThemeDelete(ev)})
                }
            })
            document.querySelector("#ks_add_custom_theme_global_1").addEventListener("click",(ev) =>{this._ksCustomColorThemeAdd(ev)})


        }

        _scrollToDown() {
            // Scroll down div
            $("div.ks_color_theme_qweb_div_global").scrollTop($("div.ks_color_theme_qweb_div_global")[0].scrollHeight);
        }

        _ksCustomColorThemeAdd() {
            var self = this;
            var ks_edit_section = qweb.render("ks_theme_edit_section_global", {
                ks_theme_data: {},
            });
            $("div#global_theme_edit_section").html(ks_edit_section);
            this._ks_addEventListener_color_section_theme()
            self._scrollToDown();
        }

        _ksColorThemeCancel() {
            $("div#global_theme_edit_section").html("");
            $("div.ks_theme_selected").removeClass("ks_theme_selected");
            this._ksResetColorTheme();
        }

        _ksResetColorTheme() {
            var ks_color_field_dict = {
                ks_body_background: "body-background",
                ks_menu: "nav-link-color",
                ks_menu_hover: "ks-over-link",
                ks_button: "primary-btn",
                ks_border: "tab-bg",
                ks_heading: "heading-color",
                ks_link: "link-color",
                ks_primary_color: "primary",
                ks_tooltip: "tooltip-heading-bg",
            };
            _.each(ks_color_field_dict, (value,key)=>{
                if (document.body.style.getPropertyValue("--" + value)) {
                    document.body.style.setProperty("--" + value, session.ks_color_theme[value]);
                }
            }
            );
        }

        async _ksColorThemeSave() {
            var self = this;
            var ks_theme_data = this._ks_get_theme_data_dict();
            ks_theme_data["ks_global"] = true;
            var create_id=await this.rpc("/web/dataset/call", {
                model: "ks.color.theme",
                method: "create",
                args: [ks_theme_data],
            })
            var arg1= await self.rpc("/web/dataset/call", {
                    model: "ks.color.theme",
                    method: "search_read",
                    args:[[]],
                    kwargs: {
                        domain: [["id", "=", create_id]],
                        fields: [],
                    },
                })
            var arg=arg1.find((item)=>item.id==create_id)
            self.ks_theme_global_data.ks_color_theme.custom.push(arg);
            var color_theme_temp = qweb.render("ks_color_theme_qweb_template_global", {
                  ks_theme_global_data: self.ks_theme_global_data,
            });
            $("div.ks_color_theme_qweb_div_global").html(color_theme_temp);
            this._ks_addEventListener_color_theme()
        }

        _ks_get_theme_data_dict() {
            var ks_data = {};
            this.ks_global_theme_fields.forEach((ks_element)=>{
                ks_data[ks_element] = $(`input#${ks_element}_global`).val();
            }
            );
            return ks_data;
        }

        async _ksColorThemeUpdate(ev) {
            var self = this;
            var ks_theme_data = this._ks_get_theme_data_dict();
            var ks_theme_id = parseInt($(ev.currentTarget).attr("data-theme-id"));
            var arg= await this.rpc("/web/dataset/call", {
                model: "ks.color.theme",
                method: "write",
                args: [[ks_theme_id], ks_theme_data],
            })
            arg=  await self.rpc("/web/dataset/call", {
                    model: "ks.color.theme",
                    method: "search_read",
                    args:[],
                    kwargs: {
                        domain: [["id", "=", ks_theme_id]],
                        fields: [],
                    },
                })
             var x;
            var arg1=arg.find((item)=>item.id==ks_theme_id)
            self._updateThemeData(arg1);
            var color_theme_temp = qweb.render("ks_color_theme_qweb_template_global", {
                   ks_theme_global_data: self.ks_theme_global_data,
            });
            $("div.ks_color_theme_qweb_div_global").html(color_theme_temp);
            this._ks_addEventListener_color_theme()
        }

        _updateThemeData(updated_data) {
            var ks_updated_data = _.map(this.ks_theme_global_data.ks_color_theme.custom, function(theme) {
                if (theme.id == updated_data.id)
                    return updated_data;
                else
                    return theme;
            });
            this.ks_theme_global_data.ks_color_theme.custom = ks_updated_data;
        }
//
        _ksColorThemeDelete(ev) {
            var self = this;
            var ks_theme_id = parseInt($(ev.currentTarget).attr("data-theme-id"));
            $("div.ks_theme_selected").removeClass("ks_theme_selected");
            $(ev.currentTarget.parentElement.parentElement).addClass("ks_theme_selected");
            if (ks_theme_id) {
                Dialog.confirm(this, this.env._t("Are you sure you want to delete this record ?"), {
                    confirm_callback: function() {
                        return this.__parentedParent.rpc("/web/dataset/call", {
                            model: "ks.color.theme",
                            method: "unlink",
                            args: [ks_theme_id],
                        }).then(function() {
                            var x
                            self._ksRemoveTheme(ks_theme_id);
                            var color_theme_temp = qweb.render("ks_color_theme_qweb_template_global", {
                                ks_theme_global_data: self.ks_theme_global_data,
                            });
                            $("div.ks_color_theme_qweb_div_global").html(color_theme_temp);
                            self._ks_addEventListener_color_theme()
                        });
                    },
                    cancel_callback: ()=>{
                        $("div.ks_theme_selected").removeClass("ks_theme_selected");
                    }
                    ,
                });
            }
        }

        _ksRemoveTheme(ks_theme_id) {
            var result = false;
            var ks_custom_themes = _.filter(this.ks_theme_global_data.ks_color_theme.custom, function(theme) {
                return ks_theme_id != theme.id;
            });
            this.ks_theme_global_data.ks_color_theme.custom = ks_custom_themes;
            return result;
        }

        async _ksLoginPageBgColor(){
            var self=this
            var ks_selected_color = $('#ks_login_bg_color_add').val();
            var res= await ajax.jsonRpc("/ks_curved_backend_theme_enter/add/login/color", "call", {
                data: {
                   value: ks_selected_color
                },
            })
            var ks_template_data=this
            ks_template_data["ks_login_colors"] = res;
            var ks_color_container = qweb.render("ks_login_background_color_template", ks_template_data);
            $("div.ks_login_background_color_container").html(ks_color_container);
            document.querySelector(".ks_add_login_color").addEventListener("click",(ev) =>{this._ksLoginPageBgColor(ev)})
            Object.values(document.querySelectorAll(".ks_login_background_color_1")).map((item)=>{
                item.children[0].addEventListener("change",(ev) =>{this._onInputChange(ev)})
                item.children[2].addEventListener("click",(ev) =>{this._ksDelLoginBackgroundColor(ev)})
            })
        }

        on_detach_callback() {
            this._ksColorThemeCancel();
        }


 }

 KsGlobalConfigWidget.template="ks_global_settings";


 registry.category("view_widgets").add('ks_global_config_widget', KsGlobalConfigWidget);

