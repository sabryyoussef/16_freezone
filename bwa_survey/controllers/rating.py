
import base64
from collections import OrderedDict
from datetime import datetime

from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request, Response
from odoo.tools import image_process
from odoo.tools.translate import _
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager as portal_pager, get_records_pager

class EmployeeRating(portal.CustomerPortal):

    @http.route('/my/rating/new', type='http', auth="public", website=True)
    def portal_my_rating_request_new(self, **kw):
        # kw['customer_id'] = http.request.env.user.id
        if kw:
            http.request.env['survey.rating'].sudo().create(kw)
            return request.render("bwa_survey.portal_my_rating_request_submit",
                                  {'page_name': 'NewRating'})
        else:
            return request.render("bwa_survey.portal_my_rating_request_new",
                                  {'page_name': 'NewRating'})

    @http.route(['''/my/rating/submit/<model('survey.rating'):rating>'''], type='http', methods=['GET'],
                auth="user", website=True,
                csrf=False)
    def portal_my_rating_request_new_submit(self, rating, **kw):
        rating.sudo().button_submit()
        return request.render("bwa_survey.portal_my_rating_request_submit",
                              {'page_name': 'NewRating'})

