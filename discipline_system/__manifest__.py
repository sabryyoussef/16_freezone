# -*- coding: utf-8 -*-
{
    'name': "Discipline System",

    'category': 'Human Resources/Employees',
    'version': '16.2.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_payroll', 'resource'],

    # always loaded
    'data': [
        'security/security.xml',
        'data/structure.xml',
        'security/rules.xml',
        'security/ir.model.access.csv',
        'wizard/dispute_wizard.xml',
        'views/deductions/deductions_tree_form.xml',
        'views/deductions/menu_action.xml',
        'views/reasons/reasons_tree_form.xml',
        'views/reasons/menu_action.xml',
        'views/payroll/salary_slip.xml',
    ],
    'application': True
}
