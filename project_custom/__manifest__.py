{
    'name': "Project Custom",
    'author': "BeshoyWageh",
    'version': '16.0',
    'depends': ['base', 'freezoner_custom','compliance_cycle','partner_custom',
                'client_documents','partner_custom','partner_custom_fields'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/document.xml',
        'views/partner.xml',
        'views/project.xml',
        'views/project_fields.xml',
        'views/task.xml',
        'views/milestone.xml',
        'views/views.xml',
    ],
}
