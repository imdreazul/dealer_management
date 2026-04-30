# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_dealer = fields.Boolean(string='Is Dealer', default=False, index=True)
    dealer_application_id = fields.Many2one(
        'dealership.application',
        string='Dealer Application',
        compute='_compute_dealer_application',
        store=False
    )
    dealer_since = fields.Date(string='Dealer Since')
    dealer_website = fields.Char(string='Dealer Website URL')
    shop_image = fields.Binary(
        string='Shop Image',
        related='dealer_application_id.shop_image',
        readonly=True
    )
    # Geo coordinates for map (Find a Dealer)
    geo_lat = fields.Float(string='Latitude', digits=(10, 7))
    geo_lng = fields.Float(string='Longitude', digits=(10, 7))

    def _compute_dealer_application(self):
        Application = self.env['dealership.application']
        for partner in self:
            app = Application.search(
                [('partner_id', '=', partner.id)], limit=1
            )
            partner.dealer_application_id = app
