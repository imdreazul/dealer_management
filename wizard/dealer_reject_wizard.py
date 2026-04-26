# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class DealerRejectWizard(models.TransientModel):
    _name = 'dealer.reject.wizard'
    _description = 'Reject Dealer Application'

    application_id = fields.Many2one(
        'dealer.application', string='Application', required=True)
    rejection_reason = fields.Text(
        string='Rejection Reason', required=True,
        placeholder='Please provide a clear reason for rejection...')

    def action_confirm_reject(self):
        self.ensure_one()
        if not self.rejection_reason.strip():
            raise UserError(_('Please provide a rejection reason.'))
        self.application_id.write({
            'state': 'rejected',
            'rejection_reason': self.rejection_reason,
        })
        self.application_id._send_rejection_email()
        return {'type': 'ir.actions.act_window_close'}
