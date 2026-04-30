# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    dealer_application_id = fields.Many2one(
        'dealership.application',
        string='Dealer Application',
        index=True,
        copy=False,
        help='Link this sale order to a dealer application'
    )
    is_dealer_qualifying_order = fields.Boolean(
        string='Dealer Qualifying Order', default=False,
        help='Checked when this order qualifies the customer to become a dealer'
    )

    def _confirm_dealer_on_delivery_payment(self):
        """
        Called when payment is confirmed. If this is a dealer-qualifying order
        and all deliveries are done, approve the dealer application.
        """
        self.ensure_one()
        app = self.dealer_application_id
        if not app or not self.is_dealer_qualifying_order:
            return
        if app.state == 'done':
            return

        # Check all pickings done
        pickings_done = all(
            p.state == 'done' for p in self.picking_ids
        ) if self.picking_ids else True

        # Check invoices paid
        invoices_paid = all(
            inv.payment_state in ('paid', 'in_payment')
            for inv in self.invoice_ids
        ) if self.invoice_ids else False

        if pickings_done and invoices_paid:
            _logger.info(
                'Auto-approving dealer application %s after sale order %s paid & delivered.',
                app.ref_code, self.name
            )
            app._do_approve(reason=_('Auto-approved: qualifying order %s paid and delivered.') % self.name)

    def _create_invoices(self, grouped=False, final=False, date=None):
        """Hook to auto-link invoices to dealer flow."""
        moves = super()._create_invoices(grouped=grouped, final=final, date=date)
        return moves


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_payment_state_changed(self):
        """Called after payment reconciliation in Odoo 17."""
        res = super().action_payment_state_changed() if hasattr(super(), 'action_payment_state_changed') else None
        self._check_dealer_qualifying_payment()
        return res

    def _check_dealer_qualifying_payment(self):
        """After invoice is fully paid, check if dealer should be activated."""
        for move in self:
            if move.move_type != 'out_invoice':
                continue
            if move.payment_state not in ('paid', 'in_payment'):
                continue
            for line in move.invoice_line_ids:
                for sale_line in line.sale_line_ids:
                    so = sale_line.order_id
                    if so and so.dealer_application_id and so.is_dealer_qualifying_order:
                        so._confirm_dealer_on_delivery_payment()
