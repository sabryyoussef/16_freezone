# -*- coding: utf-8 -*-
{
    'name': "Client's Projects",

    'author': "Ziad Habiba",

    'category': 'Project',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base','project'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/client_projects_form_view.xml',
        'views/client_projects_kanban_view.xml',
        'views/client_projects.xml',
    ],
}
