# -*- coding: utf-8 -*-
{
    'name': 'Dealer Management',
    'version': '17.0.1.0.0',
    'summary': 'Full Dealer Lifecycle: Apply → Review → Proposal → Payment → Portal Access',
    'description': """
Dealer Management – Odoo 17
============================
Complete dealer onboarding and management system.

Business Flow
-------------
1. Applicant fills the "Become a Dealer" form on the website
   (with location, GPS, shop/office images, documents, plan selection)
2. System auto-generates a Reference Code (DLR/YYYY/NNNNN)
3. Applicant receives a confirmation email with the ref code + status tracker link
4. Admin reviews the application in the backend (Kanban / List / Form)
5. Admin sends a Proposal (Sale Order) to the applicant via a wizard
6. Applicant receives proposal email with order details and total price
7. Sale Order is confirmed → Delivery + Payment processed
8. On delivery done + invoice paid → Dealer is auto-approved
   - Dealer profile created
   - Portal user access granted
   - Congratulations email sent with dashboard link
9. Applicant/Dealer can track status anytime via the public link (no login needed)
10. Dealer logs into portal → Dashboard, Profile, Orders, Plan, Reviews

Website Features
----------------
- /become-a-dealer        → Application form
- /dealer/status          → Track by ref code + email
- /dealer/status/<ref>/<token>  → Direct public status page
- /find-a-dealer          → Google Maps / OpenStreetMap dealer locator
                            with real-time distance calculation

Portal Features
---------------
- /my/dealer/dashboard    → Stats, orders, plan info
- /my/dealer/profile      → Editable profile
- /my/dealer/orders       → All sale orders
- /my/dealer/plan         → Plan comparison & current plan
- /my/dealer/reviews      → Customer reviews

Admin Features
--------------
- Kanban & list pipeline for applications
- Rejection wizard (with reason sent to applicant)
- Proposal wizard (linked to sale order)
- Auto-approval hook on delivery + payment
- Dealer certificate PDF report
- Application summary PDF report
- Google Maps API key configuration
    """,
    'category': 'Generic Modules/Dealer Management',
    'author': "Reazul",
    'website': "https://github.com/imdreazul",
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'website',
        'portal',
        'sale_management',
        'account',
        'contacts',
        'crm',
        'stock',
    ],
    'data': [
        # Security
        'security/dealer_security.xml',
        'security/ir.model.access.csv',

        # Data
        'data/ir_sequence_data.xml',
        'data/mail_template_data.xml',
        'data/dealer_plan_data.xml',

        # Menus (must come after all actions)
        'views/menus.xml',

        # Wizard Views
        'views/wizard_views.xml',

        # Backend Views
        'views/dealer_plan_views.xml',
        'views/dealer_application_views.xml',
        'views/dealer_views.xml',
        'views/res_config_settings_views.xml',


        # Website Templates
        'views/website_dealer_templates.xml',

        # Portal Templates
        'views/portal_dealer_templates.xml',

        # Reports
        'report/dealer_application_report.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'dealer_management/static/src/css/dealer_frontend.css',
            'dealer_management/static/src/js/dealer_apply.js',
            'dealer_management/static/src/js/dealer_locator.js',
        ],
        'web.assets_backend': [
            'dealer_management/static/src/css/dealer_backend.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
