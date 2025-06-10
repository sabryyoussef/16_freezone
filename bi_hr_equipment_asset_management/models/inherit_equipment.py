# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _

class Equipmentmaintenence(models.Model):
	_inherit = "maintenance.equipment"
	_description = "maintenance equipment"

	image_1920 = fields.Image("Image")
	equipment_code = fields.Char(string='Equipment Code',copy=False,readonly=False)
	assign_date = fields.Datetime('Assigned Date', tracking=True)
	state = fields.Selection([
		('draft', 'Draft'),
		('occupied', 'Occupied'),
		('free to use', 'Free to Use'),
		('scrap', 'Scrap'),
	], string='State', default='draft',readonly=False,tracking=True)
	components_ids = fields.One2many(
		comodel_name='equipment.components',
		inverse_name='components_id',
		string="components",
		copy=True, auto_join=True)
	history_ids = fields.One2many('equipment.history', 'components_id', string='User History')


	def _create_equipment_sequence(self):
		company_id = self.env.company.id
		seq = self.env['ir.sequence'].search([('code', '=', 'maintenance.equipment'), ('company_id', '=', company_id)], limit=1)
		if not seq:
			seq = self.env['ir.sequence'].create({
			'name': 'maintanance Equipment Sequence %s' % company_id,
			'code': 'maintenance.equipment',
			'prefix': 'ME%s' % company_id,
			'padding': 5,
			'company_id': company_id,
			})
		return seq


	@api.model_create_multi
	def create(self, vals):        
		res = super(Equipmentmaintenence, self).create(vals)
		res.update_components_employee()
		if self.env.user.has_group('bi_hr_equipment_asset_management.group_automatic_generate_asset_code'):
			seq = self._create_equipment_sequence()
			res.write({'equipment_code': seq.next_by_id()})
		if res.employee_id and res.assign_date:
			res.write({'state':'occupied'})
			self.env['equipment.history'].create({
				'components_id': res.id,
				'employee_id': res.employee_id.id,
				'assigned_date': res.assign_date,
			})

		return res


	def update_components_employee(self):
		for component in self.components_ids:
			if component.employee_id != self.employee_id:
				component.employee_id = self.employee_id
			if component.component_id and component.component_id.employee_id != self.employee_id:
				component.component_id.employee_id = self.employee_id


	def write(self, vals):
		for record in self:
			previous_employee = record.employee_id
			previous_employee_end_date = fields.Datetime.now()
			res = super(Equipmentmaintenence, record).write(vals)
			self.update_components_employee()
			if self.employee_id and self.assign_date:
				super(Equipmentmaintenence, record).write({'state':'occupied'})
			if record.env.user.has_group('bi_hr_equipment_asset_management.group_automatic_generate_asset_code'):
				seq = self._create_equipment_sequence()
				if not self.equipment_code:
					super(Equipmentmaintenence, record).write({'equipment_code': seq.next_by_id()})
			if 'employee_id' in vals and previous_employee:
				self.env['equipment.history'].search([
					('components_id', '=', record.id),
					('employee_id', '=', previous_employee.id),
					('end_date', '=', False)
				]).write({'end_date': previous_employee_end_date})	

			if vals.get('employee_id') and vals.get('employee_id') != False:
				self.env['equipment.history'].create({
					'components_id': record.id,
					'employee_id': vals['employee_id'],
					'assigned_date': record.assign_date,
				})
		return res