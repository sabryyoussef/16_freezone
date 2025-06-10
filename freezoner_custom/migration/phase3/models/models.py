from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class DocumentsShareWizard(models.TransientModel):
    _inherit = 'documents.share'

    document_share_id = fields.Many2one(
        'documents.share',
        string='Documents Share',
        tracking=True
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        res['document_share_id'] = self.env.context.get('active_id')
        return res

    def create_activity(self):
        self.ensure_one()
        partners = [
            self.document_ids[0].partner_id.id if self.document_ids else False,
            self.create_uid.partner_id.id
        ]
        
        if not partners[0]:
            raise ValidationError(_("No documents found to create activity for."))
        
        # Create calendar event
        calendar_event = self.env['calendar.event'].create({
            'name': self.name,
            'start': self.date_deadline,
            'stop': self.date_deadline,
            'user_id': self.user_id.id,
            'show_as': 'free',
            'partner_ids': [(6, 0, partners)],
            'alarm_ids': [(6, 0, [1, 2])],
            'document_share_id': self.id,
        })

        # Create mail activity
        self.env['mail.activity'].create({
            'activity_type_id': self.activity_type_id.id,
            'summary': self.name,
            'date_deadline': self.date_deadline,
            'user_id': self.user_id.id,
            'calendar_event_id': calendar_event.id,
            'res_id': self.id,
            'res_model_id': self.env['ir.model']._get('documents.share').id,
        })

        return calendar_event


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    document_share_id = fields.Many2one(
        'documents.share',
        string='Documents Share',
        tracking=True,
        ondelete='set null'
    )


class ProjectProduct(models.Model):
    _name = 'project.project.products'
    _description = 'Project Products'
    _order = 'project_id, product_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Basic Fields
    name = fields.Char(
        compute='_compute_name',
        store=True,
        string='Name'
    )
    active = fields.Boolean(
        default=True,
        tracking=True
    )

    # Related Fields
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        tracking=True,
        index=True
    )
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        required=True,
        tracking=True,
        index=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        related='project_id.partner_id',
        string='Customer',
        store=True,
        tracking=True
    )

    # Date Fields
    date_start = fields.Date(
        related='project_id.date_start',
        string='Project Planned Date',
        store=True,
        tracking=True
    )
    date_end = fields.Date(
        related='project_id.date',
        string='Project Complete Date',
        store=True,
        tracking=True
    )

    # Related Records
    remarks_ids = fields.Many2many(
        'project.project.products.remarks',
        string='Remarks',
        tracking=True
    )

    # Computed Methods
    @api.depends('product_id', 'project_id')
    def _compute_name(self):
        for record in self:
            if record.product_id and record.project_id:
                record.name = f"{record.project_id.name} - {record.product_id.name}"
            else:
                record.name = False

    # Action Methods
    def action_add_remarks(self):
        self.ensure_one()
        return {
            'name': _('Add Remarks'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'remarks.wizard',
            'context': {
                'default_line_id': self.id,
                'default_project_id': self.project_id.id,
                'default_product_id': self.product_id.id
            },
            'view_id': self.env.ref('freezoner_custom.remarks_wizard_form_view').id,
            'target': 'new',
        }

    # CRUD Methods
    @api.model_create_multi
    def create(self, vals_list):
        # Validate project and product combinations
        for vals in vals_list:
            if vals.get('project_id') and vals.get('product_id'):
                existing = self.search([
                    ('project_id', '=', vals['project_id']),
                    ('product_id', '=', vals['product_id']),
                    ('active', '=', True)
                ])
                if existing:
                    raise ValidationError(_(
                        "Product %(product)s is already added to project %(project)s"
                    ) % {
                        'product': self.env['product.product'].browse(vals['product_id']).name,
                        'project': self.env['project.project'].browse(vals['project_id']).name
                    })
        return super().create(vals_list)

    def write(self, vals):
        # Validate project and product combinations
        if 'project_id' in vals or 'product_id' in vals:
            for record in self:
                project_id = vals.get('project_id', record.project_id.id)
                product_id = vals.get('product_id', record.product_id.id)
                existing = self.search([
                    ('project_id', '=', project_id),
                    ('product_id', '=', product_id),
                    ('active', '=', True),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(_(
                        "Product %(product)s is already added to project %(project)s"
                    ) % {
                        'product': self.env['product.product'].browse(product_id).name,
                        'project': self.env['project.project'].browse(project_id).name
                    })
        return super().write(vals)


class ProjectProductRemarks(models.Model):
    _name = 'project.project.products.remarks'
    _description = 'Project Product Remarks'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Remark',
        required=True,
        tracking=True
    )
    active = fields.Boolean(
        default=True,
        tracking=True
    )
    product_ids = fields.Many2many(
        'project.project.products',
        string='Products',
        tracking=True
    )

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Remark must be unique!')
    ] 