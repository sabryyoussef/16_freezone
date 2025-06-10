# -*- coding: utf-8 -*-
{
    'name': "Sale Approval",
    'author': "BeshoyWageh",
    'version': '0.1',
    'depends': ['base','sale','approvals','project','freezoner_custom'],
    'data': [
        'data/data.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/sale.xml',
        'views/project.xml',
    ],
}
