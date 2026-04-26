# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class DealerPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        if 'dealer_count' in counters:
            dealer = request.env['dealer.dealer'].sudo().search([
                ('partner_id', '=', partner.id)], limit=1)
            values['dealer_count'] = 1 if dealer else 0
        return values

    def _get_current_dealer(self):
        partner = request.env.user.partner_id
        return request.env['dealer.dealer'].sudo().search([
            ('partner_id', '=', partner.id)], limit=1)

    # ── Dealer Portal Dashboard ───────────────────────────────────────────────
    @http.route('/my/dealer/dashboard', type='http', auth='user', website=True)
    def dealer_dashboard(self, **kwargs):
        dealer = self._get_current_dealer()
        if not dealer:
            return request.redirect('/become-a-dealer')
        orders = request.env['sale.order'].sudo().search([
            ('partner_id', '=', dealer.partner_id.id)
        ], limit=10, order='date_order desc')
        return request.render('dealer_management.portal_dealer_dashboard', {
            'dealer': dealer,
            'orders': orders,
            'page_name': 'dealer_dashboard',
        })

    # ── Dealer Profile ────────────────────────────────────────────────────────
    @http.route('/my/dealer/profile', type='http', auth='user', website=True)
    def dealer_profile(self, **kwargs):
        dealer = self._get_current_dealer()
        if not dealer:
            return request.redirect('/become-a-dealer')
        countries = request.env['res.country'].sudo().search([])
        return request.render('dealer_management.portal_dealer_profile', {
            'dealer': dealer,
            'countries': countries,
            'page_name': 'dealer_profile',
        })

    @http.route('/my/dealer/profile/save', type='http', auth='user',
                website=True, methods=['POST'], csrf=True)
    def dealer_profile_save(self, **post):
        dealer = self._get_current_dealer()
        if not dealer:
            return request.redirect('/become-a-dealer')
        dealer.sudo().write({
            'name': post.get('company_name', dealer.name),
            'phone': post.get('phone', dealer.phone),
            'website_url': post.get('website_url', dealer.website_url),
            'street': post.get('street', dealer.street),
            'city': post.get('city', dealer.city),
            'description': post.get('description', dealer.description),
        })
        return request.redirect('/my/dealer/profile?success=1')

    # ── Dealer Orders ─────────────────────────────────────────────────────────
    @http.route('/my/dealer/orders', type='http', auth='user', website=True)
    def dealer_orders(self, page=1, **kwargs):
        dealer = self._get_current_dealer()
        if not dealer:
            return request.redirect('/become-a-dealer')
        domain = [('partner_id', '=', dealer.partner_id.id)]
        order_count = request.env['sale.order'].sudo().search_count(domain)
        pager = portal_pager(
            url='/my/dealer/orders',
            total=order_count,
            page=page,
            step=10,
        )
        orders = request.env['sale.order'].sudo().search(
            domain, limit=10,
            offset=pager['offset'],
            order='date_order desc')
        return request.render('dealer_management.portal_dealer_orders', {
            'dealer': dealer,
            'orders': orders,
            'pager': pager,
            'page_name': 'dealer_orders',
        })

    # ── Dealer Plan ───────────────────────────────────────────────────────────
    @http.route('/my/dealer/plan', type='http', auth='user', website=True)
    def dealer_plan(self, **kwargs):
        dealer = self._get_current_dealer()
        if not dealer:
            return request.redirect('/become-a-dealer')
        all_plans = request.env['dealer.plan'].sudo().search([
            ('active', '=', True), ('website_published', '=', True)])
        return request.render('dealer_management.portal_dealer_plan', {
            'dealer': dealer,
            'all_plans': all_plans,
            'page_name': 'dealer_plan',
        })

    # ── Dealer Reviews ────────────────────────────────────────────────────────
    @http.route('/my/dealer/reviews', type='http', auth='user', website=True)
    def dealer_reviews(self, **kwargs):
        dealer = self._get_current_dealer()
        if not dealer:
            return request.redirect('/become-a-dealer')
        reviews = request.env['dealer.review'].sudo().search([
            ('dealer_id', '=', dealer.id),
            ('state', '=', 'approved'),
        ])
        return request.render('dealer_management.portal_dealer_reviews', {
            'dealer': dealer,
            'reviews': reviews,
            'page_name': 'dealer_reviews',
        })

    # ── Submit Review (public) ────────────────────────────────────────────────
    @http.route('/dealer/<int:dealer_id>/review', type='http',
                auth='public', website=True, methods=['POST'], csrf=True)
    def submit_review(self, dealer_id, **post):
        dealer = request.env['dealer.dealer'].sudo().browse(dealer_id)
        if not dealer.exists():
            return request.redirect('/find-a-dealer')
        request.env['dealer.review'].sudo().create({
            'dealer_id': dealer.id,
            'reviewer_name': post.get('reviewer_name', ''),
            'reviewer_email': post.get('reviewer_email', ''),
            'rating': post.get('rating', '5'),
            'review': post.get('review', ''),
        })
        return request.redirect(f'/find-a-dealer?review_submitted=1')
