# -*- coding: utf-8 -*-
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    dealer_auto_email = fields.Boolean(
        string='Send Email on Application',
        config_parameter='dealer_management.auto_email',
        default=True)
    dealer_map_api_key = fields.Char(
        string='Google Maps API Key',
        config_parameter='dealer_management.map_api_key')
    dealer_default_plan_id = fields.Many2one(
        'dealer.plan', string='Default Plan',
        config_parameter='dealer_management.default_plan_id')

    google_maps_api_key = fields.Char(
        string='Google Maps API Key',
        config_parameter='dealer_management.google_maps_api_key',
        help="API key for displaying the dealer locator map."
    )
