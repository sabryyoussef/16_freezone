# -*- coding: utf-8 -*-
{
    'name': "Client Birthday",

    'author': "Ziad Habiba",
    'category': 'Sales/CRM',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'contacts'],

    # always loaded
    'data': [
        'views/partner.xml',
        'data/cron.xml',
        'data/mail.xml',
    ],
}
