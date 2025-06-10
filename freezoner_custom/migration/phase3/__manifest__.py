{
    'name': 'Freezoner Phase 3 Migration',
    'version': '1.0',
    'category': 'Project',
    'summary': 'Migration of Freezoner customizations to Odoo 18',
    'description': """
        This module contains the migrated customizations for Freezoner:
        - Project and Task Management
        - Sale Order Management
        - Document Management
        - Partner Management
        - Compliance Management
        - Statement of Values (SOV)
        - Project Products Management
    """,
    'author': 'Freezoner',
    'website': 'https://www.freezoner.com',
    'depends': [
        'base',
        'project',
        'sale',
        'sale_project',
        'account',
        'analytic',
        'mail',
        'web',
        'client_documents',
        'calendar',
        'documents',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/task_views.xml',
        'views/sale_views.xml',
        'views/sov_views.xml',
        'views/project_products_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
} 