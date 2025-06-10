# -*- coding: utf-8 -*-
{
    'name': "HR Leave Custom",
    'author': "Beshoy Wageh",
    'depends': ['base','hr','hr_holidays'],
    'data': [
        'data/data.xml',
        'data/cron.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/leaves.xml',
        'wizard/views.xml',
    ],
}
