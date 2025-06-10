# -*- coding: utf-8 -*-

import json
import pytz

from odoo import http
from odoo.addons.http_routing.models.ir_http import url_for
from odoo.http import request
from odoo.tools import ustr
from odoo.modules.module import get_module_resource


class KsPwaController(http.Controller):

    @http.route('/ks_curved_backend_theme_enter/get_manifest', type='json', auth='public', sitemap=False)
    def ks_get_pwa_manifest(self):
        ks_enable_pwa_app = request.env['ir.config_parameter'].sudo().get_param(
            'ks_curved_backend_theme_enter.ks_enable_pwa_app')
        if not ks_enable_pwa_app:
            return False
        ks_pwa_name = request.env['ir.config_parameter'].sudo().get_param('ks_curved_backend_theme_enter.ks_pwa_name')
        ks_pwa_background_color = request.env['ir.config_parameter'].sudo().get_param(
            'ks_curved_backend_theme_enter.ks_pwa_background_color')
        ks_pwa_theme_color = request.env['ir.config_parameter'].sudo().get_param(
            'ks_curved_backend_theme_enter.ks_pwa_theme_color')
        port = request.httprequest.host_url.split('://')[1]

        manifest = {'name': ks_pwa_name, 'short_name': ks_pwa_name, 'description': ks_pwa_name,
                    # 'start_url': request.httprequest.host_url + 'web/', 'display': 'standalone',
                    'start_url': 'https://' + port + 'web/', 'display': 'standalone',
                    'background_color': ks_pwa_background_color,
                    'id': "/?db=" + request.db,
                    'theme_color': ks_pwa_theme_color, 'icons': self.ks_get_image_url()}
        return manifest

    @http.route('/ks_curved_backend_theme_enter/get/sw.js', type='http', auth='public', methods=['GET'], sitemap=False)
    def ks_get_service_worker(self):
        sw_file = get_module_resource('ks_curved_backend_theme_enter', 'static/src/js/sw.js')
        with open(sw_file, 'r') as fp:
            body = fp.read()
        response = request.make_response(body, [
            ('Content-Type', 'text/javascript'),
            ('Service-Worker-Allowed', url_for('/web/')),
        ])
        return response

    def ks_get_image_url(self):
        ks_icons = []
        for size in [(72, 72), (96, 96), (128, 128), (144, 144), (152, 152), (192, 192), (256, 256), (384, 384),
                     (512, 512)]:
            ks_url = '/ks_curved_backend_theme_enter/logo/icon_' + str(size[0]) + '_' + request.db
            ks_pwa_icons = request.env["ir.attachment"].sudo().search(
                [('url', 'like', ks_url)], limit=1)

            # Condition to solve the problem for pwa already have the icon with old url.
            if not ks_pwa_icons:
                ks_url = '/ks_curved_backend_theme_enter/logo/icon_' + str(size[0])
                ks_pwa_icons = request.env["ir.attachment"].sudo().search(
                    [('url', 'like', ks_url)], limit=1)

            if ks_pwa_icons:
                ks_icons.append({
                    "src": 'data:image/png;base64,'+ks_pwa_icons.datas.decode("utf-8"),
                    "sizes": str(size[0]) + 'x' + str(size[1]),
                    "type": "image/png"
                })
        return ks_icons

    # @http.route("/ks_curved_backend_theme_enter/manifest.webmanifest", type="http", auth="public")
    # def ks_get_pwa_manifest(self):
    #     ks_enable_pwa_app = request.env['ir.config_parameter'].sudo().get_param(
    #         'ks_curved_backend_theme_enter.ks_enable_pwa_app')
    #     if not ks_enable_pwa_app:
    #         return False
    #     ks_pwa_name = request.env['ir.config_parameter'].sudo().get_param('ks_curved_backend_theme_enter.ks_pwa_name')
    #     ks_pwa_background_color = request.env['ir.config_parameter'].sudo().get_param(
    #         'ks_curved_backend_theme_enter.ks_pwa_background_color')
    #     ks_pwa_theme_color = request.env['ir.config_parameter'].sudo().get_param(
    #         'ks_curved_backend_theme_enter.ks_pwa_theme_color')
    #     port = request.httprequest.host_url.split('://')[1]
    #
    #     manifest = {
    #         'name': ks_pwa_name, 'short_name': ks_pwa_name, 'description': ks_pwa_name,
    #         # 'start_url': request.httprequest.host_url + 'web/', 'display': 'standalone',
    #         'start_url': 'https://' + port + 'web/',
    #         'display': 'standalone',
    #         'background_color': ks_pwa_background_color,
    #         'id': "/?db=" + request.db,
    #         'theme_color': ks_pwa_theme_color, 'icons': self.ks_get_image_url()}
    #
    #     return request.make_response(
    #         json.dumps(manifest),
    #         headers=[("Content-Type", "application/json;charset=utf-8")],
    #     )

