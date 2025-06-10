
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HrLeaves(models.Model):
    _inherit = 'hr.leave'

    @api.model_create_multi
    def create(self, values):
        Leaves = super(HrLeaves, self).create(values)
        for leave in Leaves:
            today = fields.Date.today()
            start_date = leave.request_date_from
            leave_duration = leave.number_of_days_display
            period = (start_date - today).days
            if leave_duration > 4 :
                if period < 14:
                    raise ValidationError(_('The Period Must Be Before 2 Weeks From Leave Start.'))
            else:
                if period <= 2 :
                    raise ValidationError(_('The Period Must Be Before 2 Days From Leave Start.'))
        return Leaves

    def write(self, vals):
        Leaves = super(HrLeaves, self).write(vals)
        for leave in self:
            today = fields.Date.today()
            start_date = leave.request_date_from
            leave_duration = leave.number_of_days_display
            period = (start_date - today).days
            if leave_duration > 4 :
                if period < 15:
                    raise ValidationError(_('The Period Must Be Before 2 Weeks From Leave Start.'))
            else:
                if period <= 2 :
                    raise ValidationError(_('The Period Must Be Before 2 Days From Leave Start.'))
        return Leaves

