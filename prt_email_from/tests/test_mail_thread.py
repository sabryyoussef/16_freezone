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

from .common import TestEmailFromCommon


@tagged("post_install", "-at_install")
class TestMailThread(TestEmailFromCommon):
    def test_default_formatted_email_behavior(self):
        """Test flow when company settings are disabled"""
        formatted_email = self._get_formatted_email()
        expected_value = self._get_expected_value(
            self.main_company.name, self.res_partner_1.name
        )
        self.assertEqual(formatted_email, expected_value)

    def test_notify_formatted_email_with_sender_reply_to(self):
        """
        Test email creation for the company
        with 'add_sender_reply_to' enabled and empty 'email_joint'
        """
        self.main_company.write({"add_sender_reply_to": True, "email_joint": False})
        formatted_email = self._get_formatted_email()
        expected_value = self._get_expected_value(
            self.username, self.main_company.name, self.res_partner_1.name
        )
        self.assertEqual(formatted_email, expected_value)

    def test_notify_formatted_email_with_sender_and_joint(self):
        """
        Test email creation for the company
        with 'add_sender_reply_to' activated
        and default value in the 'email_joint' field.
        """
        self.main_company.add_sender_reply_to = True
        formatted_email = self._get_formatted_email()
        expected_value = self._get_expected_value(
            self.username,
            self.main_company.email_joint,
            self.main_company.name,
            self.res_partner_1.name,
        )
        self.assertEqual(formatted_email, expected_value)
