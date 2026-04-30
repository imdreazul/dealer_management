# -*- coding: utf-8 -*-
from odoo import fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    dealer_application_id = fields.Many2one(
        'dealership.application',
        string='Dealer Application',
        index=True,
        copy=False,
        help='Link this lead/opportunity to a dealer application'
    )
