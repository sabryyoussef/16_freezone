# -*- coding: utf-8 -*-
{
    'name': "Sales Commission",
    'author': "Beshoy Wageh",
    'category': 'Sales/Commissions',
    'version': '0.1',
    'depends': ['base', 'sale', 'analytic', 'crm', 'account_budget',
                'sale_management', 'hr_payroll', 'freezoner_custom'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/cron.xml',
        'data/salary_rules.xml',
        'views/sales_team.xml',
        'views/commission.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/sales_commission/static/src/css/commission.css',
        ],
    },
}
