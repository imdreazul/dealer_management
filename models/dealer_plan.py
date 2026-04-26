# -*- coding: utf-8 -*-
from odoo import models, fields, api


class DealerPlan(models.Model):
    _name = 'dealer.plan'
    _description = 'Dealer Plan'
    _order = 'sequence, id'

    name = fields.Char(string='Plan Name', required=True)
    sequence = fields.Integer(default=10)
    plan_type = fields.Selection([
        ('service', 'Service Based'),
        ('showroom', 'Showroom Based'),
        ('both', 'Both'),
    ], string='Plan Type', default='showroom', required=True)
    description = fields.Html(string='Description')
    price = fields.Float(string='Plan Price', required=True)
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.company.currency_id)
    min_investment = fields.Float(string='Minimum Investment')
    max_investment = fields.Float(string='Maximum Investment')
    validity_months = fields.Integer(string='Validity (Months)', default=12)
    product_id = fields.Many2one(
        'product.product', string='Plan Product',
        help='Product used in sale order when this plan is selected')
    active = fields.Boolean(default=True)
    website_published = fields.Boolean(string='Published on Website', default=True)
    color = fields.Integer(string='Color Index')
    dealer_ids = fields.One2many('dealer.dealer', 'plan_id', string='Dealers')
    dealer_count = fields.Integer(compute='_compute_dealer_count', string='Dealers')
    feature_ids = fields.One2many('dealer.plan.feature', 'plan_id', string='Features')
    image = fields.Binary(string='Plan Image')

    def _compute_dealer_count(self):
        for rec in self:
            rec.dealer_count = len(rec.dealer_ids)


class DealerPlanFeature(models.Model):
    _name = 'dealer.plan.feature'
    _description = 'Dealer Plan Feature'
    _order = 'sequence'

    plan_id = fields.Many2one('dealer.plan', string='Plan', ondelete='cascade')
    name = fields.Char(string='Feature', required=True)
    sequence = fields.Integer(default=10)
    included = fields.Boolean(default=True)

    def action_view_dealers(self):
        self.ensure_one()
        return {
            'name': 'Dealers',
            'type': 'ir.actions.act_window',
            # Replace 'dealer.application' with your actual dealer model name if different
            'res_model': 'dealer.application',
            'view_mode': 'tree,form',
            # Replace 'plan_id' with the actual Many2one field name on the dealer model
            'domain': [('plan_id', '=', self.id)],
            'context': {'default_plan_id': self.id},
        }
