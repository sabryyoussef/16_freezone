from odoo import models
from odoo.http import request


class KsIrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        result = super(KsIrHttp, self).session_info()
        if request.env.user.has_group('base.group_user'):
            result['ks_breadcrumb_style'] = request.env.ref('ks_curved_backend_theme_enter.ks_global_config_single_rec').ks_breadcrumb_style
            result['ks_splitted_vertical_width'] = request.env.user.ks_split_vertical_list_width
            result['ks_splitted_horizontal_height'] = request.env.user.ks_split_horizontal_list_height
            result['ks_split_view'] = request.env.user.ks_split_view
            result['show_effect'] = request.env['ir.config_parameter'].sudo().get_param('base_setup.show_effect')
            result['ks_form_view_width'] = request.env.user.ks_form_page_width if request.env.user.ks_form_page_width else False
            result['ks_lang_direction'] = request.env['res.lang']._lang_get(request.env.user.lang).direction
            ks_all_setting_scope = request.env['ks.global.config'].sudo().ks_get_config_values()
            if ks_all_setting_scope.get('scope_ks_loaders', '').lower() == 'global':
                result['ks_current_loader'] = self.sudo().env.ref('ks_curved_backend_theme_enter.ks_global_config_single_rec')['ks_loaders']
            elif ks_all_setting_scope.get('scope_ks_loaders', '').lower() == 'company':
                result['ks_current_loader'] = self.sudo().env.user.company_id.ks_loaders
            else:
                result['ks_current_loader'] = self.sudo().env.user.ks_loaders
        return result
