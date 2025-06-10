from odoo import api, fields, models
from odoo.exceptions import ValidationError
from collections import defaultdict
from datetime import timedelta
from datetime import timedelta

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    active = fields.Boolean(default=True, copy=False, tracking=True)
    system_expiry_date = fields.Date(string="System Expiry Date", copy=False)
    state = fields.Selection(
        selection=[
            ('draft', "Pro-forma Invoice"),
            ('sent', "Pro-forma Invoice Sent"),
            ('sale', "Pro-forma Confirm"),
            ('done', "Locked"),
            ('cancel', "Cancelled"),
        ],
        string="Status",
        readonly=True, copy=False, index=True,
        tracking=3,
        default='draft')
    payment_method = fields.Selection(selection=[
        ('bank', "Bank"),
        ('visa', "Stripe"),
    ], string="Payment Method", tracking=3, default='bank', required=True)
    sov_ids = fields.One2many('sale.sov', 'sale_id')
    analytic_item_ids = fields.Many2many('account.analytic.line', string='Analytic Items',
                                         compute='get_analytic_item_ids')
    total_revenue = fields.Float(string='Total Revenue', compute='get_total_revenue', store=True)
    total_planned_expenses = fields.Float(string='Total Planned Expenses', compute='get_total_planned_expenses',
                                          store=True)
    total_net_achievement = fields.Float(string='Total Net Achievement', compute='get_total_net_achievement',
                                         store=True)
    date_confirmed = fields.Datetime(compute='get_first_confirmed_date', store=True)
    validity_date = fields.Date(
        string="Expiration",
        compute='_compute_validity_date',
        store=True, readonly=True, copy=False, precompute=True,)
    is_expired = fields.Boolean(compute='check_is_expired' )

    @api.depends('validity_date')
    def check_is_expired(self):
        for rec in self:
            if rec.validity_date and rec.state in ['draft', 'sent'] and rec.validity_date < fields.Date.context_today(self) :
                rec.is_expired = True
            else:
                rec.is_expired = False


    @api.depends('create_date')
    def _compute_validity_date(self):
        for order in self:
            if order.create_date:
                order.validity_date = order.create_date + timedelta(days=30)
            else:
                order.validity_date = False

    def compute_validity_date(self):
        query = """
            UPDATE sale_order
            SET validity_date = create_date + INTERVAL '30 days'
            WHERE create_date IS NOT NULL
        """
        self.env.cr.execute(query)

    def action_sale_expiration(self):
        today = fields.Date.context_today(self)
        sale_orders = self.env['sale.order'].sudo().search([
            ('state', 'in', ['draft', 'sent']),
            ('validity_date', '<=', today)  # Get orders where validity_date is past
        ])
        print('Expired Sales Orders:', sale_orders)
        if sale_orders:
            for so in sale_orders:
                if so.validity_date and so.is_expired and so.validity_date <= today:
                    self.env.cr.execute(
                        "UPDATE sale_order SET state = %s, system_expiry_date = %s WHERE id = %s",
                        ('cancel', today, so.id)
                    )

    def action_sale_expiration_archive(self):
        today = fields.Date.context_today(self)
        sale_orders = self.env['sale.order'].sudo().search([
            ('state', '=', 'cancel'),
            ('system_expiry_date', '<=', today)  # Get orders where validity_date is past
        ])
        if sale_orders:
            for so in sale_orders:
                sub = (today - so.system_expiry_date).days if so.system_expiry_date else 0  # Ensure no NoneType error
                if so.validity_date and  sub >= 30:
                    self.env.cr.execute("UPDATE sale_order set active = False WHERE id=%s" % (so.id))

    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        for rec in self:
            for task in rec.tasks_ids:
                task.document_type_ids.unlink()
                task.document_required_type_ids.unlink()
        return res

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        for rec in self:
            if rec.partner_id and rec.partner_id.company_type == 'company':
                if not rec.partner_id.phone:
                    raise ValidationError(" Please add phone number for the customer ")
                if not rec.partner_id.email:
                    raise ValidationError(" Please add email for the customer ")
                if not rec.partner_id.license_authority_id:
                    raise ValidationError(" Please add license authority for the customer ")
                if not rec.partner_id.incorporation_date:
                    raise ValidationError(" Please add incorporation date for the customer ")
                if not rec.partner_id.license_number:
                    raise ValidationError(" Please add license number for the customer ")
            if rec.partner_id and rec.partner_id.company_type == 'person':
                if not rec.partner_id.phone:
                    raise ValidationError(" Please add phone number for the customer ")
                if not rec.partner_id.email:
                    raise ValidationError(" Please add email for the customer ")
                if not rec.partner_id.gender:
                    raise ValidationError(" Please add gender for the customer ")
                if not rec.partner_id.nationality_id:
                    raise ValidationError(" Please add nationality for the customer ")
        return res

    @api.constrains('partner_id')
    def check_partner(self):
        for rec in self:
            user = self.env.user
            team = self.env['crm.team'].sudo().search([('id', '=', 1)])
            if team and user.id in team.member_ids.ids:
                partner = rec.partner_id
                if partner and partner.create_date:
                    create_date = partner.create_date.date()  # Convert to date
                    if create_date < (fields.Date.context_today(self) - timedelta(days=180)):
                        raise ValidationError("Customer Profile has been created more than six (6) months ago. As a member of Sales Team, you are not allowed to create an invoice for this contact. Please contact your Line Manager for assistance .")

    @api.model
    def create(self, values):
        res = super(SaleOrder, self).create(values)
        if self.partner_id and self.partner_id.company_type == 'company':
            if not self.partner_id.phone:
                raise ValidationError(" Please add phone number for the customer ")
            if not self.partner_id.email:
                raise ValidationError(" Please add email for the customer ")
            if not self.partner_id.license_authority_id:
                raise ValidationError(" Please add license authority for the customer ")
            if not self.partner_id.incorporation_date:
                raise ValidationError(" Please add incorporation date for the customer ")
            if not self.partner_id.license_number:
                raise ValidationError(" Please add license number for the customer ")
        if self.partner_id and self.partner_id.company_type == 'person':
            if not self.partner_id.phone:
                raise ValidationError(" Please add phone number for the customer ")
            if not self.partner_id.email:
                raise ValidationError(" Please add email for the customer ")
            if not self.partner_id.gender:
                raise ValidationError(" Please add gender for the customer ")
            if not self.partner_id.nationality_id:
                raise ValidationError(" Please add nationality for the customer ")
        return res

    @api.depends('message_ids')
    def get_first_confirmed_date(self):
        for rec in self:
            first_confirmed_date = None
            for line in rec.message_ids:
                if line.subtype_id.description == 'Quotation confirmed':
                    if first_confirmed_date is None or line.date < first_confirmed_date:
                        first_confirmed_date = line.date
            rec.date_confirmed = first_confirmed_date

    def get_analytic_item_ids(self):
        for rec in self:
            analytic_item_ids = self.env['account.analytic.line'].sudo().search(
                [('account_id.name', 'ilike', rec.name)]).ids
            if analytic_item_ids:
                rec.analytic_item_ids = analytic_item_ids
            else:
                rec.analytic_item_ids = []

    @api.depends('sov_ids', 'sov_ids.revenue')
    def get_total_revenue(self):
        for rec in self:
            rec.total_revenue = sum(line.revenue for line in rec.sov_ids)

    @api.depends('sov_ids', 'sov_ids.planned_expenses')
    def get_total_planned_expenses(self):
        for rec in self:
            rec.total_planned_expenses = sum(line.planned_expenses for line in rec.sov_ids)

    @api.depends('sov_ids', 'sov_ids.net')
    def get_total_net_achievement(self):
        for rec in self:
            rec.total_net_achievement = sum(line.net for line in rec.sov_ids)

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals.update({
            'sale_id': self.id,
            'payment_method': self.payment_method,
        })
        return invoice_vals

    def action_update_manager(self):
        for rec in self:
            for project in rec.project_ids:
                project.write({'user_id': rec.user_id.id})

    # Old function
    # def action_confirm(self):
    #     res = super(SaleOrder, self).action_confirm()
    #     self.check_crm_payment()
    #     for project in self.project_ids:
    #         project.write({'state': 'b_new'})
    #         project.write({'user_id': self.user_id.id})
    #         for line in self.order_line:
    #             if line.id ==  project.sale_line_id.id:
    #                 date_ref = "{:02d}{:02d}".format(self.create_date.year % 100, self.create_date.month)
    #                 project.name = f"{self.name} - {date_ref} - {line.product_id.name}"
    #     for task in self.tasks_ids:
    #         task_id = 0
    #         if task.name in ['Documents To Be Collected', 'Collecting Required Documents']:
    #             task.write({'user_ids': [(4, self.user_id.id)]})
    #
    #         for line in self.order_line:
    #             if task.name in ['Upload Corporate Documents And Rename All Files', 'Uploading Deliverables']:
    #                 for ll in line.product_id.product_tmpl_id.document_type_ids:
    #                     if hasattr(ll, 'document_id') and ll.document_id and hasattr(ll.document_id, 'id'):
    #                         if ll.document_id.id in task.sale_line_id.product_id.product_tmpl_id.document_type_ids.mapped(
    #                                 'document_id').ids and line.product_id.product_tmpl_id.id == task.sale_line_id.product_id.product_tmpl_id.id:
    #                             attachment = []
    #                             document = self.env['res.partner.document'].sudo().search(
    #                                 [('partner_id', '=', self.partner_id.id),
    #                                  ('name', '=', ll.document_id.name)], limit=1)
    #                             if document and document.attachment_ids:
    #                                 for att in document.attachment_ids:
    #                                     attachment.append(att.id)
    #                             self.env['task.document.lines'].sudo().create({
    #                                 'document_id': ll.document_id.id,
    #                                 'name': str(str(ll.document_id.name) + ' - ' + str(self.partner_id.name)),
    #                                 'is_required': ll.is_required,
    #                                 'task_id': task.id,
    #                                 'attachment_ids': attachment or [],
    #                                 'issue_date': document.issue_date or False,
    #                                 'expiration_date': document.expiration_date or False,
    #                             })
    #
    #                             print('attachment  ======= >>  ' , attachment)
    #
    #             if task.name in ['Documents To Be Collected', 'Collecting Required Documents']:
    #                 if line.product_id.product_tmpl_id.document_required_type_ids:
    #                     for lll in line.product_id.product_tmpl_id.document_required_type_ids:
    #                         if hasattr(lll, 'document_id') and lll.document_id and hasattr(lll.document_id, 'id'):
    #                             if lll.document_id.id in task.sale_line_id.product_id.product_tmpl_id.document_required_type_ids.mapped('document_id').ids and line.product_id.product_tmpl_id.id == task.sale_line_id.product_id.product_tmpl_id.id:
    #                                 attachments = []
    #                                 document = self.env['res.partner.document'].sudo().search(
    #                                     [('partner_id', '=', self.partner_id.id),
    #                                      ('type_id.id', '=', lll.document_id.id)], limit=1)
    #                                 print(' document  ==>   ', document)
    #                                 if document and document.attachment_ids:
    #                                     for att in document.attachment_ids:
    #                                         attachments.append(att.id)
    #                                 self.env['task.document.required.lines'].sudo().create({
    #                                     'document_id': lll.document_id.id,
    #                                     'name': str(str(lll.document_id.name) + ' - ' + str(self.partner_id.name)),
    #                                     'is_required': lll.is_required,
    #                                     'task_id': task.id,
    #                                     'attachment_ids': attachments or [],
    #                                     'issue_date': document.issue_date or False,
    #                                     'expiration_date': document.expiration_date or False,
    #                                 })
    #
    #             if task.name == line.name:
    #                 task_id = task.id
    #
    #         if task_id > 0:
    #             self.env['project.task'].sudo().search([('id', '=', task_id)], limit=1).unlink()
    #     return res

    @api.depends('order_line.product_id', 'order_line.project_id')
    def _compute_project_ids(self):
        is_project_manager = self.user_has_groups('project.group_project_manager')
        projects = self.env['project.project'].search([('sale_order_id', 'in', self.ids)])
        projects_per_so = defaultdict(lambda: self.env['project.project'])
        for project in projects:
            projects_per_so[project.sale_order_id.id] |= project

        for order in self:
            # Fetch projects from various sources
            projects = order.order_line.mapped('product_id.project_id')
            projects |= order.order_line.mapped('project_id')
            projects |= order.project_id
            projects |= projects_per_so[order.id or order._origin.id]

            # Add additional projects with domain ('sale_id', '=', order.id)
            additional_projects = self.env['project.project'].search([('sale_id', '=', order.id)])
            projects |= additional_projects

            # Restrict projects if user is not a project manager
            if not is_project_manager:
                projects = projects._filter_access_rules('read')

            # Assign computed projects and count
            order.project_ids = projects
            order.project_count = len(projects)

    def action_create_project_tasks(self):
        for rec in self:
            # Collect products with `service_tracking == 'new_workflow'`
            products_to_process = rec.order_line.filtered(
                lambda line: line.product_id.service_tracking == 'new_workflow'
            ).mapped('product_id')

            if products_to_process:
                # Create a new project if it doesn't exist for the sale order
                project = self.env['project.project'].search([('sale_id', '=', rec.id)], limit=1)
                if not project:
                    project = self.env['project.project'].create({
                        'name': f"{rec.name} - {rec.partner_id.name}",
                        'state': 'b_new',
                        'sale_id': rec.id,
                        'user_id': rec.user_id.id,
                        'partner_id': rec.partner_id.id,
                        'product_ids': [(6, 0, rec.order_line.mapped('product_id').ids)],
                    })
                    if project:
                        ProjectProduct = self.env['project.project.products']
                        for prod in project.product_ids:
                            ProjectProduct.sudo().create({
                                'project_id': project.id,
                                'product_id': prod.id,
                            })
                    stages = self.env['project.task.type'].sudo().search([])
                    for stage_id in [243, 65, 28, 29, 67]:
                        stage = stages.filtered(lambda s: s.id == stage_id)
                        if stage:
                            stage.project_ids = [(4, project.id)]

                # Track created tasks to avoid duplication
                existing_task_names = set(project.task_ids.mapped('name'))

                # Prepare tasks to be created
                tasks_to_create = []
                merged_tasks = defaultdict(lambda: defaultdict(list))

                # Group tasks by name and merge child_ids
                for product in products_to_process:
                    for task in product.task_ids:
                        task_data = merged_tasks[task.name]
                        task_data['description'] = task.description
                        task_data['sequence'] = task.sequence
                        task_data['planned_hours'] = task.planned_hours
                        task_data['user_ids'] = task.user_ids.ids
                        task_data['child_ids'] += [
                            {
                                'is_subtask': True,
                                'name': child.name,
                                'project_id': project.id,
                                'display_project_id': project.id,
                                'description': child.description,
                                'sequence': child.sequence,
                                'planned_hours': child.planned_hours,
                                # Corrected: Remove rec.user_id from child task's user_ids
                                'user_ids': [(6, 0, child.user_ids.ids)] if child.user_ids else [],
                                'checkpoint_ids': [
                                    (0, 0, {  # Command to create a new checkpoint
                                        'reached_checkpoint_ids': [(6, 0, cp.reached_checkpoint_ids.ids)],
                                        'stage_id': cp.stage_id.id,
                                        'milestone_id': cp.milestone_id.id,
                                        'sequence': cp.sequence,
                                    }) for cp in child.checkpoint_ids
                                ],
                            } for child in task.child_ids
                        ]

                # Deduplicate child_ids for each task
                for task_name, task_data in merged_tasks.items():
                    if task_name not in existing_task_names:
                        unique_children = {child['name']: child for child in task_data['child_ids']}.values()

                        tasks_to_create.append({
                            'name': task_name,
                            'project_id': project.id,
                            'display_project_id': project.id,
                            'sale_order_id': rec.id,
                            # Parent task still includes sale user and task's user_ids
                            'user_ids': [(6, 0, [rec.user_id.id] + (
                                task_data['user_ids'] if task_data.get('user_ids') else []))],
                            'description': task_data['description'],
                            'planned_hours': task_data['planned_hours'],
                            'sequence': task_data['sequence'],
                            'child_ids': [(0, 0, {
                                'is_subtask': True,
                                'name': child['name'],
                                'description': child['description'],
                                'sequence': child['sequence'],
                                'planned_hours': child['planned_hours'],
                                'project_id': project.id,
                                'sale_order_id': rec.id,
                                'user_ids': child['user_ids'],  # Now uses corrected user_ids (no sale user)
                                'checkpoint_ids': child['checkpoint_ids'],
                            }) for child in unique_children]
                        })
                        existing_task_names.add(task_name)

                # Create tasks in bulk
                if tasks_to_create:
                    self.env['project.task'].create(tasks_to_create)

                # Prepare task.document.lines, task.document.required.lines, and partner fields in bulk

                document_lines_to_create = []
                document_required_lines_to_create = []
                # Track processed (document_type_id, partner_id) combinations
                processed_docs = set()
                processed_required_docs = set()

                for line in rec.order_line:
                    for doc_line in line.product_id.product_tmpl_id.document_type_ids:
                        doc_type = doc_line.document_id
                        if not doc_type:
                            continue

                        partner_id = rec.partner_id.id
                        unique_key = (doc_type.id, partner_id)

                        # Skip if already processed
                        if unique_key in processed_docs:
                            continue
                        processed_docs.add(unique_key)

                        # Check existing document
                        existing_doc = self.env['documents.document'].sudo().search([
                            ('type_id', '=', doc_type.id),
                            ('partner_id', '=', partner_id),
                        ], limit=1)

                        if existing_doc:
                            existing_doc.sudo().write({'deliverable_project_id': project.id})
                        else:
                            document_lines_to_create.append({
                                'deliverable_project_id': project.id,
                                'folder_id': project.documents_folder_id.id,
                                # 'partner_id': partner_id,
                                'type_id': doc_type.id,
                                'name': f"{doc_type.name} - {rec.partner_id.name}",
                                'issue_date': False,
                                'expiration_date': False,
                            })

                    # Process document_required_type_ids (Requirements)
                    for req_doc_line in line.product_id.product_tmpl_id.document_required_type_ids:
                        req_doc_type = req_doc_line.document_id
                        if not req_doc_type:
                            continue

                        partner_id = rec.partner_id.id
                        unique_key = (req_doc_type.id, partner_id)

                        # Skip if already processed
                        if unique_key in processed_required_docs:
                            continue
                        processed_required_docs.add(unique_key)

                        # Check existing document
                        existing_doc = self.env['documents.document'].sudo().search([
                            ('type_id', '=', req_doc_type.id),
                            ('partner_id', '=', partner_id),
                        ], limit=1)

                        if existing_doc:
                            existing_doc.sudo().write({'required_project_id': project.id})
                        else:
                            document_required_lines_to_create.append({
                                'required_project_id': project.id,
                                'folder_id': project.documents_folder_id.id,
                                # 'partner_id': partner_id,
                                'type_id': req_doc_type.id,
                                'name': f"{req_doc_type.name} - {rec.partner_id.name}",
                                'issue_date': False,
                                'expiration_date': False,
                            })

                # Bulk create documents
                if document_required_lines_to_create:
                    self.env['documents.document'].sudo().create(document_required_lines_to_create)
                if document_lines_to_create:
                    self.env['documents.document'].sudo().create(document_lines_to_create)

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        self.check_crm_payment()
        for project in self.project_ids:
            project.write({'state': 'b_new'})
            project.write({'user_id': self.user_id.id})
            for line in self.order_line:
                if line.id == project.sale_line_id.id:
                    date_ref = "{:02d}{:02d}".format(self.create_date.year % 100, self.create_date.month)
                    project.name = f"{self.name} - {date_ref} - {line.product_id.name}"
                    for ll in line.product_id.product_tmpl_id.document_type_ids:
                        if hasattr(ll, 'document_id') and ll.document_id and hasattr(ll.document_id, 'id'):
                            self.env['task.document.lines'].sudo().create({
                                'project_id': project.id,
                                'document_id': ll.document_id.id,
                                'name': str(str(ll.document_id.name) + ' - ' + str(self.partner_id.name)),
                                'is_required': ll.is_required,
                                'issue_date': False,
                                'expiration_date': False,
                            })
                    if line.product_id.product_tmpl_id.document_required_type_ids:
                        for lll in line.product_id.product_tmpl_id.document_required_type_ids:
                            if hasattr(lll, 'document_id') and lll.document_id and hasattr(lll.document_id, 'id'):
                                self.env['task.document.required.lines'].sudo().create({
                                    'project_id': project.id,
                                    'document_id': lll.document_id.id,
                                    'name': str(str(lll.document_id.name) + ' - ' + str(self.partner_id.name)),
                                    'is_required': lll.is_required,
                                    'issue_date': False,
                                    'expiration_date': False,
                                })
            stages = self.env['project.task.type'].sudo().search([])
            for stage_id in [64, 65, 66, 67, 29, 30]:
                stage = stages.filtered(lambda s: s.id == stage_id)
                if stage:
                    stage.project_ids = [project.id]
        self.action_create_project_tasks()
        self.remove_duplicate_tasks()
        today = fields.Date.context_today(self)
        # if today > self.validity_date:
        #     raise ValidationError("Validity date has passed")
        return res

    def remove_duplicate_tasks(self):
        for rec in self:
            seen_names = set()
            duplicate_tasks = self.env['project.task']  # Adjust the model if necessary

            for task in rec.tasks_ids:
                if task.name in seen_names:
                    duplicate_tasks |= task
                else:
                    seen_names.add(task.name)

            # Unlink the duplicate tasks
            if duplicate_tasks:
                duplicate_tasks.unlink()
                print('Removed duplicate tasks:', duplicate_tasks)

    def check_crm_payment(self):
        for rec in self:
            return {
                'res_model': 'sale.crm.wizard',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
                'context': {'default_sale_id': rec.id},
                'view_id': self.env.ref("freezoner_custom.sale_crm_wizard_form_view").id,
                'target': 'new'
            }

    # def sov_old(self):
    #     sales = self.env['sale.order'].sudo().search([])
    #     for rec in sales:
    #         rec.prepare_lines()

    @api.onchange('payment_method', 'order_line')
    def action_visa(self):
        self.add_visa_line()

    @api.onchange('order_line')
    def action_calculate(self):
        self.prepare_lines()

    def prepare_lines(self):
        sov_lines = []
        self.sov_ids = None
        for rec in self:
            if rec.order_line:
                for line in rec.order_line:
                    tax = 0.0
                    for t in line.tax_id:
                        tax += t.amount
                    sov_lines.append(
                        (0, 0, {
                            'product_id': line.product_id.id,
                            'qty': line.product_uom_qty,
                            'unit_cost': 0.0,
                            'name': line.name,
                            'unit_price': line.price_unit + ((tax * line.price_unit) / 100),
                        }))
                sov_lines.append(
                    (0, 0, {
                        'product_id': self.env['product.product'].sudo().search([('is_service_commission', '=', True)],
                                                                                limit=1).id,
                        'qty': 1,
                        'unit_cost': 0.0,
                        'unit_price': 0.0,
                    }))
                self.write({'sov_ids': sov_lines})

    def add_visa_line(self):
        for rec in self:
            lines = []
            if rec.payment_method == 'visa':
                total = 0.0
                product = self.env['product.product'].sudo().search([('stripe_visa', '=', True)], limit=1)
                for line in rec.order_line:
                    if line.product_id.product_tmpl_id.stripe_visa == False:
                        total += line.price_total
                product.lst_price = total * 0.04
                if product not in rec.order_line.mapped('product_id'):
                    lines.append(
                        (0, 0, {
                            'product_id': product.id,
                            'name': 'Kindly note that an additional charge of 4% is applicable to the total invoice amount to cover online payment processing fees. Your attention to this matter is appreciated.',
                            'product_uom_qty': 1,
                            'price_unit': total,
                        }))
                    self.write({'order_line': lines})
            if rec.payment_method == 'bank':
                product = self.env['product.product'].sudo().search([('stripe_visa', '=', True)], limit=1)
                for line in rec.order_line:
                    if product.id == line.product_id.id:
                        line.unlink()
