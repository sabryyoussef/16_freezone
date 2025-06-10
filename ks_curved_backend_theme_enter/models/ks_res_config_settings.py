from odoo import _, api, exceptions, fields, models
import base64
from odoo.tools.mimetypes import guess_mimetype


class KsResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    def _default_global_config(self):
        return self.env.ref('ks_curved_backend_theme_enter.ks_global_config_single_rec')

    ks_enable_pwa_app = fields.Boolean(string="Enable PWA",
                                       config_parameter='ks_curved_backend_theme_enter.ks_enable_pwa_app')
    ks_pwa_name = fields.Char(string="Name", config_parameter='ks_curved_backend_theme_enter.ks_pwa_name')
    ks_global_config = fields.Many2one(comodel_name='ks.global.config',
                                       config_parameter='ks_curved_backend_theme_enter.ks_global_config')
    ks_pwa_icon = fields.Binary(related='ks_global_config.ks_pwa_icon', readonly=False, string="Icon")
    ks_pwa_short_name = fields.Char(string="Short Name", config_parameter='ks_curved_backend_theme_enter.ks_pwa_short_name')

    ks_pwa_background_color = fields.Char(string="PWA Background Color",
                                          config_parameter='ks_curved_backend_theme_enter.ks_pwa_background_color')
    ks_pwa_theme_color = fields.Char(string="PWA Head Theme Color",
                                     config_parameter='ks_curved_backend_theme_enter.ks_pwa_theme_color')

    @api.model
    def get_values(self):
        res = super(KsResConfigSettings, self).get_values()

        # Check if global setting field has no data then assign the default the global setting record.
        if not self.ks_global_config:
            res.update(ks_global_config=self.env.ref('ks_curved_backend_theme_enter.ks_global_config_single_rec').id)

        ks_pwa_icon = self.env.ref('ks_curved_backend_theme_enter.ks_global_config_single_rec').sudo().ks_pwa_icon
        res.update(
            ks_pwa_icon=ks_pwa_icon if ks_pwa_icon else False,
        )
        return res
