# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _


class EquipmentComponents(models.Model):
    _name = 'equipment.components'
    _description = 'Equipment Components'



    name = fields.Char(string="name")
    components_id = fields.Many2one('maintenance.equipment', string='Equipment ',default=False)
    component_id = fields.Many2one('maintenance.equipment', string='Equipment',default=False)
    employee_id = fields.Many2one('hr.employee', string='Employee',default=False)  



    @api.onchange('components_id')
    def _onchange_employee_id(self):
        for j in self:
            j.employee_id = j.components_id.employee_id

    @api.model_create_multi
    def create(self, vals_list):
        records = super(EquipmentComponents, self).create(vals_list)
        for record in records:
            if record.components_id and record.components_id.assign_date:
                record.component_id.assign_date = record.components_id.assign_date

            if record.component_id:
                record.components_id.message_post(body=_("%s Component added") % record.component_id.name)
        return records

    def write(self, vals):
        res = super(EquipmentComponents, self).write(vals)
        for record in self:
            if record.components_id and record.components_id.assign_date:
                record.component_id.assign_date = record.components_id.assign_date
        return res 


    def unlink(self):
        for component in self:
            if component.component_id:
                component.component_id.write({'state': 'free to use','employee_id':False,'assign_date':False})
                component.components_id.message_post(body=_("%s Component removed") % component.component_id.name)
        res = super(EquipmentComponents, self).unlink()
        return res

class EquipmentHistory(models.Model):
    _name = 'equipment.history'
    _description = 'Equipment Usage History'

    components_id = fields.Many2one('maintenance.equipment',string='components')
    assigned_date = fields.Datetime(string='Assigned Date')
    end_date = fields.Datetime(string='End Date')
    employee_id = fields.Many2one('hr.employee', string='Employee')



