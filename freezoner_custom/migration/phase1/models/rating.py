from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class Rating(models.Model):
    """
    Rating Model Extension
    Extends the standard rating model with additional fields and functionality
    for enhanced rating management
    """
    _inherit = 'rating.rating'
    _description = 'Rating Extension'

    priority = fields.Selection([
        ('0', 'Not Rated'),
        ('1', 'Low'),
        ('2', 'Normal'),
        ('3', 'Medium'),
        ('4', 'High'),
        ('5', 'Very High')
    ], string='Priority Rating',
        tracking=True,
        default='0',
        help='Priority level of the rating'
    )
    
    category = fields.Selection([
        ('service', 'Service Quality'),
        ('communication', 'Communication'),
        ('delivery', 'Delivery Time'),
        ('quality', 'Product Quality'),
        ('support', 'Customer Support'),
        ('other', 'Other')
    ], string='Rating Category',
        tracking=True,
        default='service',
        help='Category of the rating'
    )
    
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        tracking=True,
        help='Related project',
        index=True
    )
    
    task_id = fields.Many2one(
        'project.task',
        string='Task',
        tracking=True,
        help='Related task',
        index=True
    )
    
    sale_id = fields.Many2one(
        'sale.order',
        string='Sales Order',
        tracking=True,
        help='Related sales order',
        index=True
    )
    
    rating_date = fields.Datetime(
        string='Rating Date',
        default=fields.Datetime.now,
        tracking=True,
        help='Date and time when the rating was given'
    )
    
    is_public = fields.Boolean(
        string='Public Rating',
        default=True,
        tracking=True,
        help='Whether this rating is visible to the public'
    )
    
    response_text = fields.Text(
        string='Response',
        tracking=True,
        help='Response to the rating feedback'
    )
    
    response_date = fields.Datetime(
        string='Response Date',
        tracking=True,
        help='Date and time when the response was given'
    )
    
    responded_by = fields.Many2one(
        'res.users',
        string='Responded By',
        tracking=True,
        help='User who responded to the rating'
    )
    
    rating_status = fields.Selection([
        ('pending', 'Pending'),
        ('responded', 'Responded'),
        ('closed', 'Closed'),
        ('archived', 'Archived')
    ], string='Status',
        default='pending',
        tracking=True,
        compute='_compute_rating_status',
        store=True,
        help='Current status of the rating'
    )

    @api.depends('response_text', 'response_date', 'responded_by')
    def _compute_rating_status(self):
        for rating in self:
            if rating.response_text and rating.response_date and rating.responded_by:
                rating.rating_status = 'responded'
            elif not rating.response_text and not rating.response_date and not rating.responded_by:
                rating.rating_status = 'pending'
            else:
                rating.rating_status = 'closed'

    @api.constrains('rating', 'priority')
    def _check_rating_priority(self):
        for rating in self:
            if rating.rating and rating.priority == '0':
                raise ValidationError(_('Priority must be set when a rating value is provided.'))

    def action_respond(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Respond to Rating'),
            'res_model': 'rating.rating',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': {
                'default_rating_status': 'responded',
                'default_response_date': fields.Datetime.now(),
                'default_responded_by': self.env.user.id,
            }
        }

    def action_close(self):
        self.ensure_one()
        if self.rating_status != 'closed':
            self.write({
                'rating_status': 'closed',
                'response_date': fields.Datetime.now(),
                'responded_by': self.env.user.id
            })
        return True

    def action_archive(self):
        self.ensure_one()
        if self.rating_status != 'archived':
            self.write({
                'rating_status': 'archived',
                'is_public': False
            })
        return True

    def action_reopen(self):
        self.ensure_one()
        if self.rating_status in ['closed', 'archived']:
            self.write({
                'rating_status': 'pending',
                'response_text': False,
                'response_date': False,
                'responded_by': False
            })
        return True

    @api.model
    def create(self, vals):
        if vals.get('rating') and not vals.get('priority'):
            vals['priority'] = '3'  # Default to Medium priority
        return super(Rating, self).create(vals)

    def write(self, vals):
        if 'rating' in vals and vals['rating'] and not vals.get('priority'):
            vals['priority'] = '3'  # Default to Medium priority
        return super(Rating, self).write(vals)

    def name_get(self):
        result = []
        for rating in self:
            name = f"{rating.res_name} - {rating.rating}/5"
            if rating.category:
                name += f" ({rating.category})"
            result.append((rating.id, name))
        return result

class MailThread(models.AbstractModel):
    """
    Mail Thread Model Extension
    Extends the standard mail thread with enhanced rating functionality
    """
    _inherit = 'mail.thread'

    def _notify_get_recipients_groups(self, msg_vals=None):
        groups = super()._notify_get_recipients_groups(msg_vals=msg_vals)
        if not self:
            return groups

        # Add portal customer group if applicable
        if hasattr(self, '_portal_ensure_token'):
            partners = self._mail_get_partners()
            if partners:
                customer = partners[0]
                access_token = self._portal_ensure_token()
                local_msg_vals = dict(msg_vals or {})
                local_msg_vals.update({
                    'access_token': access_token,
                    'pid': customer.id,
                    'hash': self._sign_token(customer.id),
                })
                local_msg_vals.update(customer.signup_get_auth_param()[customer.id])
                access_link = self._notify_get_action_link('view', **local_msg_vals)

                groups.append((
                    'portal_customer',
                    lambda pdata: pdata['id'] == customer.id,
                    {
                        'has_button_access': True,
                        'button_access': {'url': access_link},
                        'notification_is_customer': True,
                    }
                ))

                # Enable portal access
                portal_group = next((group for group in groups if group[0] == 'portal'), None)
                if portal_group:
                    portal_group[2].update({
                        'active': True,
                        'has_button_access': True
                    })

        return groups

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if len(self) > 1:
            raise ValueError(_("Expected singleton: %s") % self)

        rating_id = kwargs.pop('rating_id', False)
        rating_value = kwargs.pop('rating_value', False)
        rating_feedback = kwargs.pop('rating_feedback', False)
        rating_category = kwargs.pop('rating_category', 'service')
        rating_priority = kwargs.pop('rating_priority', '3')

        message = super(MailThread, self).message_post(**kwargs)

        if rating_value is not None:
            rating_vals = {
                'rating': float(rating_value),
                'feedback': rating_feedback,
                'res_model_id': self.env['ir.model']._get_id(self._name),
                'res_id': self.id,
                'message_id': message.id,
                'consumed': True,
                'partner_id': self.env.user.partner_id.id,
                'category': rating_category,
                'priority': rating_priority,
                'rating_date': fields.Datetime.now(),
            }

            # Add related record if available
            if hasattr(self, 'project_id'):
                rating_vals['project_id'] = self.project_id.id
            if hasattr(self, 'task_id'):
                rating_vals['task_id'] = self.task_id.id
            if hasattr(self, 'sale_id'):
                rating_vals['sale_id'] = self.sale_id.id

            self.env['rating.rating'].sudo().create(rating_vals)
        elif rating_id:
            self.env['rating.rating'].browse(rating_id).write({'message_id': message.id})

        return message 