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
    "name": "Check In / Check Out Photo and Geolocation | HR Attendance Photo and Geolocation | Attendance Photo | Attendance Location",
    "summary": """
        This module allows the odoo employees to log the attendance with Photo and Geolocation                
        the module will record employee geolocation and photo.
    """,
    "version": "16.0.1",
    "description": """
        This module allows the odoo employees to log the attendance with Photo and Geolocation                
        the module will record employee geolocation and photo.
        Geolocation
        Photo
    """,    
    "author": "CFIS",
    "maintainer": "CFIS",
    "license" :  "Other proprietary",
    "website": "https://www.cfis.store",
    "images": ["images/hr_attendance_photo_geolocation.png"],
    "category": "Human Resources",
    "depends": [
        "base",
        "hr_attendance",
    ],
    "data": [
        "data/geolocation_data.xml",
        "views/res_config_settings.xml",
        "views/hr_attendance_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "/hr_attendance_photo_geolocation/static/src/css/style.css",
            "/hr_attendance_photo_geolocation/static/src/js/my_attendances.js",

            "/hr_attendance_photo_geolocation/static/src/xml/*.xml",
        ],
    },   
    "installable": True,
    "application": True,
    "price"                 :  48.00,
    "currency"              :  "EUR",
    "pre_init_hook"         :  "pre_init_check",
}
