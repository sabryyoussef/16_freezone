
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError


class doc(models.Model):
    _name = 'request.document'


class TaskLines(models.Model):
    _name = 'task.document.lines'

    project_id = fields.Many2one('project.project')
    task_id = fields.Many2one('project.task')
    document = fields.Binary(string="Document")
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments',required=True)
    document_id = fields.Many2one('res.partner.document.type')
    name = fields.Char()
    is_required_expiration = fields.Boolean('Required Expiration')
    is_moved = fields.Boolean()
    issue_date = fields.Date()
    expiration_date = fields.Date()
    is_required = fields.Boolean('Check Required')
    is_verify = fields.Boolean(compute='check_is_verify')
    source_document_id = fields.Many2one("res.partner.document", string="Document Source",
                                         compute='get_document_source')
    partner_id = fields.Many2one("res.partner", string="Customer")

    @api.onchange('project_id','project_id.hand_partner_id')
    def _onchange_partner_id(self):
        for rec in self:
            if rec.project_id:
                rec.partner_id = rec.project_id.hand_partner_id.id

    @api.depends('task_id', 'document_id')
    def get_document_source(self):
        for rec in self:
            rec.source_document_id = self.env['res.partner.document'].sudo().search([('task_id', '=', rec.task_id.id),
                                                                                     ('type_id', '=',
                                                                                      rec.document_id.id),
                                                                                     ('name', '=', rec.name),
                                                                                     ('issue_date', '=',
                                                                                      rec.issue_date)],
                                                                                    limit=1).id or False

    @api.depends('task_id', 'document_id', 'name', 'issue_date')
    def check_is_verify(self):
        for rec in self:
            document = self.env['res.partner.document'].sudo().search([('task_id', '=', rec.task_id.id),
                                                                       ('type_id', '=', rec.document_id.id),
                                                                       ('name', '=', rec.name),('is_verify','=', True),
                                                                       ('issue_date', '=', rec.issue_date)])
            if document:
                rec.is_verify = True
            else:
                rec.is_verify = False

    def unlink(self):
        for rec in self:
            if rec.task_id and rec.is_required:
                rec.task_id._message_log(
                    body=" ( " + str(rec.document_id.name) + ' By : ' + str(
                        rec.write_uid.name),
                    subject=_('Document Deleted'), message_type='comment',
                )
            if rec.project_id and rec.is_required:
                rec.project_id._message_log(
                    body=" ( " + str(rec.document_id.name) + ' By : ' + str(
                        rec.write_uid.name),
                    subject=_('Document Deleted'), message_type='comment',
                )
        return super(TaskLines, self).unlink()

    # def unlink(self):
    #     for rec in self:
    #         print('  ')
    #         if rec.is_required == True and rec.task_id.name in ['Upload Corporate Documents And Rename All Files','Uploading Deliverables']:
    #             raise ValidationError('You Can Not Delete Required Line')
    #     return super(TaskLines, self).unlink()

