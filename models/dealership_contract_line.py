# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class DealershipContractLine(models.Model):
    _name = 'dealership.contract.line'
    _description = 'Dealership Contract Line (Sale Orders)'
    _order = 'start_date desc'

    contract_id = fields.Many2one(
        'dealership.contract', string='Contract',
        required=True, ondelete='cascade'
    )
    sale_order_id = fields.Many2one(
        'sale.order', string='Sale Order',
        domain="[('dealer_application_id', '=', parent.application_id)]"
    )
    sale_order_reference = fields.Char(
        string='Order Ref', related='sale_order_id.name', store=True
    )
    status = fields.Char(
        string='Order Status',
        compute='_compute_order_status', store=True
    )
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    total_days = fields.Integer(
        string='Total Days', compute='_compute_total_days', store=True
    )
    # Correct: Defined as a Monetary field alongside its required currency field
    currency_id = fields.Many2one(related='sale_order_id.currency_id', string='Currency')
    amount_total = fields.Monetary(related='sale_order_id.amount_total', string='Total', currency_field='currency_id')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('ongoing', 'Ongoing'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
    ], string='Line Status', default='draft', required=True)

    notes = fields.Text(string='Notes')

    @api.depends('sale_order_id', 'sale_order_id.state')
    def _compute_order_status(self):
        state_map = {
            'draft': 'Quotation',
            'sent': 'Quotation Sent',
            'sale': 'Sales Order',
            'done': 'Locked',
            'cancel': 'Cancelled',
        }
        for rec in self:
            if rec.sale_order_id:
                rec.status = state_map.get(rec.sale_order_id.state, rec.sale_order_id.state)
            else:
                rec.status = ''

    @api.depends('start_date', 'end_date')
    def _compute_total_days(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                delta = rec.end_date - rec.start_date
                rec.total_days = delta.days
            else:
                rec.total_days = 0
