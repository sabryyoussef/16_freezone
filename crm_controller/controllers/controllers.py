# -*- coding: utf-8 -*-
from odoo import http, models
from odoo.http import request


class CreateLeadAPI(http.Controller):
    @http.route('/api/crm/create/', type='json', auth="none", cors='*', csrf=False, methods=['POST'], )
    def create_lead_api(self, **items):
        lead_model = request.env['crm.lead'].sudo().with_user(1)
        lead = lead_model.create(items)
        return {'message': 'Lead Created'.format(lead)}
