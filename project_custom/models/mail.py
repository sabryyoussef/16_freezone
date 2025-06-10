# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import ast
import base64
import datetime
import dateutil
import email
import email.policy
import hashlib
import hmac
import json
import lxml
import logging
import pytz
import re
import time
import threading

from collections import namedtuple
from email.message import EmailMessage
from email import message_from_string
from lxml import etree
from werkzeug import urls
from xmlrpc import client as xmlrpclib
from markupsafe import Markup

from odoo import _, api, exceptions, fields, models, tools, registry, SUPERUSER_ID, Command
from odoo.exceptions import MissingError, AccessError
from odoo.osv import expression
from odoo.tools import is_html_empty
from odoo.tools.misc import clean_context, split_every

_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def _notify_get_recipients_groups(self, msg_vals=None):
        """ Return groups used to classify recipients of a notification email,
        including additional portal customer handling."""
        if not self:
            return []

        is_thread_notification = self._notify_get_recipients_thread_info(msg_vals=msg_vals)['is_thread_notification']
        portal_enabled = isinstance(self, self.env.registry['portal.mixin'])
        partner_data = self._mail_get_partners().get(self.id, [])
        customer = partner_data[0] if partner_data else None

        groups = [
            ['user', lambda pdata: pdata['type'] == 'user', {'has_button_access': is_thread_notification}],
            ['portal', lambda pdata: pdata['type'] == 'portal',
             {'active': portal_enabled, 'has_button_access': portal_enabled}],
            ['follower', lambda pdata: pdata['is_follower'], {'active': False, 'has_button_access': False}],
            ['customer', lambda pdata: True, {'has_button_access': False}]
        ]

        if portal_enabled and customer:
            access_token = self._portal_ensure_token()
            local_msg_vals = dict(msg_vals or {}, access_token=access_token, pid=customer.id,
                                  hash=self._sign_token(customer.id))
            local_msg_vals.update(customer.signup_get_auth_param().get(customer.id, {}))
            access_link = self._notify_get_action_link('view', **local_msg_vals)

            groups.insert(0, ['portal_customer', lambda pdata: pdata['id'] == customer.id, {
                'has_button_access': True,
                'button_access': {'url': access_link},
                'notification_is_customer': True
            }])

        return groups


