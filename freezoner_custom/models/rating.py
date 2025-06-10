
from odoo import api, fields, models

class Rating(models.Model):
    _inherit = 'rating.rating'

    priority = fields.Selection([('0', 'zero'), ('1', 'Low'), ('2', 'Normal'), ('3', 'Medium'), ('4', 'High'), ('5', 'Very High')], 'Rating')


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    # def _notify_get_recipients_groups(self, msg_vals=None):
    #     groups = super()._notify_get_recipients_groups(msg_vals=msg_vals)
    #     if not self:
    #         return groups
    #
    #     portal_enabled = isinstance(self, self.env.registry['portal.mixin'])
    #     if not portal_enabled:
    #         return groups
    #
    #     partners = self._mail_get_partners()
    #     if not partners:
    #         return groups  # Return early if no partners found
    #
    #     customer = partners[0]
    #
    #     access_token = self._portal_ensure_token()
    #     local_msg_vals = dict(msg_vals or {})
    #     local_msg_vals['access_token'] = access_token
    #     local_msg_vals['pid'] = customer.id
    #     local_msg_vals['hash'] = self._sign_token(customer.id)
    #     local_msg_vals.update(customer.signup_get_auth_param()[customer.id])
    #     access_link = self._notify_get_action_link('view', **local_msg_vals)
    #
    #     new_group = [
    #         ('portal_customer', lambda pdata: pdata['id'] == customer.id, {
    #             'has_button_access': True,
    #             'button_access': {
    #                 'url': access_link,
    #             },
    #             'notification_is_customer': True,
    #         })
    #     ]
    #
    #     # enable portal users that should have access through portal (if not access rights
    #     # will do their duty)
    #     portal_group = next(group for group in groups if group[0] == 'portal')
    #     portal_group[2]['active'] = True
    #     portal_group[2]['has_button_access'] = True
    #
    #     return new_group + groups


    # @api.returns('mail.message', lambda value: value.id)
    # def message_post(self, **kwargs):
    #     if len(self) > 1:
    #         raise ValueError("Expected singleton: %s" % self)
    #
    #     rating_id = kwargs.pop('rating_id', False)
    #     rating_value = kwargs.pop('rating_value', False)
    #     rating_feedback = kwargs.pop('rating_feedback', False)
    #     message = super(MailThread, self).message_post(**kwargs)
    #
    #     # create rating.rating record linked to given rating_value
    #     # Using sudo as portal users may have rights to create messages and therefore ratings
    #     # (security should be checked beforehand)
    #     if rating_value:
    #         self.env['rating.rating'].sudo().create({
    #             'rating': float(rating_value) if rating_value is not None else False,
    #             'feedback': rating_feedback,
    #             'res_model_id': self.env['ir.model']._get_id(self._name),
    #             'res_id': self.id,
    #             'message_id': message.id,
    #             'consumed': True,
    #             'partner_id': self.env.user.partner_id.id,
    #         })
    #     elif rating_id:
    #         self.env['rating.rating'].browse(rating_id).write({'message_id': message.id})
    #
    #     return message



