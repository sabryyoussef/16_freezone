
from odoo import http , _
from odoo.http import request
from odoo.exceptions import AccessError

class ApprovalRequestController(http.Controller):

    @http.route('/sale_approval_request/approve/<int:rec_id>', type='http', auth='user', website=True)
    def action_approval_request(self, rec_id, **kwargs):
        # Fetch the approval request record
        record = request.env['approval.request'].sudo().browse(rec_id)

        # Check if the user has the required security group
        if request.env.user.has_group('freezoner_sale_approval.approvals_button_in_approvals_group'):
            try:
                # Execute action if user has the group
                record.with_user(request.env.user).action_sale_confirm()
                record.message_post(
                    body=f"Approval From {request.env.user.email}",
                    message_type='notification',
                    subtype_xmlid='mail.mt_note'
                )
                return request.render('freezoner_sale_approval.approval_request_sale_portal_template')
            except AccessError as e:
                # Handle any access errors gracefully
                return request.render('freezoner_sale_approval.access_error_template', {'error': _('Access Error: ') + str(e)})
        else:
            # Return a warning message if user does not have the group
            return request.render('freezoner_sale_approval.access_error_template',
                                  {'warning_message': _('You do not have permission to perform this action.')})

    @http.route('/sale_approval_request/reject/<int:rec_id>', type='http', auth='user', website=True)
    def action_approval_reject(self, rec_id, **kwargs):
        # Fetch the approval request record
        record = request.env['approval.request'].sudo().browse(rec_id)

        # Check if the user has the required security group
        if request.env.user.has_group('freezoner_sale_approval.approvals_button_in_approvals_group'):
            try:
                # Execute reject action if user has the group
                record.with_user(request.env.user).action_reject()
                record.message_post(
                    body=f"Rejected by {request.env.user.email}",
                    message_type='notification',
                    subtype_xmlid='mail.mt_note'
                )
                return request.render('freezoner_sale_approval.approval_request_reject_sale_portal_template')
            except AccessError as e:
                # Handle any access errors gracefully
                return request.render('freezoner_sale_approval.access_error_template',
                                      {'error': _('Access Error: ') + str(e)})
        else:
            # Return a warning message if the user does not have the group
            return request.render('freezoner_sale_approval.access_error_template',
                                  {'warning_message': _('You do not have permission to perform this action.')})