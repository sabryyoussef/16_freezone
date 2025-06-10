# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, Command
from datetime import date,datetime
from odoo.exceptions import ValidationError
import base64


class SalaryCertificate(models.Model):
	_name = "salary.certificate.master"

	state = fields.Selection(string="", selection=[('draft', 'Draft'),
												   ('submitted', 'Submitted For Signature'),
												   ('approved', 'Approved'),('declined', 'Declined'),
												   ('cancelled', 'Cancelled'), ], default='draft')
	name = fields.Char(string="Name")
	employee_id = fields.Many2one("hr.employee", default=lambda self: self.env.user.employee_id.id ,string="Employee")
	date_of_joining = fields.Date(string="Date of Joining")
	salary = fields.Float(string="Salary")
	purpose_of_certificate = fields.Char(string="Purpose of Certificate")
	director_id = fields.Many2one("hr.employee",string="Managing Director")
	currency_id = fields.Many2one("res.currency",string="Currency",default=lambda x:x.env.company.currency_id)
	issued_date =  fields.Date(string="Issued Date",default=lambda x: datetime.now().date())
	company_id = fields.Many2one("res.company",default=lambda x:x.env.company.id,string="Company")
	request_id = fields.Char(
		string='Number', required=True, copy=False, readonly=True,
		index=True, default=lambda self: _('New'), track_visibility='onchange')
	type = fields.Selection(string="Request Type", selection=[('generic', 'Generic'), ('specific', 'Specific'), ],default='generic')
	certificate_id = fields.Many2one('certificate.name', string='Certificate Name')
	related_report_ids = fields.Many2many("ir.actions.report", relation="related1", column1="related2",
										  column2="related3", related='certificate_id.report_ids')
	report_ids = fields.Many2many('ir.actions.report', domain="[('id','in', related_report_ids)]", string='Templates')
	partner_id = fields.Many2one('res.partner', string='Contact')
	date_issue = fields.Date("Date of Issue",default=fields.Date.context_today)
	attachment_ids = fields.Many2many('ir.attachment',string='Attachment', copy=False)
	sign_request_ids = fields.One2many('sign.request','salary_certificate_id')
	travel_start = fields.Date('Travel Start')
	travel_end= fields.Date('Travel End')

	def action_view_sign_request(self):
		""" Smart button to run action """
		recs = self.mapped('sign_request_ids')
		signed_recs = recs.filtered(lambda r: r.state == 'signed')
		action = self.env.ref('sign.sign_request_action').read()[0]

		if len(signed_recs) > 1:
			action['domain'] = [('id', 'in', signed_recs.ids)]
		elif len(signed_recs) == 1:
			action['views'] = [(
				self.env.ref('sign.sign_request_view_form').id, 'form'
			)]
			action['res_id'] = signed_recs.id
		else:
			action = {'type': 'ir.actions.act_window_close'}

		return action

	def generate_pdf(self):
		if self.certificate_id and self.report_ids:
			lst = []
			for report in self.report_ids:
				report_name = report.report_name  # This is a string like 'module_name.template_name'
				lst.append(report_name)
				for record in self:
					# Generate PDF using the correct report_name string
					pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(report_name, record.ids)

					# Create the attachment
					attachment = self.env['ir.attachment'].create({
						'name': '%s - %s.pdf' % (report.name,record.name),
						'type': 'binary',
						'datas': base64.b64encode(pdf_content),
						'res_model': record._name,
						'res_id': record.id,
						'mimetype': 'application/pdf',
					})

					# Save the attachment to the field
					record.attachment_ids = [(4, attachment.id)]
					# Return the original report action (for download/view)
					# return report.report_action(self)


	@api.model
	def create(self, vals):
		vals['request_id'] = self.env['ir.sequence'].next_by_code('salary.certificate.master') or _('New')
		return super(SalaryCertificate, self).create(vals)

	def action_draft(self):
		for rec in self:
			rec.write({'state':'draft'})

	def action_approve(self):
		for rec in self:
			rec.write({'state':'approved'})

	def action_declined(self):
		for rec in self:
			rec.write({'state':'declined'})

	def action_cancel(self):
		sign_requests = self.mapped('sign_request_ids')
		sign_requests.sudo().unlink()
		self.write({'state': 'cancelled'})

	# def action_request_signature(self):
	# 	self.generate_pdf()
	# 	for attachment in self.attachment_ids:
	# 		if not self.director_id.address_home_id:
	# 			raise ValidationError('Kindly ensure the related partner is added to the employee screen')
	# 		template_id = self.env['sign.template'].create({
	# 			'salary_certificate_id': self.id,
	# 			'attachment_id': attachment.id,
	# 			'name': attachment.name,
	# 			'authorized_ids': [self.director_id.user_id.id],
	# 			'user_id': self.director_id.user_id.id,
	# 			'folder_id': 12,
	# 		})
	# 		signers = [{
	# 			'partner_id': self.director_id.address_home_id.id,
	# 			'role_id': self.env.ref('sign.sign_item_role_default').id,
	# 		}]
	# 		reference = attachment.name
	# 		attachment_ids = attachment
	#
	# 		# sign_request = self.env['sign.request'].create({
	# 		# 	'salary_certificate_id': self.id,
	# 		# 	'template_id': template_id.id,  # FIXED HERE
	# 		# 	'request_item_ids': [Command.create({
	# 		# 		'partner_id': signer['partner_id'],
	# 		# 		'role_id': signer['role_id'],
	# 		# 	}) for signer in signers],
	# 		# 	'reference': reference,
	# 		# 	'refusal_allowed': True,
	# 		# 	'subject': 'subject',
	# 		# 	'message': 'message',
	# 		# 	'message_cc': 'message_cc',
	# 		# 	'attachment_ids': [Command.set(attachment_ids.ids)],
	# 		# })
	# 		#
	# 		# sign_request.message_subscribe(partner_ids=self.director_id.address_home_id.ids)
	# 		self.state = 'submitted'
	# 		# return {
	# 		# 	'type': 'ir.actions.act_window',
	# 		# 	'name': 'Signature Request',
	# 		# 	'res_model': 'sign.request',
	# 		# 	'view_mode': 'kanban',
	# 		# 	'res_id': sign_request.id,
	# 		# 	'target': 'current',
	# 		# 	'domain': [('id', '=', sign_request.id)],
	# 		# }

	def action_request_signature(self):
		self.generate_pdf()
		for attachment in self.attachment_ids:
			if not self.director_id.address_home_id:
				raise ValidationError('Kindly ensure the related partner is added to the employee screen')
			template_id = self.env['sign.template'].create({
				'salary_certificate_id': self.id,
				'attachment_id': attachment.id,
				'name': attachment.name,
				'authorized_ids': [self.director_id.user_id.id],
				'user_id': self.director_id.user_id.id,
				'folder_id': 12,
			})
			print('sevooo 11111 ===== ', template_id)

			# Create an instance of SignSendRequest
			sign_send_request = self.env['sign.send.request'].create({
				'template_id': template_id.id,  # Replace with your actual template ID
				'attachment_ids': [(4, attachment.id)],  # Add attachments
				'subject': _("Signature Request - %s") % (attachment.name),
				'filename': attachment.name,
				'message': "PLease sign the document",
				'signer_id' : self.director_id.address_home_id.id
			})

			print('sevooo 222222 ===== ', sign_send_request)

			# Call the send_request method directly
			sign_send_request.send_request()
			self.state = 'submitted'

	@api.onchange("employee_id",'salary')
	def onchange_salary(self):
		for rec in self:
			if rec.salary and rec.salary < 0:
				raise ValidationError(_("Salary shouldn't be negative!"))
			wage = rec.employee_id.contract_id.wage
			rec.salary = wage
			rec.date_of_joining = rec.employee_id.joining_date