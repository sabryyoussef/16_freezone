# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
    "name" : "User Audit Management | User Activity Audit | User Audit Log",
    "version" : "16.0.0.1",
    "category" : "Extra Tools",
    'summary': 'User activity tracking user activity logs user activity tracking audit logs track user actions history user action logs track user activity history user session tracking audit log history User Audit Trail user audit rules audit trail rules audit log rules',
    "description": """User Audit Management Odoo App is designed to provide complete transparency and accountability by tracking and recording user activities within the system. This app enables businesses to maintain a detailed audit log of all user actions, ensuring a secure and controlled operational environment. By capturing essential details such as user activities, changes made, and activity type like Read, write, delete, create etc. User can see only the user audit log while the manager can do audit configuration, see the user audit log, and clear the audit log. Audit logs can be group by users, also by object, and by type (Read, write, delete, create). Manager can be clear log using models and types also there would be option to clear all the log.""",
    "author": "BROWSEINFO",
    'website': 'https://www.browseinfo.com/demo-request?app=bi_user_audit_management&version=16&edition=Community',
    "price": 20,
    "currency": 'EUR',
    "depends" : ['base','account','sale'],
    "data": [
        'security/ir.model.access.csv',
        'security/user_audit_security.xml',
        'views/user_audit_configuration.xml',
        'views/user_audit_log.xml',
        'views/menus.xml',
        'wizard/clear_log.xml',
    ],
    'license': 'OPL-1',
    "auto_install": False,
    "installable": True,
    "live_test_url":'https://www.browseinfo.com/demo-request?app=bi_user_audit_management&version=16&edition=Community',
    "images":["static/description/Banner.gif"],
}
