
from odoo import api, fields, models

class SurveyRating(models.Model):
    _name = 'survey.rating'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'customer_id'

    task_id = fields.Many2one('project.task')
    feedback = fields.Text(' Feedback ')
    feedback_rating = fields.Selection([
        ('0', '0'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
    ], string='Rating', required=True, default='0')
    customer_id = fields.Many2one("res.users", string='Customer')
