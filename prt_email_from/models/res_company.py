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

from odoo import _, api, fields, models
from odoo.http import request


class ResCompany(models.Model):
    _inherit = "res.company"

    use_company_email = fields.Boolean(
        help="Before: From 'Some User <some.user@usermail.com>'\n"
        "After: From 'Some User <mycompany@companymail.com>'",
    )
    add_company_from = fields.Boolean(
        string="Company Name In 'From'",
        help="Before: 'Some User <mycompany@example.com>'\n"
        "After: Some User via My Company <mycompany@example.com>",
    )
    add_company_mode = fields.Selection(
        selection=[("a", "append to username"), ("r", "replace completely")],
        default="a",
    )
    add_sender_reply_to = fields.Boolean(
        string="Sender's Name In 'Reply-to'",
        help="Before: 'My Company <mycompany@example.com>'\n"
        "After: Some User via My Company <mycompany@example.com>",
    )
    email_joint = fields.Char(
        string="Name Joint",
        translate=True,
        default="via",
        help="Before: 'Some User My Company <mycompany@example.com>'\n"
        "After: Some User via My Company <mycompany@example.com>",
    )

    @api.constrains("add_company_from")
    def _check_access_to_option(self):
        inactive_use_company_email = all(self.mapped("use_company_email"))
        active_add_company_from = any(self.mapped("add_company_from"))
        if not inactive_use_company_email and active_add_company_from:
            raise models.AccessError(
                _(
                    "You can't activate this option without active 'Use Company Email' option."
                )
            )

    @api.model
    def get_active_company(self):
        """Get active company from request"""
        if self.env.user.has_group("base.group_multi_company"):
            cids = request.httprequest.cookies.get("cids", str(self.env.company.id))
            try:
                company_id = int(cids.split(",")[0])
                company = self.browse(company_id)
            except ValueError:
                company = self.env.company
        else:
            company = self.env.company
        return company
