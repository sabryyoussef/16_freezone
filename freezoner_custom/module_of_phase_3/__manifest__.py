{
    'name': 'Freezoner Complex Models',
    'version': '1.0',
    'category': 'Project Management',
    'summary': 'Complex models and relations for enhanced project management',
    'description': """
        Phase 3: Complex Models and Relations
        ====================================
        
        This module extends the base project management functionality with:
        * Complex project hierarchies and relationships
        * Advanced task management and dependencies
        * Enhanced document management and workflows
        * Sophisticated partner and compliance tracking
        * Multi-level approval workflows
        * Advanced reporting and analytics
    """,
    'author': 'Freezoner',
    'website': 'https://www.freezoner.com',
    'depends': [
        'base',
        'project',
        'documents',
        'mail',
        'web',
        'freezoner_custom.migration_phase2',  # Depends on phase 2
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/project_complex_views.xml',
        'views/task_complex_views.xml',
        'views/document_complex_views.xml',
        'views/partner_complex_views.xml',
        'views/compliance_views.xml',
        'views/workflow_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
} 