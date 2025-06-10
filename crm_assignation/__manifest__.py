# -*- coding: utf-8 -*-
{
    'name': "CRM Assignation",

    'author': "Ziad Habiba",

    'category': 'Sales/CRM',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'crm'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/mail.xml',
        'views/assign_wizard.xml',
        'views/crm.xml',
    ],
}
