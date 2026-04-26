# -*- coding: utf-8 -*-
from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_dealer = fields.Boolean(string='Is Dealer', default=False)
    dealer_id = fields.Many2one('dealer.dealer', string='Dealer Profile')
