# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class DealerApplication(models.Model):
    _name = 'dealer.application'
    _description = 'Dealer Application'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'ref_code'

    # ── Basic Info ──────────────────────────────────────────────────────────
    ref_code = fields.Char(
        string='Reference Code', readonly=True, copy=False,
        default='New', tracking=True)
    name = fields.Char(string='Full Name', required=True, tracking=True)
    email = fields.Char(string='Email', required=True, tracking=True)
    phone = fields.Char(string='Phone', required=True)
    company_name = fields.Char(string='Business / Shop Name', required=True)
    website_url = fields.Char(string='Business Website')
    plan_id = fields.Many2one(
        'dealer.plan', string='Requested Plan', required=True, tracking=True)

    # ── Location ─────────────────────────────────────────────────────────────
    street = fields.Char(string='Street Address')
    city = fields.Char(string='City', required=True)
    state_id = fields.Many2one('res.country.state', string='State')
    country_id = fields.Many2one(
        'res.country', string='Country',
        default=lambda self: self.env.ref('base.bd', raise_if_not_found=False))
    zip_code = fields.Char(string='ZIP Code')
    latitude = fields.Float(string='Latitude', digits=(10, 7))
    longitude = fields.Float(string='Longitude', digits=(10, 7))

    # ── Space Info ────────────────────────────────────────────────────────────
    space_type = fields.Selection([
        ('shop', 'Shop'),
        ('office', 'Office'),
        ('showroom', 'Showroom'),
        ('warehouse', 'Warehouse'),
        ('other', 'Other'),
    ], string='Space Type', required=True, default='shop')
    space_area = fields.Float(string='Space Area (sq ft)')
    space_ownership = fields.Selection([
        ('owned', 'Owned'),
        ('rented', 'Rented'),
        ('leased', 'Leased'),
    ], string='Space Ownership')

    # ── Images & Attachments ─────────────────────────────────────────────────
    shop_image_ids = fields.Many2many(
        'ir.attachment', 'dealer_app_shop_image_rel',
        'application_id', 'attachment_id',
        string='Shop / Office Images')
    document_ids = fields.Many2many(
        'ir.attachment', 'dealer_app_doc_rel',
        'application_id', 'attachment_id',
        string='Supporting Documents',
        domain=[('mimetype', 'not in', ['image/png', 'image/jpeg', 'image/gif', 'image/webp'])])

    # ── Status & Workflow ─────────────────────────────────────────────────────
    state = fields.Selection([
        ('draft', 'Submitted'),
        ('under_review', 'Under Review'),
        ('proposal_sent', 'Proposal Sent'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, required=True)
    rejection_reason = fields.Text(string='Rejection Reason')
    admin_notes = fields.Text(string='Admin Notes')

    # ── Related Records ───────────────────────────────────────────────────────
    partner_id = fields.Many2one('res.partner', string='Partner')
    sale_order_id = fields.Many2one(
        'sale.order', string='Proposal / Sale Order', tracking=True)
    dealer_id = fields.Many2one(
        'dealer.dealer', string='Dealer Record', readonly=True)

    # ── Portal tracking ───────────────────────────────────────────────────────
    portal_token = fields.Char(string='Portal Token', copy=False)
    submission_date = fields.Datetime(
        string='Submission Date', default=fields.Datetime.now, readonly=True)
    review_date = fields.Datetime(string='Review Date')
    approval_date = fields.Datetime(string='Approval Date')

    # ── Computed ──────────────────────────────────────────────────────────────
    # Correct: Defined as a Selection field
    sale_order_state = fields.Selection(related='sale_order_id.state', string='Order State')
    delivery_status = fields.Selection(
        related='sale_order_id.delivery_status', string='Delivery Status')
    invoice_status = fields.Selection(
        related='sale_order_id.invoice_status', string='Invoice Status')

    # =========================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ref_code', 'New') == 'New':
                vals['ref_code'] = self.env['ir.sequence'].next_by_code(
                    'dealer.application') or 'New'
            # generate portal token
            import uuid
            vals['portal_token'] = str(uuid.uuid4()).replace('-', '')
        records = super().create(vals_list)
        for rec in records:
            rec._send_submission_email()
        return records

    def _send_submission_email(self):
        template = self.env.ref(
            'dealer_management.email_template_dealer_submission',
            raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)

    def _send_proposal_email(self):
        template = self.env.ref(
            'dealer_management.email_template_dealer_proposal',
            raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)

    def _send_approval_email(self):
        template = self.env.ref(
            'dealer_management.email_template_dealer_approved',
            raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)

    def _send_rejection_email(self):
        template = self.env.ref(
            'dealer_management.email_template_dealer_rejected',
            raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)

    # ── Action Buttons ────────────────────────────────────────────────────────
    def action_under_review(self):
        for rec in self:
            rec.write({
                'state': 'under_review',
                'review_date': fields.Datetime.now(),
            })
            rec._ensure_partner()

    def action_send_proposal(self):
        """Create/link a Sale Order as the dealer proposal."""
        self.ensure_one()
        if not self.partner_id:
            self._ensure_partner()
        if self.sale_order_id:
            raise UserError(_('A proposal has already been sent for this application.'))

        order_line_vals = []
        if self.plan_id and self.plan_id.product_id:
            order_line_vals.append((0, 0, {
                'product_id': self.plan_id.product_id.id,
                'product_uom_qty': 1,
                'price_unit': self.plan_id.price,
                'name': f'Dealer Plan: {self.plan_id.name}',
            }))

        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
            'origin': self.ref_code,
            'note': f'Dealer Application Proposal\nRef: {self.ref_code}\nApplicant: {self.name}',
            'order_line': order_line_vals,
        })
        self.write({
            'sale_order_id': sale_order.id,
            'state': 'proposal_sent',
        })
        self._send_proposal_email()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sale Order / Proposal'),
            'res_model': 'sale.order',
            'res_id': sale_order.id,
            'view_mode': 'form',
        }

    def action_approve(self):
        """Approve the application and create the Dealer record + portal access."""
        self.ensure_one()
        if self.state not in ('under_review', 'proposal_sent'):
            raise UserError(_('You can only approve applications under review or with a sent proposal.'))
        self._ensure_partner()
        dealer = self.env['dealer.dealer'].create({
            'name': self.company_name,
            'partner_id': self.partner_id.id,
            'application_id': self.id,
            'plan_id': self.plan_id.id,
            'street': self.street,
            'city': self.city,
            'state_id': self.state_id.id,
            'country_id': self.country_id.id,
            'zip_code': self.zip_code,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'space_type': self.space_type,
            'email': self.email,
            'phone': self.phone,
            'website_url': self.website_url,
        })
        # Grant portal access
        self._grant_portal_access()
        self.write({
            'state': 'approved',
            'dealer_id': dealer.id,
            'approval_date': fields.Datetime.now(),
        })
        self._send_approval_email()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Dealer'),
            'res_model': 'dealer.dealer',
            'res_id': dealer.id,
            'view_mode': 'form',
        }



    def action_reject(self):
        self.write({'state': 'rejected'})
        self._send_rejection_email()

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    def action_view_sale_order(self):
        self.ensure_one()
        if not self.sale_order_id:
            raise UserError(_('No sale order linked yet.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sale Order'),
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
        }

    def _ensure_partner(self):
        """Find or create a res.partner for this applicant."""
        if self.partner_id:
            return self.partner_id
        partner = self.env['res.partner'].search([
            ('email', '=', self.email)], limit=1)
        if not partner:
            partner = self.env['res.partner'].create({
                'name': self.name,
                'email': self.email,
                'phone': self.phone,
                'street': self.street,
                'city': self.city,
                'state_id': self.state_id.id,
                'country_id': self.country_id.id,
                'zip': self.zip_code,
                'company_name': self.company_name,
                'is_company': False,
            })
        self.partner_id = partner
        return partner

    def action_open_dealer_profile(self):
        self.ensure_one()
        return {
            'name': 'Dealer Profile',
            'type': 'ir.actions.act_window',
            'res_model': 'dealer.dealer',
            'view_mode': 'form',
            'res_id': self.dealer_id.id,  # This targets the specific dealer!
        }

    def _grant_portal_access(self):
        """Grant portal user access to the applicant."""
        partner = self.partner_id
        if not partner:
            return
        portal_group = self.env.ref('base.group_portal')
        user = self.env['res.users'].search([
            ('partner_id', '=', partner.id)], limit=1)
        if not user:
            user = self.env['res.users'].with_context(
                no_reset_password=False).create({
                'name': partner.name,
                'login': partner.email,
                'email': partner.email,
                'partner_id': partner.id,
                'groups_id': [(6, 0, [portal_group.id])],
            })
        else:
            user.write({'groups_id': [(4, portal_group.id)]})
        return user

    def get_status_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/dealer/status/{self.ref_code}/{self.portal_token}"
