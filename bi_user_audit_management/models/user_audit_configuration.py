# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class AuditConfiguration(models.Model):
	_name = 'user.audit.configuration'
	_description = 'User Audit Configuration'

	def read(self, fields=None, load='_classic_read'):
		return super(AuditConfiguration, self).read(fields=fields, load=load)

	name = fields.Char("Name")

	read_log = fields.Boolean('Read')
	write_log = fields.Boolean('Write')
	create_log = fields.Boolean('Create')
	delete_log = fields.Boolean('Delete')

	all_users = fields.Boolean("All Users")
	user_ids = fields.Many2many('res.users')

	model_ids = fields.Many2many('ir.model')
	field_ids = fields.Many2many('ir.model.fields', string="Fields", domain="[('model_id', 'in', model_ids)]")

