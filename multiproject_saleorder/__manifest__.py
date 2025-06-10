# -*- coding: utf-8 -*-
{
    'name': "Multi-Project SaleOrder",

    'summary': """""",

    'description': """""",

    'author': "Ziad Habiba",

    'category': 'Services/Project',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'project', 'analytic', 'sale_project', 'analytic'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/data.xml',
        'views/views.xml',
    ],
}
