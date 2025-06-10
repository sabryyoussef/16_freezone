import logging
import werkzeug

from odoo import http
from odoo.http import request
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)

MAPPED_RATES = {
    1: 1,
    5: 3,
    10: 5,
}

# class Rating(http.Controller):
#
#     @http.route('/rate/<string:token>/<int:rate>', type='http', auth="public", website=True)
#     def action_open_rating(self, token, rate, **kwargs):
#         rating, record_sudo = self._get_rating_and_record(token)
#         print(' record_sudo.display_name  ==========>  ', record_sudo.display_name)
#         record_sudo.rating_apply(
#             rate,
#             rating=rating,
#             feedback=_('Customer rated %r.', record_sudo.display_name),
#             subtype_xmlid=None,
#             notify_delay_send=True,
#         )
#
#         lang = rating.partner_id.lang or get_lang(request.env).code
#         return request.env['ir.ui.view'].with_context(lang=lang)._render_template('freezoner_custom.rating_external_page_submit_custom',
#               {
#                   'rating': rating,
#                   'token': token,
#                   'rate_priority': {
#                       0: _("Zero"),
#                       1: _("Low"),
#                       2: _("Normal"),
#                       3: _("Medium"),
#                       4: _("High"),
#                       5: _("Very High"),
#                   },
#                   'rate': rate,
#               })
#
#     @http.route(['/rate/<string:token>/submit_feedback'], type="http", auth="public", methods=['post', 'get'],
#                 website=True)
#     def action_submit_rating(self, token, rate=0, **kwargs):
#         rating, record_sudo = self._get_rating_and_record(token)
#         if request.httprequest.method == "POST":
#             rate = int(rate)
#             record_sudo.rating_apply(
#                 rate,
#                 rating=rating,
#                 feedback=kwargs.get('feedback'),
#                 subtype_xmlid=None,  # force default subtype choice
#             )
#
#         lang = rating.partner_id.lang or get_lang(request.env).code
#         return request.env['ir.ui.view'].with_context(lang=lang)._render_template('rating.rating_external_page_view', {
#             'web_base_url': rating.get_base_url(),
#             'rating': rating,
#         })
#
#     def _get_rating_and_record(self, token):
#         rating_sudo = request.env['rating.rating'].sudo().search([('access_token', '=', token)])
#         if not rating_sudo:
#             raise werkzeug.exceptions.NotFound()
#
#         record_sudo = request.env[rating_sudo.res_model].sudo().browse(rating_sudo.res_id)
#         if not record_sudo.exists():
#             raise werkzeug.exceptions.NotFound()
#         return rating_sudo, record_sudo
