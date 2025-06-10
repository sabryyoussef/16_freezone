from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class Partner(models.Model):
    _inherit = 'res.partner'

    risk_name = fields.Char(compute='get_risk_name', store=True)
    risk_assessment_ids = fields.Many2many("partner.risk.assessment", string="Partner Assessment", tracking=True)

    @api.depends('risk_assessment_ids')
    def get_risk_name(self):
        for rec in self:
            if rec.risk_assessment_ids:
                rec.risk_name = rec.risk_assessment_ids[0].name
            else:
                rec.risk_name = False

    @api.constrains("risk_assessment_ids")
    def _check_risk_assessment_ids(self):
        if  len(self.risk_assessment_ids.ids) > 1:
            raise ValidationError(_(" Please select one value from partner assessment"))

    def write(self, vals):
        if 'risk_assessment_ids' in vals:
            for record in self:
                old_risks = record.risk_assessment_ids.mapped('name')
                res = super(Partner, self).write(vals)
                new_risks = record.risk_assessment_ids.mapped('name')
                body = "Risk assessment updated<br>From: %s<br>To: %s" % (
                    ", ".join(old_risks),
                    ", ".join(new_risks)
                )
                record.message_post(body=body)
        else:
            res = super(Partner, self).write(vals)
        return res
