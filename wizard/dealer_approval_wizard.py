# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DealerApprovalWizard(models.TransientModel):
    _name = 'dealer.approval.wizard'
    _description = 'Dealer Application Approval / Decline Wizard'

    application_id = fields.Many2one(
        'dealership.application', string='Application',
        required=True, readonly=True
    )
    action = fields.Selection([
        ('approve', 'Approve'),
        ('decline', 'Decline'),
    ], string='Action', required=True, default='approve')
    reason = fields.Text(string='Reason / Notes')
    send_email = fields.Boolean(
        string='Send Notification Email', default=True
    )
    current_level = fields.Integer(
        string='Current Approval Level',
        related='application_id.approval_level', readonly=True
    )
    required_levels = fields.Integer(
        string='Required Approval Levels', default=2,
        help='Number of manager approvals required before application is approved.'
    )

    def action_confirm(self):
        self.ensure_one()
        app = self.application_id
        if not app:
            raise UserError(_('No application linked to this wizard.'))

        if self.action == 'approve':
            new_level = app.approval_level + 1
            app.write({
                'approval_level': new_level,
                'approved_by_ids': [(4, self.env.user.id)],
            })
            if new_level >= self.required_levels:
                # Final approval
                app._do_approve(reason=self.reason or '')
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Approved!'),
                        'message': _('%s has been approved as a dealer.') % app.name,
                        'type': 'success',
                        'sticky': False,
                    },
                }
            else:
                # Intermediate approval – notify next approver
                app.message_post(
                    body=_(
                        'Approval level %d/%d completed by %s.'
                    ) % (new_level, self.required_levels, self.env.user.name),
                    subtype_xmlid='mail.mt_note',
                )
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Approval Level %d Recorded') % new_level,
                        'message': _(
                            'Approval level %d of %d completed. %d more required.'
                        ) % (new_level, self.required_levels, self.required_levels - new_level),
                        'type': 'info',
                        'sticky': False,
                    },
                }

        elif self.action == 'decline':
            if not self.reason:
                raise UserError(_('Please provide a reason for declining the application.'))
            app._do_decline(reason=self.reason)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Application Declined'),
                    'message': _('%s has been declined.') % app.name,
                    'type': 'warning',
                    'sticky': False,
                },
            }


class DealerContractTerminationWizard(models.TransientModel):
    _name = 'dealer.contract.termination.wizard'
    _description = 'Dealer Contract Termination Wizard'

    contract_id = fields.Many2one(
        'dealership.contract', string='Contract',
        required=True, readonly=True
    )
    termination_date = fields.Date(
        string='Termination Date',
        required=True,
        default=fields.Date.today
    )
    reason = fields.Text(string='Termination Reason', required=True)

    def action_terminate(self):
        self.ensure_one()
        self.contract_id.write({
            'state': 'terminated',
            'termination_date': self.termination_date,
            'termination_reason': self.reason,
        })
        self.contract_id.message_post(
            body=_('Contract terminated on %s. Reason: %s') % (
                self.termination_date, self.reason
            ),
            subtype_xmlid='mail.mt_note',
        )
        return {'type': 'ir.actions.act_window_close'}
