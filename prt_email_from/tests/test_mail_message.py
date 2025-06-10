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

from odoo.tests import tagged
from odoo.tools import formataddr

from odoo.addons.website.tools import MockRequest

from .common import TestEmailFromCommon


@tagged("post_install", "-at_install")
class TestMailMessage(TestEmailFromCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.mail_message_obj = cls.env["mail.message"].with_user(cls.user_demo)
        cls.company = cls.user_demo.company_id
        cls.company.write({"use_company_email": True})
        cls.demo_partner = cls.user_demo.partner_id
        cls.test_user_demo_email = formataddr(
            (cls.demo_partner.name, cls.demo_partner.email)
        )

    def test_get_default_from_default(self):
        """Test flow when company settings are disabled"""
        self.company.write({"use_company_email": False})
        with MockRequest(self.env):
            formatted_email = self.mail_message_obj._prepare_default_email_from(
                self.user_demo, self.test_example_email
            )
            self.assertEqual(self.test_example_email, formatted_email)

    def test_get_default_from_with_use_company_email(self):
        """Test flow when 'use_company_email' mode is activated"""
        with MockRequest(self.env):
            formatted_email = self.mail_message_obj._prepare_default_email_from(
                self.user_demo, self.test_user_demo_email
            )
            expected_email = formataddr((self.demo_partner.name, self.company.email))
            self.assertEqual(formatted_email, expected_email)

    def test_get_default_from_with_use_company_email_and_context(self):
        """
        Test flow when 'use_company_email' mode is activated
        and have context 'force_email_from' key
        """
        test_email = "res_partner_email@exmaple.com"
        with MockRequest(self.env):
            formatted_email = self.mail_message_obj.with_context(
                force_email_from=test_email
            )._prepare_default_email_from(self.user_demo, self.test_user_demo_email)
            expected_email = formataddr((self.demo_partner.name, test_email))
            self.assertEqual(formatted_email, expected_email)

    def test_get_default_from_with_replace_completely_and_company_from(self):
        """Test flow when both 'add_company_from' and 'replace' mode are activated"""
        self.company.write({"add_company_mode": "r", "add_company_from": True})
        with MockRequest(self.env):
            formatted_email = self.mail_message_obj._prepare_default_email_from(
                self.user_demo, self.test_example_email
            )
            self.assertEqual(self.company.email_formatted, formatted_email)

    def test_get_default_from_with_company_from(self):
        """Test flow when 'add_company_from' is activated"""
        self.company.write({"add_company_from": True})
        with MockRequest(self.env):
            formatted_email = self.mail_message_obj._prepare_default_email_from(
                self.user_demo, self.test_example_email
            )
            name = (
                f"{self.user_demo.name} {self.company.email_joint} {self.company.name}"
            )
            expected_value = formataddr((name, self.company.email))
            self.assertEqual(formatted_email, expected_value)

    def test_get_default_from_with_company_from_and_empty_joint(self):
        """Test flow when 'add_company_from' is activated and 'email_joint' is empty"""
        self.company.write(
            {
                "add_company_from": True,
                "email_joint": False,
            }
        )
        with MockRequest(self.env):
            formatted_email = self.mail_message_obj._prepare_default_email_from(
                self.user_demo, self.test_example_email
            )
            name = f"{self.user_demo.name} {self.company.name}"
            expected_value = formataddr((name, self.company.email))
            self.assertEqual(formatted_email, expected_value)

    def test_mail_message_default_create(self):
        """Test default message creation flow"""
        message = self.env["mail.message"].create([self.mail_message_vals])
        self.assertEqual(message.email_from, self.user_demo.email_formatted)

    def test_mail_message_create_without_author(self):
        """Test flow for message without author"""
        self.mail_message_vals.update(author_id=False)
        message = self.env["mail.message"].create([self.mail_message_vals])
        self.assertEqual(message.email_from, self.user_demo.email_formatted)

    def test_mail_message_create_user_without_group(self):
        """Test flow for user without any groups"""
        self.user_demo.write({"groups_id": [(6, 0, [])]})
        message = self.env["mail.message"].create([self.mail_message_vals])
        self.assertEqual(message.email_from, self.user_demo.email_formatted)
