# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date



class UserAuditLog(models.Model):
	_name = 'user.audit.log'
	_description = 'User Audit Logs'

	name = fields.Char('Reference')
	model_id = fields.Many2one('ir.model', 'Object')
	record_id = fields.Char('Record ID')
	log_type = fields.Char('Type')
	user_id = fields.Many2one('res.users', 'User')
	date = fields.Date(required=True, default=lambda self: fields.Date.context_today(self))
	updated_id = fields.Many2one('ir.model.fields', string="Updated_Field")
	updated_value = fields.Char('Updated Value')
	old_value = fields.Char('Old Value')

	@api.model_create_multi
	def create(self, vals_list):
		for values in vals_list:
			if 'name' not in values:
				if self.env.company:
					sequence_code = f'user.audit.log.{self.env.company.id}'
					self._generate_company_sequences()
					values['name'] = self.env['ir.sequence'].next_by_code(sequence_code) or 'New'
		return super(UserAuditLog, self).create(values)


	def _generate_company_sequences(self):
		for company in self.env.company:
			sequence_code = f'user.audit.log.{self.env.company.id}'
			sequence_exists = self.env['ir.sequence'].search([('code', '=', sequence_code)])
			if not sequence_exists:
				self.env['ir.sequence'].create({
					'name': _('Sequence for ') + self.env.company.name,
					'code': sequence_code,
					'company_id': self.env.company.id,
					'prefix': 'UA/',
					'padding': 6,
					'number_next': 1,
					'number_increment': 1
				})


