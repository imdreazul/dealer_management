# -*- coding: utf-8 -*-
{
    'name': 'Dealer Management',
    'version': '1.0',
    'summary': 'Manage Dealer Applications, Contracts, Portal Access & Website Integration',
    'description': """
        Dealer Management Module for Odoo 17
        =====================================
        Features:
        - Dealer Application with multi-step approval workflow
        - Dealership Contracts with sale order linkage
        - Portal access for approved dealers
        - Website: Become a Dealer form
        - Website: Dealer Profile page
        - Website: Find a Dealer with map
        - Email notifications at every stage
        - Security groups: Dealer User & Dealer Manager
        - PDF reports for Application & Contract
    """,
    'author': "Reazul",
    'website': "https://github.com/imdreazul",
    'category': 'Generic Modules/Sales',
    'depends': [
        'base',
        'mail',
        'sale_management',
        'crm',
        'sale_crm',
        'website',
        'portal',
        'stock',
        'account',
        'web',
        'sale_stock',
    ],
    'data': [
        # Security (must come first)
        'security/dealer_security.xml',
        'security/dealer_rules.xml',
        'security/ir.model.access.csv',
        # Data
        'data/sequence_data.xml',
        'data/mail_template_data.xml',
        'data/cron_data.xml',
        # Backend Views
        'views/dealership_application_views.xml',
        'views/dealership_contract_views.xml',
        'views/res_partner_views.xml',
        'views/menu_views.xml',
        # Reports
        'report/dealer_reports.xml',
        # Website Menus & Portal
        'website/templates/website_menus.xml',
        'website/templates/portal_dealer.xml',
        # Website Templates
        'website/templates/become_dealer.xml',
        'website/templates/application_status.xml',
        'website/templates/dealer_profile.xml',
        'website/templates/find_dealer.xml',
        # Wizards
        'wizard/dealer_approval_wizard_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'dealer_management/static/src/css/dealer_frontend.css',
            'dealer_management/static/src/js/dealer_map.js',
            'dealer_management/static/src/js/become_dealer.js',
        ],
        'web.assets_backend': [
            'dealer_management/static/src/css/dealer_backend.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
