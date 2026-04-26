# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    dealer_id = fields.Many2one(
        'dealer.dealer', string='Dealer', index=True)
    dealer_application_id = fields.Many2one(
        'dealer.application', string='Dealer Application')
    is_dealer_proposal = fields.Boolean(
        string='Is Dealer Proposal', default=False)

    def write(self, vals):
        res = super().write(vals)
        # When delivery_status becomes 'full' and invoice is paid → auto-activate dealer
        for order in self:
            app = self.env['dealer.application'].sudo().search([
                ('sale_order_id', '=', order.id),
                ('state', '=', 'proposal_sent'),
            ], limit=1)
            if app:
                delivery_ok = order.delivery_status in ('full', 'done')
                invoice_ok = order.invoice_status == 'invoiced' or all(
                    inv.payment_state in ('paid', 'in_payment')
                    for inv in order.invoice_ids
                ) if order.invoice_ids else False
                if delivery_ok and invoice_ok:
                    try:
                        app.action_approve()
                        _logger.info(
                            'Dealer application %s auto-approved after '
                            'payment and delivery confirmed.', app.ref_code)
                    except Exception as e:
                        _logger.warning(
                            'Auto-approve failed for %s: %s', app.ref_code, e)
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_dealer_plan_line = fields.Boolean(
        string='Is Dealer Plan Line', default=False)
