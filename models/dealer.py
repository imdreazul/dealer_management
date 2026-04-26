# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import math


class DealerDealer(models.Model):
    _name = 'dealer.dealer'
    _description = 'Dealer'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # ── Identity ──────────────────────────────────────────────────────────────
    name = fields.Char(string='Business Name', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    application_id = fields.Many2one(
        'dealer.application', string='Original Application', readonly=True)
    plan_id = fields.Many2one('dealer.plan', string='Plan', tracking=True)
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    website_url = fields.Char(string='Website')
    logo = fields.Binary(string='Logo', attachment=True)
    description = fields.Html(string='About')

    # ── Location ──────────────────────────────────────────────────────────────
    street = fields.Char(string='Street')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    country_id = fields.Many2one('res.country', string='Country')
    zip_code = fields.Char(string='ZIP')
    latitude = fields.Float(string='Latitude', digits=(10, 7))
    longitude = fields.Float(string='Longitude', digits=(10, 7))
    space_type = fields.Selection([
        ('shop', 'Shop'), ('office', 'Office'),
        ('showroom', 'Showroom'), ('warehouse', 'Warehouse'), ('other', 'Other'),
    ], string='Space Type')

    # ── Status ────────────────────────────────────────────────────────────────
    active = fields.Boolean(default=True)
    is_website_published = fields.Boolean(
        string='Published on Website', default=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('expired', 'Expired'),
    ], string='Status', default='active', tracking=True)

    # ── Images ────────────────────────────────────────────────────────────────
    shop_image_ids = fields.Many2many(
        'ir.attachment', 'dealer_shop_image_rel',
        'dealer_id', 'attachment_id',
        string='Shop Images')

    # ── Review / Rating ───────────────────────────────────────────────────────
    review_ids = fields.One2many(
        'dealer.review', 'dealer_id', string='Reviews')
    review_count = fields.Integer(
        compute='_compute_review_stats', string='Review Count')
    avg_rating = fields.Float(
        compute='_compute_review_stats', string='Avg Rating', store=True)

    # ── Related sale orders ───────────────────────────────────────────────────
    sale_order_ids = fields.One2many(
        'sale.order', 'dealer_id', string='Sale Orders')
    sale_order_count = fields.Integer(
        compute='_compute_sale_order_count', string='Orders')

    # ── Plan expiry ───────────────────────────────────────────────────────────
    plan_start_date = fields.Date(
        string='Plan Start Date', default=fields.Date.today)
    plan_expiry_date = fields.Date(string='Plan Expiry Date')
    days_until_expiry = fields.Integer(
        compute='_compute_days_until_expiry', string='Days Until Expiry')

    @api.depends('review_ids.rating')
    def _compute_review_stats(self):
        for rec in self:
            reviews = rec.review_ids.filtered(
                lambda r: r.state == 'approved')
            rec.review_count = len(reviews)
            rec.avg_rating = (
                sum(reviews.mapped('rating')) / len(reviews)
                if reviews else 0.0)

    def _compute_sale_order_count(self):
        for rec in self:
            rec.sale_order_count = len(rec.sale_order_ids)

    def _compute_days_until_expiry(self):
        today = fields.Date.today()
        for rec in self:
            if rec.plan_expiry_date:
                delta = (rec.plan_expiry_date - today).days
                rec.days_until_expiry = delta
            else:
                rec.days_until_expiry = 0

    @api.model
    def get_dealers_for_map(self, lat=None, lng=None):
        """Return dealer data with optional distance calculation."""
        dealers = self.search([
            ('is_website_published', '=', True),
            ('state', '=', 'active'),
        ])
        result = []
        for d in dealers:
            dist = None
            if lat and lng and d.latitude and d.longitude:
                dist = self._haversine(
                    float(lat), float(lng),
                    d.latitude, d.longitude)
            images = []
            for att in d.shop_image_ids[:3]:
                images.append(f'/web/image/ir.attachment/{att.id}/datas')
            result.append({
                'id': d.id,
                'name': d.name,
                'city': d.city or '',
                'state': d.state_id.name if d.state_id else '',
                'country': d.country_id.name if d.country_id else '',
                'lat': d.latitude,
                'lng': d.longitude,
                'phone': d.phone or '',
                'email': d.email or '',
                'website': d.website_url or '',
                'plan': d.plan_id.name if d.plan_id else '',
                'rating': round(d.avg_rating, 1),
                'review_count': d.review_count,
                'distance_km': round(dist, 2) if dist is not None else None,
                'images': images,
                'space_type': d.space_type or '',
            })
        if lat and lng:
            result.sort(key=lambda x: x['distance_km'] or 9999)
        return result

    @staticmethod
    def _haversine(lat1, lon1, lat2, lon2):
        R = 6371
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + \
            math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def action_view_orders(self):
        self.ensure_one()
        return {
            'name': 'Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            # Replace 'partner_id' with how you link the sale order to the dealer
            'domain': [('partner_id', '=', self.partner_id.id)],
            'context': {'default_partner_id': self.partner_id.id},
        }


class DealerReview(models.Model):
    _name = 'dealer.review'
    _description = 'Dealer Review'
    _order = 'create_date desc'

    dealer_id = fields.Many2one(
        'dealer.dealer', string='Dealer', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Reviewer')
    reviewer_name = fields.Char(string='Name')
    reviewer_email = fields.Char(string='Email')
    rating = fields.Selection([
        ('1', '1 Star'), ('2', '2 Stars'), ('3', '3 Stars'),
        ('4', '4 Stars'), ('5', '5 Stars'),
    ], string='Rating', required=True, default='5')
    review = fields.Text(string='Review')
    state = fields.Selection([
        ('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'),
    ], default='pending')

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_reject(self):
        self.write({'state': 'rejected'})


    def action_view_reviews(self):
        self.ensure_one()
        return {
            'name': 'Reviews',
            'type': 'ir.actions.act_window',
            'res_model': 'dealer.review',
            'view_mode': 'tree,form',
            # Replace 'dealer_id' with the actual Many2one field name linking the review to the dealer
            'domain': [('dealer_id', '=', self.id)],
            'context': {'default_dealer_id': self.id},
        }
