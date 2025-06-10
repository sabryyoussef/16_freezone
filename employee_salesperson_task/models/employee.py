
from odoo import api, fields, models

class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    is_salesperson_task = fields.Boolean(string='Is Employee')
