# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class DealershipContract(models.Model):
    _name = 'dealership.contract'
    _description = 'Dealership Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'id desc'

    name = fields.Char(
        string='Contract Reference', required=True,
        default=lambda self: _('New'), copy=False, tracking=True
    )
    application_id = fields.Many2one(
        'dealership.application', string='Dealer Application',
        required=True, ondelete='restrict', tracking=True
    )
    partner_id = fields.Many2one(
        'res.partner', string='Dealer (Partner)',
        related='application_id.partner_id', store=True, readonly=True
    )
    dealer_name = fields.Char(
        string='Dealer Name',
        related='application_id.name', store=True, readonly=True
    )
    created_on = fields.Date(
        string='Created On', default=fields.Date.today, readonly=True
    )
    start_date = fields.Date(string='Start Date', required=True, tracking=True)
    end_date = fields.Date(string='End Date', tracking=True)
    sale_price_limit = fields.Float(
        string='Sale Price Limit', digits=(16, 2),
        help='Maximum sale price limit allowed for this dealer'
    )
    termination_date = fields.Date(string='Termination Date', tracking=True)
    termination_reason = fields.Text(string='Termination Reason')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
    ], string='Status', default='draft', tracking=True, required=True)

    contract_line_ids = fields.One2many(
        'dealership.contract.line', 'contract_id',
        string='Sale Order Lines'
    )

    sale_order_count = fields.Integer(
        string='# Sale Orders', compute='_compute_sale_order_count'
    )
    total_sales = fields.Float(
        string='Total Sales', compute='_compute_total_sales', digits=(16, 2)
    )

    notes = fields.Text(string='Internal Notes')

    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        related='company_id.currency_id', readonly=True
    )

    @api.depends('contract_line_ids')
    def _compute_sale_order_count(self):
        for rec in self:
            rec.sale_order_count = len(rec.contract_line_ids)

    @api.depends('contract_line_ids', 'contract_line_ids.sale_order_id.amount_total')
    def _compute_total_sales(self):
        for rec in self:
            rec.total_sales = sum(
                line.sale_order_id.amount_total
                for line in rec.contract_line_ids
                if line.sale_order_id
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'dealership.contract'
                ) or _('New')
        return super().create(vals_list)

    def action_activate(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Only draft contracts can be activated.'))
            rec.write({'state': 'active'})
        return True

    def action_terminate(self):
        self.ensure_one()
        return {
            'name': _('Terminate Contract'),
            'type': 'ir.actions.act_window',
            'res_model': 'dealer.contract.termination.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_contract_id': self.id},
        }

    def action_expire(self):
        for rec in self:
            rec.write({'state': 'expired'})
        return True

    def _check_contract_expiry(self):
        """Cron method: auto-expire contracts past their end date."""
        today = fields.Date.today()
        expired = self.search([
            ('state', '=', 'active'),
            ('end_date', '<', today),
        ])
        expired.write({'state': 'expired'})
        _logger.info('Auto-expired %d dealer contracts.', len(expired))
