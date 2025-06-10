# -*- coding: utf-8 -*-
{
    'name': "Crm Log",
    'author': "BeshoyWageh",
    'version': '0.1',
    'depends': ['base', 'crm','sale','sales_team','client_documents'],
    'data': [
        'data/data.xml',
        'security/lead_security.xml',
        'security/ir.model.access.csv',
        'views/source.xml',
        'views/crm.xml',
        'views/sale.xml',
        'wizard/wizard.xml',
        'wizard/call.xml',

    ],
}
