# -*- coding: utf-8 -*-
from odoo import fields, models


class DealershipApplicationExperience(models.Model):
    _name = 'dealership.application.experience'
    _description = 'Dealer Application - Business Experience'
    _order = 'date_from desc'

    application_id = fields.Many2one(
        'dealership.application',
        string='Application',
        required=True,
        ondelete='cascade'
    )
    company_name = fields.Char(string='Company Name', required=True)
    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To')
    is_current = fields.Boolean(string='Currently Working')
    role = fields.Char(string='Role / Position')
    description = fields.Text(string='Description')
