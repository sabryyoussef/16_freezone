
{
    'name': 'HR Attendance IP MAC Adress',
    'version': '16.0.1.0.1',
    'author': 'Beshoy Wageh',
    'category': 'Human Resources',
    'depends': ['base', 'hr', 'hr_attendance'],
    'data': [
        'views/hr_attendance_views.xml',
    ],
    'external_dependencies': {'python': ['geopy']},
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
