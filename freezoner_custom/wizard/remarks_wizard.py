
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class RemarksWizard(models.TransientModel):
    _name = 'remarks.wizard'

    remarks_id = fields.Many2one('project.project.products.remarks')
    line_id = fields.Many2one("project.project.products",string="Line")

    def submit(self):
        for rec in self:
            line = rec.line_id
            if rec.remarks_id:  # make sure remark_id exists
                line.remarks_ids = [(4, rec.remarks_id.id)]
