
from odoo import models, fields, api
from datetime import date, datetime, time

class ResCompany(models.Model):
    _inherit = 'res.company'

    commission_perc = fields.Float('Perc %')
    product_id = fields.Many2one('product.product', domain=[('detailed_type','=','service')])
    journal_id = fields.Many2one('account.journal', domain=[('type','=','purchase')])


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    commission_perc = fields.Float(related='company_id.commission_perc', readonly=False)
    product_id = fields.Many2one('product.product',related='company_id.product_id', readonly=False)
    journal_id = fields.Many2one('account.journal',related='company_id.journal_id', readonly=False)
