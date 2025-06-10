# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

{
    'name': 'Partner Statement Report',
    'version': '16.0.1.1',
    'category': 'Accounting/Accounting',
    'summary': "This module allows us to print or send reports of individual and all partners. We can view details of multiple partners at the same time and can also apply date filters. | partner statement | Statement | invoice Statement",
    'description': """
Partner Statement Report module is used to Print and Send Individual or all Partner's Statement.
====================================================================================
    """,
    'license': 'OPL-1',
    'author': 'Kanak Infosystems LLP.',
    'website': 'https://www.kanakinfosystems.com',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'report/report_qweb.xml',
        'report/report_view.xml',
        'views/statement_view.xml',
        'views/res_config_settings_views.xml',
        'wizard/partner_statement_wizard.xml',
        'data/mail_template_data.xml',
        'data/data.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'sequence': 1,
    'installable': True,
    'price': 30,
    'currency': 'EUR',
    'live_test_url': 'https://www.youtube.com/watch?v=SbZYbNjk-2Q',
}