class TaskRequiredLines(models.Model):
    _name = 'task.document.required.lines'

    project_id = fields.Many2one('project.project')
    task_id = fields.Many2one('project.task')
    document = fields.Binary(string="Document")
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments',  )
    document_id = fields.Many2one('res.partner.document.type')
    name = fields.Char()
    is_moved = fields.Boolean()
    is_required_expiration = fields.Boolean('Required Expiration')
    issue_date = fields.Date()
    expiration_date = fields.Date()
    is_required = fields.Boolean('Check Required')
    is_verify = fields.Boolean(compute='check_is_verify')
    is_ready = fields.Boolean(compute='check_line_is_ready')
    source_document_id = fields.Many2one("res.partner.document", string="Document Source", compute='get_document_source')
    project_partner_id = fields.Many2one("res.partner", string="Project Customer", related='project_id.partner_id')
    partner_id = fields.Many2one("res.partner", string="Customer")

    @api.onchange('project_id', 'project_id.hand_partner_id')
    def _onchange_partner_id(self):
        for rec in self:
            if rec.project_id:
                rec.partner_id = rec.project_id.partner_id.id

    def fitch_document(self):
        for rec in self:
            documents_map = []
            if rec.partner_id and rec.document_id:
                documents = self.env['documents.document'].sudo().search([
                    ('partner_id', '=', rec.partner_id.id),
                    ('type_id', '=', rec.document_id.id),
                    # ('issue_date', '=', rec.issue_date)
                ],limit=1)

                rec.document = documents.datas
                rec.name = documents.name
                rec.issue_date = documents.issue_date

    def _message_log(self, body='',
                     subject=False,
                     message_type='notification', **kwargs):
        self.task_id._message_log(
            body=f"{self.name} : \n{body}",
            subject=subject, message_type=message_type,
            **kwargs
        )
    #
    def write(self, vals):
        res = super(TaskRequiredLines, self).write(vals)
        if 'attachment_ids' in vals and not self.env.context.get('avoid_recursion'):
            # Use context flag to prevent recursion
            ctx = dict(self.env.context, avoid_recursion=True)

            # Search for related tasks
            all_related_tasks = self.env['project.task'].sudo().search([
                ('partner_id', '=', self.task_id.partner_id.id),
                ('name', '=', self.task_id.name),
                ('project_id', '=', self.task_id.project_id.id)
            ])
            if not all_related_tasks:
                print('No related tasks found.')

            for task in all_related_tasks:
                # Print details to debug
                print(f'Processing task: {task.name}')
                for line in task.document_required_type_ids:
                    if line.document_id.id == self.document_id.id:
                        # Debugging information
                        print(f'Updating line: {line.name}')

                        # Update the line
                        line.with_context(ctx).write({
                            'attachment_ids': [(6, 0, self.attachment_ids.ids)],
                            'issue_date': self.issue_date,
                            'is_required_expiration': self.is_required_expiration,
                            'expiration_date': self.expiration_date,
                        })
                    else:
                        print(f'Skipping line: {line.name}')
        return res

    @api.model
    def create(self, values):
        res = super(TaskRequiredLines, self).create(values)
        for rec in res:
            if 'task_id' in values:
                # Fetch the task using the task_id
                task = self.env['project.task'].browse(values['task_id'])

                # Check if the task name is 'Processing'
                if task.name == 'Processing':
                    rec.task_id._message_log(
                        body=" (" + str(rec.document_id.name) + ') By: ' + str(rec.create_uid.name),
                        subject=_('New Document Added'),
                        message_type='comment',
                    )

                    # Fetch the 'Collecting Required Documents' task
                    collecting_task = rec.task_id.project_id.task_ids.filtered(
                        lambda t: t.name == 'Collecting Required Documents')
                    print('Values: ', values)
                    print('Collecting Task: ', collecting_task)

                    if collecting_task:
                        # Check if a record with the same document_id, name, and issue_date already exists
                        existing_record = collecting_task.document_required_type_ids.filtered(lambda r:
                                                                                              r.document_id == rec.document_id and
                                                                                              r.name == f"{rec.document_id.name} - {rec.partner_id.name}" and
                                                                                              r.issue_date == rec.issue_date
                                                                                              )

                        if not existing_record:
                            # Prepare the values for the new record
                            vals = {
                                'document_id': rec.document_id.id,
                                'name': f"{rec.document_id.name} - {rec.partner_id.name}",
                                'is_required': rec.is_required,
                                'task_id': collecting_task.id,
                                'attachment_ids': [(6, 0, rec.attachment_ids.ids)] if rec.attachment_ids else [],
                                'issue_date': rec.issue_date or False,
                                'expiration_date': rec.expiration_date or False,
                            }
                            # Create the new record in the document_required_type_processing_ids field
                            collecting_task.document_required_type_ids.create(
                                vals)  # Replace with the correct model name
        return res


    #
    #@api.model
    # def create(self, values):
    #     res = super(TaskRequiredLines, self).create(values)
    #     for rec in res:
    #         if 'document_id' in values:
    #             rec.task_id._message_log(
    #                 body=" ( " + str(rec.document_id.name) + ' By : ' + str(
    #                     rec.create_uid.name),
    #                 subject=_('Document Type'), message_type='comment',
    #             )
    #         if 'name' in values:
    #             rec.task_id._message_log(
    #                 body=" ( " + str(rec.name) + ' By : ' + str(rec.create_uid.name),
    #                 subject=_('Name'), message_type='comment',
    #             )
    #         if 'attachment_ids' in values:
    #             current_attachment_names = ", ".join(attachment.name for attachment in rec.attachment_ids)
    #             rec.task_id._message_log(
    #                 body=" ( " + current_attachment_names + ' By : ' + str(rec.create_uid.name),
    #                 subject=_('Attachments'), message_type='comment',
    #             )
    #     return res

    # @api.constrains('attachment_ids')
    # def check_attachment(self):
    #     for rec in self:
    #         if len(rec.attachment_ids) > 1 :
    #             raise ValidationError('You cannot add more than one document')


    @api.depends('task_id', 'document_id')
    def get_document_source(self):
        for rec in self:
            rec.source_document_id = self.env['res.partner.document'].sudo().search([('task_id', '=', rec.task_id.id),
                                                                       ('type_id', '=', rec.document_id.id),
                                                                       ('name', '=', rec.name),
                                                                       ('issue_date', '=', rec.issue_date)],limit=1).id or False

    @api.depends('task_id','document_id','name','issue_date')
    def check_is_verify(self):
        for rec in self:
            document = self.env['res.partner.document'].sudo().search([('task_id','=', rec.task_id.id),
                                                                       ('type_id','=', rec.document_id.id),
                                                                       ('name','=', rec.name),('is_verify','=', True),
                                                                       ('issue_date','=', rec.issue_date)])
            if document:
                rec.is_verify = True
            else:
                rec.is_verify = False

    def check_line_is_ready(self):
        for rec in self:
            if rec.attachment_ids and rec.document_id and rec.name and rec.issue_date:
                rec.is_ready = True
            else:
                rec.is_ready = False

    def unlink(self):
        for rec in self:
            if rec.task_id and rec.is_required:
                rec.task_id._message_log(
                    body=" ( " + str(rec.document_id.name) + ' By : ' + str(
                        rec.write_uid.name),
                    subject=_('Document Deleted'), message_type='comment',
                )
            if rec.project_id and rec.is_required:
                rec.project_id._message_log(
                    body=" ( " + str(rec.document_id.name) + ' By : ' + str(
                        rec.write_uid.name),
                    subject=_('Document Deleted'), message_type='comment',
                )
        return super(TaskRequiredLines, self).unlink()


    # def unlink(self):
    #     for rec in self:
    #         if rec.is_required == True and rec.task_id.name in ['Documents To Be Collected','Collecting Required Documents']:
    #             raise ValidationError('You Can Not Delete Required Line')
    #     return super(TaskRequiredLines, self).unlink()

class Document(models.Model):
    _inherit = 'res.partner.document'

    task_id = fields.Many2one('project.task')
    task_ids = fields.Many2many('project.task')
    project_id = fields.Many2one('project.project', related='task_id.project_id')
    is_task_moved = fields.Boolean(compute='check_stage')

    def check_stage(self):
        for rec in self:
            if rec.task_id.stage_id == 64:
                rec.is_task_moved = False
            else:
                rec.is_task_moved = True

    def move_task_stage(self):
        for rec in self:
            all_documents = self.env['res.partner.document'].sudo().search([('task_id', '=', rec.task_id.id)])
            for line in all_documents:
                if line.is_verify == False:
                    raise ValidationError(' Still exist document not verify !!! ')
                else:
                    rec.task_id.stage_id = 66
