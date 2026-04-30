# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class DealershipApplication(models.Model):
    _name = 'dealership.application'
    _description = 'Dealer Application'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'id desc'

    # ── Basic Information ──────────────────────────────────────────────────
    name = fields.Char(
        string='Full Name', required=True, tracking=True,
        help='Full legal name of the applicant'
    )
    ref_code = fields.Char(
        string='Reference Code', readonly=True, copy=False, index=True
    )
    dob = fields.Date(string='Date of Birth')
    phone = fields.Char(string='Phone Number', tracking=True)
    email = fields.Char(string='Email Address', required=True, tracking=True)

    # ── Address (segregated) ───────────────────────────────────────────────
    street = fields.Char(string='Street / House No.')
    street2 = fields.Char(string='Street 2 / Area')
    home_city = fields.Char(string='City')
    home_zip = fields.Char(string='Postal / ZIP Code')
    home_state_id = fields.Many2one(
        'res.country.state', string='State / Province',
        domain="[('country_id', '=', home_country_id)]"
    )
    home_country_id = fields.Many2one('res.country', string='Country')

    secondary_phone = fields.Char(string='Secondary Phone Number')
    secondary_email = fields.Char(string='Secondary Email Address')

    # ── Company ────────────────────────────────────────────────────────────
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True
    )

    # ── Professional Background ────────────────────────────────────────────
    current_occupation = fields.Char(string='Current Occupation')
    qualification = fields.Char(string='Qualification')
    vacancy_known_through = fields.Selection([
        ('social_media', 'Social Media'),
        ('newspaper', 'Newspaper / Magazine'),
        ('friend', 'Friend / Colleague'),
        ('website', 'Company Website'),
        ('exhibition', 'Exhibition / Trade Show'),
        ('tv', 'TV / Radio'),
        ('other', 'Other'),
    ], string='Dealer Vacancy Known Through', tracking=True)

    # ── Business Details ───────────────────────────────────────────────────
    code = fields.Char(string='Code')
    business_type = fields.Selection([
        ('retail', 'Retail'),
        ('wholesale', 'Wholesale'),
        ('distribution', 'Distribution'),
        ('franchise', 'Franchise'),
        ('other', 'Other'),
    ], string='Business Type')

    city_interested = fields.Char(string='City Interested In')
    country_interested_id = fields.Many2one(
        'res.country', string='Country Interested In'
    )
    state_interested_id = fields.Many2one(
        'res.country.state', string='State Interested In',
        domain="[('country_id', '=', country_interested_id)]"
    )

    # ── Experience ─────────────────────────────────────────────────────────
    has_experience = fields.Boolean(
        string='Do you have any experience in our business?'
    )
    experience_ids = fields.One2many(
        'dealership.application.experience',
        'application_id',
        string='Business Experience'
    )

    # ── Financial ──────────────────────────────────────────────────────────
    last_year_turnover = fields.Float(
        string='Last One Year Turnover', digits=(16, 2)
    )
    investment_from = fields.Float(string='Investment From', digits=(16, 2))
    investment_to = fields.Float(string='Investment To', digits=(16, 2))
    investment_available = fields.Boolean(string='Available')
    investment_not_available = fields.Boolean(string='Not Available')
    total_area = fields.Float(string='Total Area (In Sq Ft)', digits=(16, 2))

    # ── Enquiry ────────────────────────────────────────────────────────────
    enquiry_description = fields.Text(string='Enquiry Description')

    # ── Attachments ────────────────────────────────────────────────────────
    shop_image = fields.Binary(string='Shop Image', attachment=True)
    shop_image_filename = fields.Char(string='Shop Image Filename')
    document_ids = fields.Many2many(
        'ir.attachment',
        'dealership_application_attachment_rel',
        'application_id',
        'attachment_id',
        string='Documents'
    )

    # ── State & Dates ──────────────────────────────────────────────────────
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('process', 'In Process'),
        ('pending', 'Pending'),
        ('declined', 'Declined'),
        ('done', 'Approved'),
    ], string='Status', default='draft', tracking=True, required=True)

    drafted_on = fields.Datetime(string='Drafted On', readonly=True)
    submitted_on = fields.Datetime(string='Submitted On', readonly=True)
    processed_on = fields.Datetime(string='Processed On', readonly=True)
    approved_on = fields.Datetime(string='Approved On', readonly=True)
    declined_on = fields.Datetime(string='Declined On', readonly=True)

    # ── Approval Tracking ──────────────────────────────────────────────────
    approval_level = fields.Integer(
        string='Approval Level', default=0, readonly=True
    )
    approved_by_ids = fields.Many2many(
        'res.users',
        'dealership_application_approver_rel',
        'application_id',
        'user_id',
        string='Approved By', readonly=True
    )
    decline_reason = fields.Text(string='Decline Reason')

    # ── Relations ──────────────────────────────────────────────────────────
    partner_id = fields.Many2one(
        'res.partner', string='Related Partner',
        help='Linked once applicant becomes a dealer/portal user'
    )
    sale_order_ids = fields.One2many(
        'sale.order', 'dealer_application_id',
        string='Sale Orders'
    )
    sale_order_count = fields.Integer(
        string='# Sale Orders', compute='_compute_sale_order_count'
    )
    lead_ids = fields.One2many(
        'crm.lead', 'dealer_application_id',
        string='Leads / Opportunities'
    )
    lead_count = fields.Integer(
        string='# Leads', compute='_compute_lead_count'
    )
    contract_ids = fields.One2many(
        'dealership.contract', 'application_id',
        string='Contracts'
    )
    contract_count = fields.Integer(
        string='# Contracts', compute='_compute_contract_count'
    )
    active_contract_id = fields.Many2one(
        'dealership.contract', string='Active Contract',
        compute='_compute_active_contract'
    )

    # ── Portal & Website ───────────────────────────────────────────────────
    portal_access_granted = fields.Boolean(
        string='Portal Access Granted', default=False, readonly=True
    )
    website_published = fields.Boolean(
        string='Listed on Website', default=False,
        help='Show this dealer on the public Find a Dealer page'
    )
    website_url_slug = fields.Char(string='Website URL Slug')

    # ──────────────────────────────────────────────────────────────────────
    # Compute Methods
    # ──────────────────────────────────────────────────────────────────────
    @api.depends('sale_order_ids')
    def _compute_sale_order_count(self):
        for rec in self:
            rec.sale_order_count = len(rec.sale_order_ids)

    @api.depends('lead_ids')
    def _compute_lead_count(self):
        for rec in self:
            rec.lead_count = len(rec.lead_ids)

    @api.depends('contract_ids')
    def _compute_contract_count(self):
        for rec in self:
            rec.contract_count = len(rec.contract_ids)

    @api.depends('contract_ids', 'contract_ids.state')
    def _compute_active_contract(self):
        for rec in self:
            active = rec.contract_ids.filtered(lambda c: c.state == 'active')
            rec.active_contract_id = active[:1]

    # ──────────────────────────────────────────────────────────────────────
    # ORM Overrides
    # ──────────────────────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('ref_code') or vals['ref_code'] == _('New'):
                vals['ref_code'] = self.env['ir.sequence'].next_by_code(
                    'dealership.application'
                ) or _('New')
            if not vals.get('drafted_on'):
                vals['drafted_on'] = fields.Datetime.now()
        return super().create(vals_list)

    def name_get(self):
        result = []
        for rec in self:
            name = f"[{rec.ref_code}] {rec.name}" if rec.ref_code else rec.name
            result.append((rec.id, name))
        return result

    # ──────────────────────────────────────────────────────────────────────
    # State Transition Actions
    # ──────────────────────────────────────────────────────────────────────
    def action_submit(self):
        """Applicant or website submits the application."""
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Only draft applications can be submitted.'))
            rec.write({
                'state': 'submitted',
                'submitted_on': fields.Datetime.now(),
            })
            rec._send_submission_email()
        return True

    def action_process(self):
        """Manager marks application as in-process."""
        for rec in self:
            if rec.state not in ('submitted', 'pending'):
                raise UserError(_('Application must be in Submitted or Pending state.'))
            rec.write({
                'state': 'process',
                'processed_on': fields.Datetime.now(),
            })
        return True

    def action_pending(self):
        """Mark as pending (awaiting applicant info)."""
        for rec in self:
            rec.write({'state': 'pending'})
            rec._send_pending_email()
        return True

    def action_approve(self):
        """Open approval wizard for multi-level approval."""
        self.ensure_one()
        return {
            'name': _('Approve Application'),
            'type': 'ir.actions.act_window',
            'res_model': 'dealer.approval.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_application_id': self.id,
                'default_action': 'approve',
            },
        }

    def action_decline(self):
        """Open decline wizard."""
        self.ensure_one()
        return {
            'name': _('Decline Application'),
            'type': 'ir.actions.act_window',
            'res_model': 'dealer.approval.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_application_id': self.id,
                'default_action': 'decline',
            },
        }

    def action_reset_draft(self):
        for rec in self:
            if rec.state == 'declined':
                rec.write({
                    'state': 'draft',
                    'approval_level': 0,
                    'approved_by_ids': [(5, 0, 0)],
                    'decline_reason': False,
                })
        return True

    def _do_approve(self, reason=''):
        """Internal approve - called from wizard after final approval level."""
        self.ensure_one()

        # Add this safety check!
        if not self.email:
            raise UserError(
                _("You cannot approve an application without an Email Address. The email is required to create their portal login."))

        self.write({
            'state': 'done',
            'approved_on': fields.Datetime.now(),
            'approved_by_ids': [(4, self.env.user.id)],
        })
        self._grant_portal_access()
        self._create_dealer_contract()
        self._send_approval_email()

    def _do_decline(self, reason=''):
        """Internal decline - called from wizard."""
        self.ensure_one()
        self.write({
            'state': 'declined',
            'declined_on': fields.Datetime.now(),
            'decline_reason': reason,
        })
        self._send_decline_email(reason)

    # ──────────────────────────────────────────────────────────────────────
    # Portal Access
    # ──────────────────────────────────────────────────────────────────────
    def _grant_portal_access(self):
        """Create / find res.partner and grant portal user access (Odoo 17)."""
        self.ensure_one()
        if self.portal_access_granted:
            return

        Partner = self.env['res.partner'].sudo()
        partner = self.partner_id

        if not partner:
            partner = Partner.search([('email', '=', self.email)], limit=1)
        if not partner:
            partner = Partner.create({
                'name': self.name,
                'email': self.email,
                'phone': self.phone,
                'mobile': self.secondary_phone,
                'street': self.street,
                'country_id': self.country_interested_id.id,
                'state_id': self.state_interested_id.id,
                'city': self.city_interested,
                'is_dealer': True,
                'dealer_since': fields.Date.today(),
            })
        else:
            partner.write({
                'is_dealer': True,
                'dealer_since': fields.Date.today(),
            })

        self.sudo().write({'partner_id': partner.id})

        # Grant portal access via portal.wizard (Odoo 17 compatible)
        try:
            portal_wizard = self.env['portal.wizard'].sudo().create({})

            wizard_user = self.env['portal.wizard.user'].sudo().search([
                ('wizard_id', '=', portal_wizard.id),
                ('partner_id', '=', partner.id)
            ], limit=1)

            if not wizard_user:
                wizard_user = self.env['portal.wizard.user'].sudo().create({
                    'wizard_id': portal_wizard.id,
                    'partner_id': partner.id,
                    'email': self.email,
                })

            # Use is_portal for Odoo 17+
            wizard_user.sudo().write({'is_portal': True})
            portal_wizard.sudo().action_apply()

        except Exception as e:
            _logger.warning('Could not grant portal access automatically: %s', e)
            # Safe Fallback: Create a res.users record manually if the wizard fails
            existing_user = self.env['res.users'].sudo().search([('partner_id', '=', partner.id)], limit=1)
            if not existing_user:
                portal_group = self.env.ref('base.group_portal')
                self.env['res.users'].sudo().create({
                    'name': partner.name,
                    'login': partner.email,
                    'partner_id': partner.id,
                    'groups_id': [(6, 0, [portal_group.id])]
                })

        self.sudo().write({'portal_access_granted': True})
        _logger.info('Portal access granted to dealer: %s (%s)', self.name, self.email)

    # ──────────────────────────────────────────────────────────────────────
    # Contract Creation
    # ──────────────────────────────────────────────────────────────────────
    def _create_dealer_contract(self):
        """Auto-create a dealer contract on approval."""
        self.ensure_one()
        existing = self.contract_ids.filtered(lambda c: c.state in ('draft', 'active'))
        if existing:
            return existing[0]
        contract = self.env['dealership.contract'].create({
            'application_id': self.id,
            'partner_id': self.partner_id.id,
            'name': f"DC/{self.ref_code}",
            'start_date': fields.Date.today(),
        })
        return contract

    # ──────────────────────────────────────────────────────────────────────
    # Email Methods
    # ──────────────────────────────────────────────────────────────────────
    def _send_submission_email(self):
        template = self.env.ref(
            'dealer_management.mail_template_application_submitted',
            raise_if_not_found=False
        )
        if template:
            try:
                template.sudo().send_mail(self.id, force_send=True)
            except Exception as e:
                _logger.warning('Failed to send submission email for %s: %s', self.ref_code, e)

    def _send_pending_email(self):
        template = self.env.ref(
            'dealer_management.mail_template_application_pending',
            raise_if_not_found=False
        )
        if template:
            try:
                template.sudo().send_mail(self.id, force_send=True)
            except Exception as e:
                _logger.warning('Failed to send pending email for %s: %s', self.ref_code, e)

    def _send_approval_email(self):
        template = self.env.ref(
            'dealer_management.mail_template_application_approved',
            raise_if_not_found=False
        )
        if template:
            try:
                template.sudo().send_mail(self.id, force_send=True)
            except Exception as e:
                _logger.warning('Failed to send approval email for %s: %s', self.ref_code, e)

    def _send_decline_email(self, reason=''):
        template = self.env.ref(
            'dealer_management.mail_template_application_declined',
            raise_if_not_found=False
        )
        if template:
            try:
                template.sudo().with_context(decline_reason=reason).send_mail(
                    self.id, force_send=True
                )
            except Exception as e:
                _logger.warning('Failed to send decline email for %s: %s', self.ref_code, e)

    # ──────────────────────────────────────────────────────────────────────
    # Smart Button Actions
    # ──────────────────────────────────────────────────────────────────────
    def action_view_sale_orders(self):
        self.ensure_one()
        return {
            'name': _('Sale Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [('dealer_application_id', '=', self.id)],
            'context': {'default_dealer_application_id': self.id},
        }

    def action_view_leads(self):
        self.ensure_one()
        return {
            'name': _('Leads / Opportunities'),
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'tree,form',
            'domain': [('dealer_application_id', '=', self.id)],
            'context': {'default_dealer_application_id': self.id},
        }

    def action_view_contracts(self):
        self.ensure_one()
        return {
            'name': _('Dealer Contracts'),
            'type': 'ir.actions.act_window',
            'res_model': 'dealership.contract',
            'view_mode': 'tree,form',
            'domain': [('application_id', '=', self.id)],
            'context': {'default_application_id': self.id},
        }

    # ──────────────────────────────────────────────────────────────────────
    # Website helpers
    # ──────────────────────────────────────────────────────────────────────
    def get_portal_url(self):
        self.ensure_one()
        return f"/dealer-profile/{self.id}"

    @api.model
    def get_public_dealers(self, country=None, city=None, postal=None, name=None):
        """Return published dealers for Find a Dealer page."""
        domain = [('state', '=', 'done'), ('website_published', '=', True)]
        if country:
            domain += [('country_interested_id.name', 'ilike', country)]
        if city:
            domain += [('city_interested', 'ilike', city)]
        if name:
            domain += [('name', 'ilike', name)]
        return self.search(domain)
