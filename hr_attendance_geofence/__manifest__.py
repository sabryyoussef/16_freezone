# -*- coding: utf-8 -*-
#################################################################################
# Author      : CFIS (<https://www.cfis.store/>)
# Copyright(c): 2017-Present CFIS.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://www.cfis.store/>
#################################################################################

{
    "name": "HR Attendance Geofence | Geo-Fencing | Geofencing | Geofence | Geolocation | Attendance Geolocation | Attendance Location Restriction",
    "summary": """
        The odoo Hr Attendance Manager / Administrators can use this module to create a virtual geographic boundary 
        for attendance locations, and employees can only check in and out within one of these Geofence areas.
    """,
    "version": "16.0.1",
    "description": """
        The odoo Hr Attendance Manager / Administrators can use this module to create a virtual geographic boundary 
        for attendance locations, and employees can only check in and out within one of these Geofence areas.
        HR Attendance Geofencing
        Geofencing
        Attendance Geofence          
    """,    
    "author": "CFIS",
    "maintainer": "CFIS",
    "license" :  "Other proprietary",
    "website": "https://www.cfis.store",
    "images": ["images/hr_attendance_geofence.png"],
    "category": "Sales",
    "depends": [
        "base",
        "hr_attendance",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/geolocation_data.xml",
        # "views/assets.xml",
        "views/hr_attendance_geofence.xml",
        "views/hr_attendance_views.xml",
        "views/res_users.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "/hr_attendance_geofence/static/src/js/lib/ol-6.12.0/ol.css",
            "/hr_attendance_geofence/static/src/js/lib/ol-ext/ol-ext.css",
            "/hr_attendance_geofence/static/src/js/lib/ol-6.12.0/ol.js",
            "/hr_attendance_geofence/static/src/js/lib/ol-ext/ol-ext.js",
            
            "/hr_attendance_geofence/static/src/css/style.css",
            "/hr_attendance_geofence/static/src/js/user_menu.js",

            "/hr_attendance_geofence/static/src/js/geofence_drawing.js",
            "/hr_attendance_geofence/static/src/js/geofence_model.js",
            "/hr_attendance_geofence/static/src/js/geofence_controller.js",
            "/hr_attendance_geofence/static/src/js/geofence_renderer.js",
            "/hr_attendance_geofence/static/src/js/geofence_view.js",

            "/hr_attendance_geofence/static/src/js/geofence_common.js",
            "/hr_attendance_geofence/static/src/js/my_attendances.js",

            "/hr_attendance_geofence/static/src/xml/*.xml",
        ],
    },   
    "installable": True,
    "application": True,
    "price"                 :  150.00,
    "currency"              :  "EUR",
    "pre_init_hook"         :  "pre_init_check",
    'uninstall_hook': 'uninstall_hook',
}
