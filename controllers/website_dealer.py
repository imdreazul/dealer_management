# -*- coding: utf-8 -*-
import json
import logging
from odoo import http, _
from odoo.http import request

_logger = logging.getLogger(__name__)


class WebsiteDealerController(http.Controller):

    # ── Application Form ──────────────────────────────────────────────────────
    @http.route('/become-a-dealer', type='http', auth='public', website=True)
    def become_dealer_page(self, **kwargs):
        plans = request.env['dealer.plan'].sudo().search([
            ('active', '=', True),
            ('website_published', '=', True),
        ])
        countries = request.env['res.country'].sudo().search([])
        return request.render('dealer_management.website_become_dealer', {
            'plans': plans,
            'countries': countries,
            'error': kwargs.get('error'),
        })

    @http.route('/become-a-dealer/submit', type='http', auth='public',
                website=True, methods=['POST'], csrf=True)
    def submit_dealer_application(self, **post):
        # Validate required fields
        required = ['name', 'email', 'phone', 'company_name',
                    'city', 'plan_id', 'space_type']
        errors = {}
        for field in required:
            if not post.get(field, '').strip():
                errors[field] = _('This field is required.')

        if errors:
            plans = request.env['dealer.plan'].sudo().search([
                ('active', '=', True), ('website_published', '=', True)])
            countries = request.env['res.country'].sudo().search([])
            return request.render('dealer_management.website_become_dealer', {
                'plans': plans,
                'countries': countries,
                'errors': errors,
                'values': post,
            })

        # Parse country/state
        country_id = int(post.get('country_id', 0)) or None
        state_id = int(post.get('state_id', 0)) or None
        plan_id = int(post.get('plan_id', 0))

        try:
            lat = float(post.get('latitude', 0))
            lng = float(post.get('longitude', 0))
        except (ValueError, TypeError):
            lat = lng = 0.0

        application = request.env['dealer.application'].sudo().create({
            'name': post.get('name', '').strip(),
            'email': post.get('email', '').strip(),
            'phone': post.get('phone', '').strip(),
            'company_name': post.get('company_name', '').strip(),
            'website_url': post.get('website_url', '').strip(),
            'plan_id': plan_id,
            'street': post.get('street', '').strip(),
            'city': post.get('city', '').strip(),
            'state_id': state_id,
            'country_id': country_id,
            'zip_code': post.get('zip_code', '').strip(),
            'latitude': lat,
            'longitude': lng,
            'space_type': post.get('space_type', 'shop'),
            'space_area': float(post.get('space_area', 0) or 0),
            'space_ownership': post.get('space_ownership', ''),
        })

        # Handle file uploads
        if request.httprequest.files:
            shop_images = request.httprequest.files.getlist('shop_images')
            docs = request.httprequest.files.getlist('documents')
            for f in shop_images:
                if f and f.filename:
                    att = request.env['ir.attachment'].sudo().create({
                        'name': f.filename,
                        'datas': f.read().encode('base64') if hasattr(f.read(), 'encode') else __import__('base64').b64encode(f.read()).decode(),
                        'res_model': 'dealer.application',
                        'res_id': application.id,
                        'mimetype': f.content_type,
                    })
                    application.sudo().write({
                        'shop_image_ids': [(4, att.id)]})
            for f in docs:
                if f and f.filename:
                    att = request.env['ir.attachment'].sudo().create({
                        'name': f.filename,
                        'datas': __import__('base64').b64encode(f.read()).decode(),
                        'res_model': 'dealer.application',
                        'res_id': application.id,
                        'mimetype': f.content_type,
                    })
                    application.sudo().write({
                        'document_ids': [(4, att.id)]})

        return request.redirect(
            f'/dealer/application/thank-you?ref={application.ref_code}')

    @http.route('/dealer/application/thank-you', type='http',
                auth='public', website=True)
    def dealer_thankyou(self, ref='', **kwargs):
        application = None
        if ref:
            application = request.env['dealer.application'].sudo().search(
                [('ref_code', '=', ref)], limit=1)
        return request.render('dealer_management.website_dealer_thankyou', {
            'application': application,
            'ref': ref,
        })

    # ── Status Tracker (public link) ──────────────────────────────────────────
    @http.route('/dealer/status', type='http', auth='public', website=True)
    def dealer_status_search(self, **kwargs):
        return request.render('dealer_management.website_dealer_status_search', {
            'error': kwargs.get('error', ''),
        })

    @http.route('/dealer/status/check', type='http', auth='public',
                website=True, methods=['POST'], csrf=True)
    def dealer_status_check(self, ref_code='', email='', **kwargs):
        application = request.env['dealer.application'].sudo().search([
            ('ref_code', '=', ref_code.strip()),
            ('email', '=', email.strip().lower()),
        ], limit=1)
        if not application:
            return request.render('dealer_management.website_dealer_status_search', {
                'error': _('No application found with that Reference Code and Email.'),
            })
        return request.redirect(
            f'/dealer/status/{application.ref_code}/{application.portal_token}')

    @http.route('/dealer/status/<string:ref_code>/<string:token>',
                type='http', auth='public', website=True)
    def dealer_status_view(self, ref_code, token, **kwargs):
        application = request.env['dealer.application'].sudo().search([
            ('ref_code', '=', ref_code),
            ('portal_token', '=', token),
        ], limit=1)
        if not application:
            return request.render('website.404')
        return request.render('dealer_management.website_dealer_status', {
            'application': application,
        })

    # ── Find a Dealer ─────────────────────────────────────────────────────────
    @http.route('/find-a-dealer', type='http', auth='public', website=True)
    def find_dealer_page(self, **kwargs):
        api_key = request.env['ir.config_parameter'].sudo().get_param(
            'dealer_management.map_api_key', '')
        return request.render('dealer_management.website_find_dealer', {
            'gmaps_api_key': api_key,
        })

    @http.route('/dealer/map/data', type='json', auth='public', website=True)
    def dealer_map_data(self, lat=None, lng=None, **kwargs):
        dealers = request.env['dealer.dealer'].sudo().get_dealers_for_map(
            lat=lat, lng=lng)
        return {'dealers': dealers}

    @http.route('/dealer/states', type='json', auth='public', website=True)
    def get_states(self, country_id=None, **kwargs):
        if not country_id:
            return []
        states = request.env['res.country.state'].sudo().search([
            ('country_id', '=', int(country_id))])
        return [{'id': s.id, 'name': s.name} for s in states]
