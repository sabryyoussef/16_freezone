# -*- coding: utf-8 -*-
{
    'name': "Compliance",
    'author': "Beshoy Wageh",
    'version': '16.0',
    'depends': ['base', 'crm', 'freezoner_custom', 'partner_organization','documents','crm_log'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/business_structure.xml',
        'views/compliance.xml',
        'views/partner.xml',
        'views/config.xml',
        'views/onboarding.xml',
    ],
}