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

from odoo import tools
from odoo.tests import TransactionCase


class TestEmailFromCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestEmailFromCommon, cls).setUpClass()
        cls.res_partner_1 = cls.env.ref("base.res_partner_1")
        cls.main_company = cls.env.ref("base.main_company")
        cls.username = cls.env.user.name
        cls.user_demo = cls.env.ref("base.user_demo")
        cls.test_example_email = "test@example.com"
        cls.mail_message_vals = {
            "model": "res.partner",
            "res_id": cls.res_partner_1.id,
            "subject": "Test Mail Message #1",
            "message_type": "email",
            "subtype_id": cls.env.ref("mail.mt_comment").id,
            "author_id": cls.user_demo.partner_id.id,
            "message_id": "<123456-openerp-%s-mail.test.gateway@%s>"
            % (cls.res_partner_1.id, "localhost"),
        }

    def _get_formatted_email(self):
        """Get prepared formatted email"""
        return (
            self.env["mail.thread"]
            .with_company(self.main_company)
            ._notify_get_reply_to_formatted_email(
                self.main_company.email, self.res_partner_1.name
            )
        )

    def _get_expected_value(self, *args):
        """Get expected value"""
        return tools.formataddr((" ".join(args), self.main_company.email))
