###################################################################################
#
#    Copyright (C) 2020 Cetmix OÜ
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################

from odoo import api, models, tools


class MailMessage(models.Model):
    _inherit = "mail.message"

    @api.model
    def _prepare_default_email_from(self, user, email_from):
        """
        Preparing formatted mail for company
        Make 'From:' look like 'John Smith via Your Company <yorcompany@example.com>
        :param user: author's user record
        :param email_from: messages "email_from" key value
        :return: formatted email address or email_from
        """
        if user == self.env.user:
            company = self.env["res.company"].get_active_company()
        else:
            company = user.company_id
        if not company.use_company_email:
            return email_from

        user_name = user.name

        # Setting force email_from value by key in context
        email_from = self._context.get("force_email_from", company.email)

        # If not using company email returned "email_from" value
        if not company.add_company_from:
            return tools.formataddr((user_name, email_from))

        if company.add_company_mode == "r":
            return tools.formataddr((company.name, email_from))
        if company.email_joint:
            return tools.formataddr(
                (f"{user_name} {company.email_joint} {company.name}", email_from)
            )
        return tools.formataddr((f"{user_name} {company.name}", email_from))

    @api.model_create_multi
    def create(self, vals_list):
        # Proceed only if Author is an internal user
        if self._context.get("email_from_skip_create"):
            return super(MailMessage, self).create(vals_list)
        res_users_obj = self.env["res.users"]
        for vals in filter(lambda v: v.get("author_id"), vals_list):
            user = res_users_obj.search(
                [("partner_id", "=", vals.get("author_id"))], limit=1
            )
            if user and user.has_group("base.group_user"):
                email_from = vals.get("email_from", False)
                vals.update(
                    email_from=self._prepare_default_email_from(user, email_from)
                )
        return super(MailMessage, self).create(vals_list)
