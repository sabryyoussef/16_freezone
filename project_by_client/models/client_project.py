# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ClientProjects(models.Model):
    _inherit = 'res.partner'

    project_ids = fields.One2many(comodel_name='project.project', inverse_name='partner_id')
    project_count = fields.Integer(compute='_compute_project_count', store=True)

    @api.depends('project_ids')
    def _compute_project_count(self):
        for rec in self:
            rec.project_count = rec.project_ids.search_count([('partner_id', '=', rec.id)])

    def view_client_projects(self):
        kanban_view = self.env.ref('project.view_project_kanban')
        tree_view = self.env.ref('project.view_project')
        action = {
            'type': 'ir.actions.act_window',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
            'view_mode': 'kanban,tree,form',
            'name': f'{self.name}\'s Projects',
            'view_ids': [(kanban_view, 'kanban'), (tree_view, 'tree'), (False, 'form')],
            'res_model': 'project.project',
        }
        return action
