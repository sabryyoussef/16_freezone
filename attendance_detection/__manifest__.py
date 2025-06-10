# -*- coding: utf-8 -*-
{
    'name': "Attendance Detection",

    'category': 'Human Resources/Attendances',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_attendance', 'discipline_system', 'resource', 'hr_holidays'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/resource_calendar.xml',
        'views/employee.xml',
        'views/deduction.xml',
        'data/data.xml',
    ],
}
