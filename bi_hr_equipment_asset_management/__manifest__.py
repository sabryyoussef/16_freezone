# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Employee Asset Management | HR Employee Equipment Request and Allocation | Employee Asset History',
    'version': '16.0.0.0',
    'category': 'Human Resources',
    'summary': 'employee asset allocation equipment allocation equipment approval Employee asset request approval office equipment tracking asset tracking employees Employee device request Office equipment Employee IT assets HR equipment IT equipment Assets Allocation',
    'description': """Employee Asset Management Odoo App is designed to streamline the allocation, tracking, and return of company assets assigned to employees. This app enables businesses to efficiently manage employee equipment requests, approvals, and allocations, ensuring a structured and transparent process. With a detailed asset tracking system, organizations can maintain a complete history of issued assets, monitor their status, and track returns, minimizing losses and ensuring accountability. The app helps HR and administrative teams manage employee asset requests seamlessly, keeping records of approvals and tracking asset movements throughout the employee lifecycle. Whether dealing with IT equipment, office supplies, or other company-owned resources, this app provides an organized approach to asset management, improving visibility, control, and overall asset utilization.""",
    'author': 'BROWSEINFO',
    'website': 'https://www.browseinfo.com/demo-request?app=bi_hr_equipment_asset_management&version=16&edition=Community',
    "price":25,
    "currency": 'EUR',
    'depends': ['base','hr','hr_maintenance','mail'],
    'data': [
                'data/mail.xml',
                'report/equipment_asset_report.xml',
                'security/ir.model.access.csv',
                'security/user_access_groups.xml',
                'views/equipment_request.xml',
                'views/inherit_equipment.xml'   
            ],
    'installable': True,
    'auto_install': False,
    'application': True,
    "license":'OPL-1',
    "live_test_url":'https://www.browseinfo.com/demo-request?app=bi_hr_equipment_asset_management&version=16&edition=Community',
    "images":["static/description/Banner.gif"],
}
