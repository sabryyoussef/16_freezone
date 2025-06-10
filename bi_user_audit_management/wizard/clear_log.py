# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class ClearLog(models.TransientModel):
	_name = 'clear.log'
	_description = 'Clear Log'

	name = fields.Char()
	all_log = fields.Boolean('All log')
	to_date = fields.Date('To Date')

	read_log = fields.Boolean('Read')
	write_log = fields.Boolean('Write')
	create_log = fields.Boolean('Create')
	delete_log = fields.Boolean('Delete')

	model_ids = fields.Many2many('ir.model')

	def log_delete(self):
		if self.all_log:
			search = self.env['user.audit.log'].sudo().search([])
			search.sudo().unlink()
		for log in self.model_ids:
			search = self.env['user.audit.log'].sudo().search([('model_id','=',log.id)])
			for search in search:
				if self.create_log:
					if search.log_type == 'Create':
						search.sudo().unlink()
				if self.read_log:
					if search.log_type == 'Read':
						search.sudo().unlink()
				if self.write_log:
					if search.log_type == 'Write':
						search.sudo().unlink()
				if self.delete_log:
					if search.log_type == 'Delete':
						search.sudo().unlink()
		