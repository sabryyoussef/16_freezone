# -*- coding: utf-8 -*-
{
    'name': "Cabinet Directory",
    'author': "Beshoy Wageh",
    'version': '16.0',
    'depends': ['base','crm','client_documents'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/cabinet.xml',
        'views/folder.xml',
        'views/sub_folder_files.xml',
        'wizard/meeting.xml',
        'wizard/handover.xml',
    ],
}