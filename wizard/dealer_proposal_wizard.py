# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class DealerProposalWizard(models.TransientModel):
    _name = 'dealer.proposal.wizard'
    _description = 'Send Dealer Proposal'

    application_id = fields.Many2one(
        'dealer.application', string='Application', required=True)
    plan_id = fields.Many2one(
        'dealer.plan', string='Plan',
        related='application_id.plan_id', readonly=False)
    product_id = fields.Many2one(
        'product.product', string='Plan Product',
        related='plan_id.product_id', readonly=True)
    price = fields.Float(
        string='Proposal Amount',
        related='plan_id.price', readonly=False)
    note = fields.Text(string='Note / Proposal Terms')
    partner_id = fields.Many2one(
        'res.partner', string='Customer',
        related='application_id.partner_id', readonly=True)

    @api.onchange('plan_id')
    def _onchange_plan(self):
        if self.plan_id:
            self.price = self.plan_id.price

    def action_send_proposal(self):
        self.ensure_one()
        app = self.application_id
        if not app.partner_id:
            app._ensure_partner()

        order_lines = []
        if self.plan_id and self.product_id:
            order_lines.append((0, 0, {
                'product_id': self.product_id.id,
                'product_uom_qty': 1,
                'price_unit': self.price,
                'name': f'Dealer Plan: {self.plan_id.name}',
                'is_dealer_plan_line': True,
            }))
        elif self.price:
            # fallback product
            product = self.env['product.product'].search(
                [('name', 'ilike', 'dealer')], limit=1)
            if product:
                order_lines.append((0, 0, {
                    'product_id': product.id,
                    'product_uom_qty': 1,
                    'price_unit': self.price,
                    'name': f'Dealer Registration – {app.plan_id.name if app.plan_id else ""}',
                }))

        sale_order = self.env['sale.order'].create({
            'partner_id': app.partner_id.id,
            'origin': app.ref_code,
            'note': self.note or f'Dealer Application Proposal\nRef: {app.ref_code}',
            'is_dealer_proposal': True,
            'dealer_application_id': app.id,
            'order_line': order_lines,
        })
        app.write({
            'sale_order_id': sale_order.id,
            'state': 'proposal_sent',
        })
        app._send_proposal_email()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Sale Order / Proposal'),
            'res_model': 'sale.order',
            'res_id': sale_order.id,
            'view_mode': 'form',
            'target': 'current',
        }
