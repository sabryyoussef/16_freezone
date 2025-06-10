# -*- coding: utf-8 -*-
{
    'name': "HR Salary Certificate",
    'version': "16.0.0.0.1",
    'category': 'hr',
    'summary': "It will provide an option to generate employee salary certificate. At anytime you can create a salary certificate by providing necessary information.",
    'author': 'Santhi',
    'license': 'OPL-1',
    'price': 5,
    'currency': 'USD',
    'description': """
    This module contains the Employee Salary Certificate Feature.

        * Create a Salary certificate as a record.
        * Provide necessary employee's details.
        * Then go to the action and click Salary Certificate print.
    """,
    'depends': ['base', 'web', 'hr','hr_employee_custom','sign'],
    'qweb': [],
    'images':['static/description/cover.png'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'reports/salary_certificate_paper_format.xml',
        'reports/salary_certificate_report1.xml',
        'reports/salary_certificate_report2.xml',
        'views/salary_certificate_views.xml',
        'views/views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}
