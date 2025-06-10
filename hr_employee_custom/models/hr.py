
from odoo import api, fields, models

class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    joining_date = fields.Date()
