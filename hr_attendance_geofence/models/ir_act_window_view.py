from odoo import fields, models

class IrActionsActWindowView(models.Model):
    _inherit = 'ir.actions.act_window.view'

    view_mode = fields.Selection(
        selection_add=[('geofence_view', 'Geofence View')],
        ondelete={'geofence_view': 'cascade'},
    )
