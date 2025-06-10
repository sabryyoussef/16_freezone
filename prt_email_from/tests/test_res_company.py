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

from odoo.exceptions import AccessError
from odoo.tests import tagged

from .common import TestEmailFromCommon


@tagged("post_install", "-at_install")
class TestResCompany(TestEmailFromCommon):
    @classmethod
    def setUpClass(cls):
        super(cls, TestResCompany).setUpClass()
        cls.company = cls.user_demo.company_id

    def test_access_to_option_email_from(self):
        """Test flow for check access to set 'add_company_from' option"""
        with self.assertRaises(AccessError):
            self.company.write({"add_company_from": True})
