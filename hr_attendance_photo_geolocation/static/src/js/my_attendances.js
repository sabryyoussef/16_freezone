odoo.define('hr_attendance_photo_geolocation.my_attendances', function (require) {
    "use strict";

    var MyAttendances = require('hr_attendance.my_attendances');
    var session = require("web.session");
    var Dialog = require('web.Dialog');

    var core = require('web.core');
    var _t = core._t;

    var MyAttendances = MyAttendances.include({
        cssLibs: [],
        jsLibs: [],
        events: _.extend({}, MyAttendances.prototype.events, {
            'click .glocation_kisok_toggle': '_toggle_glocation',
        }),
        willStart: function () {
            var self = this;
            var superDef = this._super.apply(this, arguments);                             
            return Promise.all([superDef]);
        },
        start: function () {
            var self = this;
            this.olmap = null;
            this.ip = null;            
            return this._super.apply(this, arguments).then(function () {
                if (window.location.protocol == 'https:') {
                    self.def_geolocation = $.Deferred();
                    if (session.hr_attendance_geolocation) {
                        self._getGeolocation();
                    }else{
                        self.$('.glocation_kisok_container').css('display','none');
                        self.def_geolocation.resolve();
                    }
                }                
            });
        },
        on_attach_callback: function () {
            this._super.apply(this, arguments);            
        },                
        _toggle_glocation: function () {
            var self = this;
            if (self.$(".glocation_kisok_toggle").hasClass('fa-angle-double-down')) {
                self.$('.glocation_kisok_view').toggle('show');
                self.$("i.glocation_kisok_toggle", self).toggleClass("fa-angle-double-down fa-angle-double-up");
                if (self.latitude && self.longitude){
                    self.$('.glocation_kisok_view span')[0].innerText =  "Lattitude:" + self.latitude + ", Longitude:" + self.longitude ;
                }
            } else {
                self.$('.glocation_kisok_view').toggle('hide');
                self.$("i.glocation_kisok_toggle", self).toggleClass("fa-angle-double-up fa-angle-double-down");                
            }
        },
        _getGeolocation: function () {
            var self = this;
            var options = {
                enableHighAccuracy: true,
                maximumAge: 30000,
                timeout: 27000
            };
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(successCallback, errorCallback, options);
            } else {
                self.geolocation = false;
                self.def_geolocation.resolve();
            }

            function successCallback(position) {
                self.latitude = position.coords.latitude;
                self.longitude = position.coords.longitude;
                self.$('.glocation_kisok_container').css('display','');
                self.def_geolocation.resolve();
            }

            function errorCallback(err) {
                switch (err.code) {
                    case err.PERMISSION_DENIED:
                        console.log("The request for geolocation was refused by the user.");
                        break;
                    case err.POSITION_UNAVAILABLE:
                        console.log("There is no information about the location available.");
                        break;
                    case err.TIMEOUT:
                        console.log("The request for the user's location was unsuccessful.");
                        break;
                    case err.UNKNOWN_ERROR:
                        console.log("An unidentified error has occurred.");
                        break;
                }
                self.def_geolocation.reject();
            }            
        },
        update_attendance: function () {
            var self = this;
            if (window.location.protocol == 'https:') {
                self._validate_attendances();
            }else {
                this._rpc({
                    model: 'hr.employee',
                    method: 'attendance_manual',
                    args: [[self.employee.id], 'hr_attendance.hr_attendance_action_my_attendances'],
                })
                .then(function(result) {
                    if (result.action) {
                        var action = result.action;
                        self.do_action(action);                         
                    } else if (result.warning) {
                        self.do_warn(result.warning);
                    }
                });
            }
        },

        _validate_attendances: function(){
            var self = this;
            self.data_latitude = null;
            self.data_longitude = null;       
            self.data_photo = false;          

            self.def_geolocation_data = new $.Deferred();
            if (session.hr_attendance_geolocation) {                
                if (window.location.protocol == 'https:') {
                self._validate_Geolocation();
            }else{
                self.def_geolocation_data.resolve();
            }
            }else{
                self.def_geolocation_data.resolve();
            }

            self.def_photo_data = new $.Deferred();
            if (session.hr_attendance_photo) {                
                if (window.location.protocol == 'https:') {
                self._validate_Photo();
            }else{
                self.def_photo_data.resolve();
            }
            }else{
                self.def_photo_data.resolve();
            }

            $.when(self.def_geolocation_data, self.def_photo_data).then(function(){
                self._manual_attendance(self.data_latitude, self.data_longitude, self.data_photo);
            })
        },

        _validate_Photo: function () {
            var self = this;
            this.dialogPhoto = new Dialog(this, {
                size: 'medium',
                title: _t("Capture Snapshot"),
                $content: `
                <div class="container-fluid">
                    <div class="col-12 controls">
                        <fieldset class="reader-config-group">
                            <div class="row">
                                <div class="col-3">
                                    <label>
                                        <span>Select Camera</span>
                                    </label>
                                </div>
                                <div class="col-6">
                                    <select name="video_source" class="videoSource" id="videoSource">                                       
                                    </select>
                                </div>
                                <div class="col-3">
                                </div>
                            </div>
                        </fieldset>
                    </div>
                    <div class="row">                                
                        <div class="col-12" id="videoContainer">
                            <video autoplay muted playsinline id="video" style="width: 100%; max-height: 100%; box-sizing: border-box;" autoplay="1"/>
                            <canvas id="image" style="display: none;"/>
                        </div>
                    </div>
                </div>`,
                buttons: [
                    {
                        text: _t("Capture Snapshot"), classes: 'btn-primary captureSnapshot',
                    },
                    {
                        text: _t("Close"), classes: 'btn-secondary captureClose', close: true,
                    }
                ]
            }).open();

            this.dialogPhoto.opened().then(async function () {
                var videoElement = self.dialogPhoto.$('#video').get(0);
                var videoSelect = self.dialogPhoto.$('select#videoSource').get(0);
                videoSelect.onchange = getStream;

                getStream().then(getDevices).then(gotDevices);

                function getStream() {
                    if (window.stream) {
                        window.stream.getTracks().forEach(track => {
                            track.stop();
                        });
                    }
                    const videoSource = videoSelect.value;
                    const constraints = {
                        video: { deviceId: videoSource ? { exact: videoSource } : undefined }
                    };
                    return navigator.mediaDevices.getUserMedia(constraints).then(gotStream).catch(handleError);
                }

                function getDevices() {
                    return navigator.mediaDevices.enumerateDevices();
                }

                function gotDevices(deviceInfos) {
                    window.deviceInfos = deviceInfos;
                    for (const deviceInfo of deviceInfos) {
                        const option = document.createElement('option');
                        option.value = deviceInfo.deviceId;
                        if (deviceInfo.kind === 'videoinput') {
                            option.text = deviceInfo.label || "Camera" + (videoSelect.length + 1) + "";
                            videoSelect.appendChild(option);
                        }
                    }
                }

                function gotStream(stream) {
                    window.stream = stream;
                    videoSelect.selectedIndex = [...videoSelect.options].
                        findIndex(option => option.text === stream.getVideoTracks()[0].label);
                    videoElement.srcObject = stream;
                }

                function handleError(error) {
                    console.error('Error: ', error);
                }

                var $captureSnapshot = self.dialogPhoto.$footer.find('.captureSnapshot');
                var $closeBtn = self.dialogPhoto.$footer.find('.captureClose');

                $captureSnapshot.on('click', function (event) {
                    var img64 = "";
                    var image = self.dialogPhoto.$('#image').get(0);
                    image.width = $(video).width();
                    image.height = $(video).height();
                    image.getContext('2d').drawImage(video, 0, 0, image.width, image.height);
                    var img64 = image.toDataURL("image/jpeg");
                    img64 = img64.replace(/^data:image\/(png|jpg|jpeg|webp);base64,/, "");
                    if (img64) {
                        self.data_photo = img64;
                        self.def_photo_data.resolve();
                        $closeBtn.click();
                    }else{
                        self.def_photo_data.reject();
                    }
                    $captureSnapshot.text("uploading....").addClass('disabled');
                });

            });
        },

        _validate_Geolocation: function(){
            var self = this;
            if (self.latitude && self.longitude){
                self.data_latitude = self.latitude || null;
                self.data_longitude = self.longitude || null;
                self.def_geolocation_data.resolve();
            }else{
                self.def_geolocation_data.reject();
            }     
        },
        
        _manual_attendance: function (data_latitude, data_longitude, data_photo) {
            var self = this;
            var data_latitude = self.data_latitude || null;
            var data_longitude = self.data_longitude || null;
            var data_photo = self.data_photo || null;
            this._rpc({
                model: 'hr.employee',
                method: 'attendance_manual',
                args: [[self.employee.id], 'hr_attendance.hr_attendance_action_my_attendances', null, [data_latitude, data_longitude], [data_photo]],
            }).then(function (result) {
                if (result.action) {
                    var action = result.action;
                    self.do_action(action);
                    if (window.stream) {
                        window.stream.getTracks().forEach(track => {
                            track.stop();
                        });
                    }
                } else if (result.warning) {
                    self.do_warn(result.warning);
                }
            });
        },
    });
});
