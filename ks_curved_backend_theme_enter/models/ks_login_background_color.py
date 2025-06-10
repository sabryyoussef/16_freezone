# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class KsLoginBackgroundColor(models.Model):
    _name = 'ks.login.background.color'
    _description = 'Arc Theme Login Background Color'

    ks_color = fields.Char(string="Color")
    ks_active = fields.Boolean(string="Background selected")
