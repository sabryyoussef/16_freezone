/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadBundle } from "@web/core/assets";

const { Component, onMounted, onWillStart, onWillUnmount, onWillUpdateProps, useEffect, useRef} = owl;

export class GeofenceDrawing extends Component {
    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.mapContainerRef = useRef("mapContainer");

        this.olmap = null;
        this.isDrawingEnabled = false;

        if (!this.props.value) {
            this.props.value = 'Empty';
        }

        useEffect(
            () => {
                this.olmap = new ol.Map({
                    layers: [
                        new ol.layer.Tile({
                            source: new ol.source.OSM(),
                        })],
                    view: new ol.View({
                        center: ol.proj.fromLonLat([0, 0]),
                        zoom: 0,
                    }),
                });
                this.olmap.setTarget(this.mapContainerRef.el);
                this.olmap.updateSize();
                if (this.olmap){
                    this.addLayerVector();
                }
            },
            () => []
        );
        useEffect(() => {
            this.updateMap();
        });

        onWillStart(this.onWillStart);
        onMounted(this.onMounted);
    }

    async onWillStart() {
        await loadBundle({
            cssLibs: [
                '/hr_attendance_geofence/static/src/js/lib/ol-6.12.0/ol.css',
                '/hr_attendance_geofence/static/src/js/lib/ol-ext/ol-ext.css',
            ],
            jsLibs: [
                '/hr_attendance_geofence/static/src/js/lib/ol-6.12.0/ol.js',
                '/hr_attendance_geofence/static/src/js/lib/ol-ext/ol-ext.js',
            ],
        });
    }

    onMounted() {
        if(this.olmap){
            this.olmap.updateSize();
        }
    }

    addLayerVector(){
        if (!this.vectorSource) {
            this.vectorSource = new ol.source.Vector();
        }
        if (!this.vectorLayer) {
            this.vectorLayer = new ol.layer.Vector({
                source: this.vectorSource,
                name: 'vectorSource',
                style: new ol.style.Style({
                    fill: new ol.style.Fill({
                        color: 'rgb(255 235 59 / 62%)',
                    }),
                    stroke: new ol.style.Stroke({
                        color: '#ffc107',
                        width: 2,
                    }),
                    image: new ol.style.Circle({
                        radius: 7,
                        fill: new ol.style.Fill({
                            color: '#ffc107',
                        }),
                    }),
                }),
            });
            this.olmap.addLayer(this.vectorLayer);
        }
        if (this.props.value && this.props.value != 'Empty') {                
            var readFeatures = new ol.format.GeoJSON().readFeatures(this.props.value);
            this.vectorSource.addFeatures(readFeatures);
            _.each(this.vectorSource.getFeatures(), function (feature) {
                feature.setStyle(
                    new ol.style.Style({
                        fill: new ol.style.Fill({
                            color: 'rgb(255 235 59 / 62%)',
                        }),
                        stroke: new ol.style.Stroke({
                            color: '#ffc107',
                            width: 2,
                        }),
                        image: new ol.style.Circle({
                            radius: 7,
                            fill: new ol.style.Fill({
                                color: '#ffc107',
                            }),
                        }),
                    })
                );
            });
        }
    }

    updateMap() {
        this.addPolygonDrawingControl();
        this.addPolygonClearControl();
    }

    addPolygonDrawingControl(){
        var buttonElement = document.createElement('button');
        buttonElement.innerHTML = '<i class="fa fa-pencil" style="cursor: pointer !important;"></i>';
        buttonElement.id = 'ol-draw';
        buttonElement.addEventListener('click', this.drawingPolygon.bind(this));

        var divElement = document.createElement('div');
        divElement.className = 'ol-draw ol-unselectable ol-control';
        divElement.appendChild(buttonElement);

        this._OnStartPolygonDrawControl = new ol.control.Control({
            element: divElement
        });
        this.olmap.addControl(this._OnStartPolygonDrawControl);
    }

    drawingPolygon(e) {
        if (this.isDrawingEnabled) {
            console.log("you can't edit or draw features");
            return null;
        }
        var self = this;
        this.olmap.removeInteraction(this.draw);
        this.isDrawingEnabled = !this.isDrawingEnabled;
        var geometryFunction = null;
        if (this.isDrawingEnabled) {
            $(this.mapContainerRef.el).find("#btn-olmap-edit").html("<i class='fa fa-play'></i>");
            this.isDrawingEnabled = false;

            this.draw = new ol.interaction.Draw({
                source: self.vectorSource,
                type: 'Polygon',
                geometryFunction: geometryFunction,
                name: 'draw',
            });

            this.olmap.addInteraction(this.draw);
            this.draw.on('drawend', this.drawingPolygonDrawEnd.bind(this));
            this.draw.on('drawstart', function (e) {
                self.vectorSource.clear();
            });

            this.modify = new ol.interaction.Modify({
                source: this.vectorSource,
                name: 'modify',
            });
            this.olmap.addInteraction(this.modify);
            this.modify.on('modifyend', this.drawingPolygonDrawEnd.bind(this));

            this.snap = new ol.interaction.Snap({
                source: this.vectorSource,
                name: 'snap',
            });
            this.olmap.addInteraction(this.snap);
        } else {
            $(this.mapContainerRef.el).find("#btn-olmap-edit").html("<i class='fa fa-pencil'></i>");
            ol.Observable.unByKey(this.key);
        }
    }

    drawingPolygonDrawEnd(e) {
        var self = this;
        if (!this.isDrawingEnabled){
            this.isDrawingEnabled = false;
            if (this.draw) {
                this.olmap.removeInteraction(this.draw);
            }
            if (this.snap) {
                this.olmap.removeInteraction(this.snap);
            }
            if (this.modify) {
                this.olmap.removeInteraction(this.modify);
            }
            $(this.mapContainerRef.el).find("#btn-olmap-edit").html("<i class='fa fa-pencil'></i>");
            setTimeout(function () {
                self.fieldChanged();
            }, 100);
        }
    }

    addPolygonClearControl() {
        var buttonElement = document.createElement('button');
        buttonElement.innerHTML = '<i class="fa fa-trash" style="cursor: pointer !important;"></i>';
        buttonElement.id = 'ol-clear';
        buttonElement.addEventListener('click', this.clearPolygon.bind(this));

        var divElement = document.createElement('div');
        divElement.className = 'ol-clear ol-unselectable ol-control';
        divElement.appendChild(buttonElement);

        this._OnDeletePolygonDrawControl = new ol.control.Control({
            element: divElement
        });
        this.olmap.addControl(this._OnDeletePolygonDrawControl);
    }

    clearPolygon() {
        var self = this;
        this.isDrawingEnabled = false;
        if (this.draw) {
            this.olmap.removeInteraction(this.draw);
        }
        if (this.snap) {
            this.olmap.removeInteraction(this.snap);
        }
        if (this.modify) {
            this.olmap.removeInteraction(this.modify);
        }
        self.vectorSource.clear();
        self.fieldChanged();
    }

    fieldChanged() {
        var getFeatures = this.vectorSource.getFeatures();
        var _newValue = new ol.format.GeoJSON().writeFeatures(getFeatures);
        this.props.update(_newValue);
    }
}
GeofenceDrawing.template = "GeofenceDrawingView";

registry.category("fields").add("geofence_drawing", GeofenceDrawing);
