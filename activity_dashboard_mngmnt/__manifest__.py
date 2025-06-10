{
    'name': 'Activity Management',
    'version': '16.0.1.1.1',
    'category': 'Tools',
    'summary': 'Advance Activity Management and Dashboard View.',
    'author': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'description': "Advance Activity Management and Dashboard View to track "
                   "activity of users.",
    'depends': ['base', 'mail','hr'],
    'images': ['static/description/banner.png'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/mail_activity_views.xml',
        'views/activity_tag_views.xml',
        'views/message.xml',
        'views/activity_dashbord.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'activity_dashboard_mngmnt/static/src/css/dashboard.css',
            'activity_dashboard_mngmnt/static/src/css/style.scss',
            'activity_dashboard_mngmnt/static/src/css/material-gauge.css',
            'activity_dashboard_mngmnt/static/src/xml/activity_dashboard_view.xml',
            'activity_dashboard_mngmnt/static/src/js/activity_dashboard.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
