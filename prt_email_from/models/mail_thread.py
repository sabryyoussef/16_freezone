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

from odoo import models, tools


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _notify_get_reply_to_formatted_email(self, record_email, record_name):
        company = self.env["res.company"].get_active_company()
        if not company.add_sender_reply_to:
            return super(MailThread, self)._notify_get_reply_to_formatted_email(
                record_email, record_name
            )
        company_name = [self.env.user.name, company.name]
        if company.email_joint:
            company_name.insert(1, company.email_joint)
        name = " ".join((" ".join(company_name), record_name)).rstrip()
        return tools.formataddr((name, record_email))
