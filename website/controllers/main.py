# -*- coding: utf-8 -*-
import json
import base64
import logging
from odoo import http, _, fields
from odoo.http import request
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class DealerWebsiteController(http.Controller):

    # ═══════════════════════════════════════════════════════════════
    #  HELPERS
    # ═══════════════════════════════════════════════════════════════

    def _get_base_vals(self):
        """Common template values."""
        return {
            'countries': request.env['res.country'].sudo().search([], order='name asc'),
            'error': {},
            'success': False,
        }

    # ═══════════════════════════════════════════════════════════════
    #  BECOME A DEALER – GET (show form)
    # ═══════════════════════════════════════════════════════════════

    @http.route('/become-a-dealer', type='http', auth='public', website=True, sitemap=True)
    def become_dealer_page(self, **kwargs):
        vals = self._get_base_vals()
        return request.render('dealer_management.template_become_dealer', vals)

    # ═══════════════════════════════════════════════════════════════
    #  BECOME A DEALER – POST (submit form)
    # ═══════════════════════════════════════════════════════════════

    @http.route(
        '/become-a-dealer/submit',
        type='http', auth='public', website=True,
        methods=['POST'], csrf=True
    )
    def become_dealer_submit(self, **post):
        error = {}
        countries = request.env['res.country'].sudo().search([], order='name asc')

        # ── Validation ──────────────────────────────────────────
        for fld in ['name', 'email', 'phone']:
            if not post.get(fld, '').strip():
                error[fld] = _('This field is required.')
        if post.get('email') and '@' not in post['email']:
            error['email'] = _('Please enter a valid email address.')

        if error:
            return request.render('dealer_management.template_become_dealer', {
                'countries': countries,
                'error': error,
                'values': post,
                'success': False,
            })

        # ── Build experience lines ───────────────────────────────
        experience_vals = []
        for i in range(20):
            company = post.get(f'exp_company_{i}', '').strip()
            if not company:
                break
            experience_vals.append((0, 0, {
                'company_name': company,
                'role': post.get(f'exp_role_{i}', '').strip(),
                'date_from': post.get(f'exp_from_{i}') or False,
                'date_to': post.get(f'exp_to_{i}') or False,
            }))

        try:
            app_vals = {
                'name': post.get('name', '').strip(),
                'email': post.get('email', '').strip(),
                'phone': post.get('phone', '').strip(),
                'secondary_phone': post.get('secondary_phone', '').strip(),
                'secondary_email': post.get('secondary_email', '').strip(),
                'dob': post.get('dob') or False,
                # Segregated address
                'street': post.get('street', '').strip(),
                'street2': post.get('street2', '').strip(),
                'home_city': post.get('home_city', '').strip(),
                'home_zip': post.get('home_zip', '').strip(),
                'home_state_id': int(post['home_state_id']) if post.get('home_state_id') else False,
                'home_country_id': int(post['home_country_id']) if post.get('home_country_id') else False,
                # Professional
                'current_occupation': post.get('current_occupation', '').strip(),
                'qualification': post.get('qualification', '').strip(),
                'vacancy_known_through': post.get('vacancy_known_through') or False,
                'business_type': post.get('business_type') or False,
                'code': post.get('code', '').strip(),
                # Business location interest
                'city_interested': post.get('city_interested', '').strip(),
                'country_interested_id': int(post['country_interested_id']) if post.get('country_interested_id') else False,
                'state_interested_id': int(post['state_interested_id']) if post.get('state_interested_id') else False,
                # Experience
                'has_experience': bool(post.get('has_experience')),
                'experience_ids': experience_vals,
                # Financial
                'last_year_turnover': float(post.get('last_year_turnover') or 0),
                'investment_from': float(post.get('investment_from') or 0),
                'investment_to': float(post.get('investment_to') or 0),
                'investment_available': bool(post.get('investment_available')),
                'investment_not_available': bool(post.get('investment_not_available')),
                'total_area': float(post.get('total_area') or 0),
                # Enquiry
                'enquiry_description': post.get('enquiry_description', '').strip(),
                'state': 'draft',
            }

            application = request.env['dealership.application'].sudo().create(app_vals)

            # ── File uploads ─────────────────────────────────────
            shop_image = request.httprequest.files.get('shop_image')
            if shop_image and shop_image.filename:
                application.sudo().write({
                    'shop_image': base64.b64encode(shop_image.read()),
                    'shop_image_filename': shop_image.filename,
                })

            attachment_ids = []
            for doc in request.httprequest.files.getlist('documents'):
                if doc and doc.filename:
                    att = request.env['ir.attachment'].sudo().create({
                        'name': doc.filename,
                        'datas': base64.b64encode(doc.read()),
                        'res_model': 'dealership.application',
                        'res_id': application.id,
                    })
                    attachment_ids.append(att.id)
            if attachment_ids:
                application.sudo().write({'document_ids': [(6, 0, attachment_ids)]})

            # ── Submit (triggers email) ──────────────────────────
            application.sudo().action_submit()

            return request.render('dealer_management.template_become_dealer', {
                'success': True,
                'ref_code': application.ref_code,
                'applicant_name': application.name,
                'error': {},
                'countries': countries,
                'values': {},
            })

        except (ValidationError, UserError) as e:
            return request.render('dealer_management.template_become_dealer', {
                'error': {'general': str(e)},
                'values': post,
                'success': False,
                'countries': countries,
            })
        except Exception as e:
            _logger.exception('Unexpected error during dealer application submission')
            return request.render('dealer_management.template_become_dealer', {
                'error': {'general': _('An unexpected error occurred. Please try again.')},
                'values': post,
                'success': False,
                'countries': countries,
            })

    # ═══════════════════════════════════════════════════════════════
    #  APPLICATION STATUS TRACKING  (dedicated template, NOT 404)
    # ═══════════════════════════════════════════════════════════════

    @http.route(
        ['/dealer-status', '/dealer-status/<string:ref_code>'],
        type='http', auth='public', website=True, sitemap=False
    )
    def dealer_application_status(self, ref_code=None, **kwargs):
        """Public status tracking page — always renders, never 404."""
        app = False
        not_found = False

        if ref_code:
            app = request.env['dealership.application'].sudo().search(
                [('ref_code', '=', ref_code.strip().upper())], limit=1
            )
            # Also try lowercase / as-is
            if not app:
                app = request.env['dealership.application'].sudo().search(
                    [('ref_code', '=', ref_code.strip())], limit=1
                )
            if not app:
                not_found = True

        return request.render('dealer_management.template_application_status', {
            'app': app,
            'ref_code': ref_code or '',
            'not_found': not_found,
        })

    # ═══════════════════════════════════════════════════════════════
    #  DEALER PROFILE – portal users only
    # ═══════════════════════════════════════════════════════════════

    @http.route('/dealer-profile', type='http', auth='user', website=True)
    def dealer_profile(self, **kwargs):
        """Dealer profile page. Requires portal/internal user login."""
        try:
            partner = request.env.user.partner_id
            application = request.env['dealership.application'].sudo().search(
                [('partner_id', '=', partner.id), ('state', '=', 'done')],
                limit=1
            )
            if not application:
                # User is logged in but not an approved dealer
                return request.render('dealer_management.template_not_a_dealer', {
                    'partner': partner,
                })

            sale_orders = request.env['sale.order'].sudo().search(
                [('dealer_application_id', '=', application.id)],
                order='date_order desc', limit=20
            )
            leads = request.env['crm.lead'].sudo().search(
                [('dealer_application_id', '=', application.id)],
                order='create_date desc', limit=20
            )
            contracts = request.env['dealership.contract'].sudo().search(
                [('application_id', '=', application.id)],
                order='id desc'
            )

            return request.render('dealer_management.template_dealer_profile', {
                'application': application,
                'partner': partner,
                'sale_orders': sale_orders,
                'leads': leads,
                'contracts': contracts,
                'success': False,
                'error': {},
            })
        except Exception as e:
            _logger.exception('Error rendering dealer profile for user %s', request.env.user.login)
            return request.render('dealer_management.template_not_a_dealer', {
                'partner': request.env.user.partner_id,
                'error_msg': str(e),
            })

    @http.route(
        '/dealer-profile/update',
        type='http', auth='user', website=True, methods=['POST'], csrf=True
    )
    def dealer_profile_update(self, **post):
        partner = request.env.user.partner_id
        application = request.env['dealership.application'].sudo().search(
            [('partner_id', '=', partner.id), ('state', '=', 'done')],
            limit=1
        )
        if not application:
            return request.redirect('/dealer-profile')

        error = {}
        update_vals = {}

        if post.get('phone', '').strip():
            update_vals['phone'] = post['phone'].strip()
            partner.sudo().write({'phone': post['phone'].strip()})
        if post.get('secondary_phone', '').strip():
            update_vals['secondary_phone'] = post['secondary_phone'].strip()
        if post.get('secondary_email', '').strip():
            se = post['secondary_email'].strip()
            if '@' not in se:
                error['secondary_email'] = _('Invalid email address.')
            else:
                update_vals['secondary_email'] = se

        if update_vals and not error:
            application.sudo().write(update_vals)

        sale_orders = request.env['sale.order'].sudo().search(
            [('dealer_application_id', '=', application.id)],
            order='date_order desc', limit=20
        )
        leads = request.env['crm.lead'].sudo().search(
            [('dealer_application_id', '=', application.id)],
            order='create_date desc', limit=20
        )
        contracts = request.env['dealership.contract'].sudo().search(
            [('application_id', '=', application.id)], order='id desc'
        )

        return request.render('dealer_management.template_dealer_profile', {
            'application': application,
            'partner': partner,
            'sale_orders': sale_orders,
            'leads': leads,
            'contracts': contracts,
            'success': not bool(error),
            'error': error,
        })

    # ═══════════════════════════════════════════════════════════════
    #  FIND A DEALER
    # ═══════════════════════════════════════════════════════════════

    @http.route('/find-a-dealer', type='http', auth='public', website=True, sitemap=True)
    def find_dealer(self, country=None, city=None, postal=None, name=None, **kwargs):
        Application = request.env['dealership.application'].sudo()
        domain = [('state', '=', 'done'), ('website_published', '=', True)]

        if country:
            domain += [('country_interested_id.name', 'ilike', country)]
        if city:
            domain += [('city_interested', 'ilike', city)]
        if name:
            domain += [('name', 'ilike', name)]

        dealers = Application.search(domain)

        dealers_json = []
        for d in dealers:
            partner = d.partner_id
            lat = partner.geo_lat if partner and partner.geo_lat else 0.0
            lng = partner.geo_lng if partner and partner.geo_lng else 0.0
            dealers_json.append({
                'id': d.id,
                'name': d.name or '',
                'phone': d.phone or '',
                'email': d.email or '',
                'city': d.city_interested or '',
                'country': d.country_interested_id.name if d.country_interested_id else '',
                'address': (d.street or '') + (', ' + d.home_city if d.home_city else ''),
                'website': partner.dealer_website if partner else '',
                'lat': lat,
                'lng': lng,
                'has_image': bool(d.shop_image),
                'image_url': f'/web/image/dealership.application/{d.id}/shop_image/100x100',
            })

        return request.render('dealer_management.template_find_dealer', {
            'dealers': dealers,
            'dealers_json': json.dumps(dealers_json),
            'countries': request.env['res.country'].sudo().search([], order='name asc'),
            'search_country': country or '',
            'search_city': city or '',
            'search_postal': postal or '',
            'search_name': name or '',
        })

    # ═══════════════════════════════════════════════════════════════
    #  AJAX: states by country
    # ═══════════════════════════════════════════════════════════════

    @http.route('/dealer/get-states', type='json', auth='public', website=True)
    def get_states(self, country_id=None, **kwargs):
        if not country_id:
            return []
        states = request.env['res.country.state'].sudo().search(
            [('country_id', '=', int(country_id))], order='name asc'
        )
        return [{'id': s.id, 'name': s.name} for s in states]

    # ═══════════════════════════════════════════════════════════════
    #  Application messaging (portal/public)
    # ═══════════════════════════════════════════════════════════════

    @http.route(
        '/dealer/message',
        type='http', auth='public', website=True, methods=['POST'], csrf=True
    )
    def dealer_message(self, ref_code=None, message=None, **kwargs):
        if ref_code and message and message.strip():
            app = request.env['dealership.application'].sudo().search(
                [('ref_code', '=', ref_code.strip())], limit=1
            )
            if app:
                author = request.env.user.partner_id if not request.env.user._is_public() else \
                    request.env.ref('base.partner_root')
                app.sudo().message_post(
                    body=message.strip(),
                    author_id=author.id,
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment',
                )
        return request.redirect(f'/dealer-status/{ref_code}' if ref_code else '/become-a-dealer')
