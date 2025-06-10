from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import re
from odoo.tools import html_escape
from markupsafe import Markup
from werkzeug.utils import escape
from urllib.parse import urlencode


class ResPartner(models.Model):
    _inherit = 'res.partner'

    project_product_ids = fields.Many2many('project.project.products', compute='get_project_product_ids')

    def get_project_product_ids(self):
        for rec in self:
            projects = self.env['project.project.products'].sudo().search([('partner_id', '=', rec.id)])
            rec.project_product_ids = projects

    @api.constrains('phone')
    def _check_method_name_phone(self):
        for rec in self:
            if rec.phone:
                phone_cleaned = rec.phone.replace(" ", "")
                if any(isinstance(line.phone, str) and phone_cleaned == line.phone.replace(" ", "") for line in
                       rec.parent_partner_ids):
                    return
                check_partner_child = self.env['res.partner'].search([
                    ('id', '!=', rec.id),
                    ('parent_partner_ids', '=', rec.id),
                ])
                print(" vllllll  check_partner_child  ==========  ", check_partner_child)
                if check_partner_child:
                    for child in check_partner_child.parent_partner_ids:
                        if child.phone == rec.phone:
                            return
                check_partner_parent = self.env['res.partner'].search([
                    ('id', '!=', rec.id),
                    ('parent_partner_ids', 'in', rec.parent_partner_ids.ids),
                ])
                print(" vllllll  check_partner_parent  ==========  ", check_partner_parent)
                if check_partner_parent:
                    for child in check_partner_parent.parent_partner_ids:
                        if child.phone == rec.phone:
                            return
                check_parent = self.env['res.partner'].search([
                    ('id', '!=', rec.id),
                    ('parent_partner_ids', 'in', rec.id),
                    ('phone', '=', rec.phone),
                ])
                print(" vllllll  check_parent  ==========  ", check_parent)
                if check_parent:
                    return
                for parent in rec.parent_partner_ids:
                    partner_child = self.env['res.partner'].search([
                        ('id', '!=', rec.id),
                        ('parent_partner_ids', 'in', parent.id),
                        ('phone', '=', rec.phone),
                    ])
                    print(" phone  partner_child  ==========  ", partner_child)
                    if partner_child:
                        return
                partner_count = self.env['res.partner'].search_count([
                    ('id', '!=', rec.id),
                    ('phone', '=', rec.phone),
                    ('company_id', '=', rec.company_id.id)
                ])
                print('phone  partner_count ', partner_count)
                if partner_count > 0:
                    raise ValidationError(
                        'This Phone Already Exists for another contact within the same company.')

    @api.constrains('mobile')
    def _check_method_name_mobile(self):
        for rec in self:
            if rec.mobile:
                mobile_cleaned = rec.mobile.replace(" ", "")
                if any(isinstance(line.mobile, str) and mobile_cleaned == line.mobile.replace(" ", "") for line in
                       rec.parent_partner_ids):
                    return
                check_partner_child = self.env['res.partner'].search([
                    ('id', '!=', rec.id),
                    ('parent_partner_ids', '=', rec.id),
                ])
                print(" vllllll  check_partner_child  ==========  ", check_partner_child)
                if check_partner_child:
                    for child in check_partner_child.parent_partner_ids:
                        if child.mobile == rec.mobile:
                            return
                check_partner_parent = self.env['res.partner'].search([
                    ('id', '!=', rec.id),
                    ('parent_partner_ids', 'in', rec.parent_partner_ids.ids),
                ])
                print(" vllllll  check_partner_parent  ==========  ", check_partner_parent)
                if check_partner_parent:
                    for child in check_partner_parent.parent_partner_ids:
                        if child.mobile == rec.mobile:
                            return
                check_parent = self.env['res.partner'].search([
                    ('id', '!=', rec.id),
                    ('parent_partner_ids', 'in', rec.id),
                    ('mobile', '=', rec.mobile),
                ])
                print(" vllllll  check_parent  ==========  ", check_parent)
                if check_parent:
                    return
                for parent in rec.parent_partner_ids:
                    partner_child = self.env['res.partner'].search([
                        ('id', '!=', rec.id),
                        ('parent_partner_ids', 'in', parent.id),
                        ('mobile', '=', rec.mobile),
                    ])
                    print(" mobile  partner_child  ==========  ", partner_child)
                    if partner_child:
                        return
                partner_count = self.env['res.partner'].search_count([
                    ('id', '!=', rec.id),
                    ('mobile', '=', rec.mobile),
                    ('company_id', '=', rec.company_id.id)
                ])
                print('mobile  partner_count ', partner_count)
                if partner_count > 0:
                    raise ValidationError(
                        'This Mobile Already Exists for another contact within the same company.')

    @api.constrains('email')
    def _check_method_name_email(self):
        for rec in self:
            if rec.email:
                email_cleaned = rec.email.replace(" ", "")
                if any(isinstance(line.email, str) and email_cleaned == line.email.replace(" ", "") for line in
                       rec.parent_partner_ids):
                    return
                check_partner_child = self.env['res.partner'].search([
                    ('id', '!=', rec.id),
                    ('parent_partner_ids', '=', rec.id),
                ])
                print(" vllllll  check_partner_child  ==========  ", check_partner_child)
                if check_partner_child:
                    for child in check_partner_child.parent_partner_ids:
                        if child.email == rec.email:
                            return
                check_partner_parent = self.env['res.partner'].search([
                    ('id', '!=', rec.id),
                    ('parent_partner_ids', 'in', rec.parent_partner_ids.ids),
                ])
                print(" vllllll  check_partner_parent  ==========  ", check_partner_parent)
                if check_partner_parent:
                    for child in check_partner_parent.parent_partner_ids:
                        if child.email == rec.email:
                            return
                check_parent = self.env['res.partner'].search([
                    ('id', '!=', rec.id),
                    ('parent_partner_ids', 'in', rec.id),
                    ('email', '=', rec.email),
                ])
                print(" vllllll  check_parent  ==========  ", check_parent)
                if check_parent:
                    return
                for parent in rec.parent_partner_ids:
                    partner_child = self.env['res.partner'].search([
                        ('id', '!=', rec.id),
                        ('parent_partner_ids', 'in', parent.id),
                        ('email', '=', rec.email),
                    ])
                    print(" email  partner_child  ==========  ", partner_child)
                    if partner_child:
                        return
                partner_count = self.env['res.partner'].search_count([
                    ('id', '!=', rec.id),
                    ('email', '=', rec.email),
                    ('company_id', '=', rec.company_id.id)
                ])
                print('email  partner_count ', partner_count)
                partner = self.env['res.partner'].search([
                    ('id', '!=', rec.id),
                    ('email', '=', email_cleaned),
                    ('company_id', '=', rec.company_id.id)
                ], limit=1)
                if partner_count > 0:
                    if partner:
                        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                        action_id = self.env.ref('base.action_partner_form').id
                        menu_id = self.env.ref('contacts.menu_contacts').id
                        partner_url = (
                            f"{base_url}/web#id={partner.id}"
                            f"&menu_id={menu_id}"
                            f"&cids={self.env.company.id}"
                            f"&action={action_id}"
                            f"&model=res.partner&view_type=form"
                        )
                        url_params = {
                            'id': partner.id,
                            'menu_id': menu_id,
                            'cids': self.env.company.id,
                            'action': action_id,
                            'model': 'res.partner',
                            'view_type': 'form',
                        }

                        partner_url = f"{base_url}/web?{urlencode(url_params)}"

                        # Trigger a client action with a popup showing the clickable URL
                        action = {
                            'type': 'ir.actions.client',
                            'tag': 'reload',
                            'params': {
                                'message': _(
                                    'This email already exists. You can view the partner record here: ') + partner_url,
                            }
                        }

                        raise ValidationError(
                            _('This Email Already Exists for another contact within the same company.\n\n'
                              'Partner Name: %(partner_name)s\n\n'
                              'Click here to view the partner: %(partner_url)s') % {
                                'partner_name': partner.name,
                                'partner_url': partner_url
                            })

    # Create a custom JavaScript action
    def open_url_in_new_tab(self, partner_url):
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {
                'message': _('Click on the link below to view the partner record.'),
                'button': {
                    'label': _('Open Link'),
                    'action': 'window.open("' + partner_url + '", "_blank")',
                }
            }
        }

    @api.model
    def open_partner_link_action(self, partner_id):
        partner = self.env['res.partner'].browse(partner_id)
        partner_url = f"{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}/web#id={partner.id}&model=res.partner&view_type=form"
        return {
            'type': 'ir.actions.act_url',
            'url': partner_url,
            'target': 'new',
        }

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        if vals.get('parent_partner_ids'):
            self._check_method_name_email()
            self._check_method_name_phone()
            self._check_method_name_mobile()
        return res
