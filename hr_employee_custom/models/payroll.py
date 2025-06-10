

import base64
import logging
import random

from collections import defaultdict, Counter
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, Command, fields, models, _
from odoo.addons.hr_payroll.models.browsable_object import BrowsableObject, InputLine, WorkedDays, Payslips, ResultRules
from odoo.exceptions import UserError, ValidationError
from odoo.osv.expression import AND
from odoo.tools import float_round, date_utils, convert_file, html2plaintext, is_html_empty, format_amount
from odoo.tools.float_utils import float_compare
from odoo.tools.misc import format_date
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def action_payslip_done(self):
        invalid_payslips = self.filtered(lambda p: p.contract_id and (p.contract_id.date_start > p.date_to or (p.contract_id.date_end and p.contract_id.date_end < p.date_from)))
        if invalid_payslips:
            raise ValidationError(_('The following employees have a contract outside of the payslip period:\n%s', '\n'.join(invalid_payslips.mapped('employee_id.name'))))
        if any(slip.contract_id.state == 'cancel' for slip in self):
            raise ValidationError(_('You cannot validate a payslip on which the contract is cancelled'))
        if any(slip.state == 'cancel' for slip in self):
            raise ValidationError(_("You can't validate a cancelled payslip."))
        self.write({'state' : 'done'})

        line_values = self._get_line_values(['NET'])

        self.filtered(lambda p: not p.credit_note and line_values['NET'][p.id]['total'] < 0).write({'has_negative_net_to_report': True})
        self.mapped('payslip_run_id').action_close()
        # Validate work entries for regular payslips (exclude end of year bonus, ...)
        regular_payslips = self.filtered(lambda p: p.struct_id.type_id.default_struct_id == p.struct_id)
        work_entries = self.env['hr.work.entry']
        for regular_payslip in regular_payslips:
            work_entries |= self.env['hr.work.entry'].search([
                ('date_start', '<=', regular_payslip.date_to),
                ('date_stop', '>=', regular_payslip.date_from),
                ('employee_id', '=', regular_payslip.employee_id.id),
            ])
        if work_entries:
            work_entries.action_validate()

        self._generate_pdf()
        if self.env.context.get('payslip_generate_pdf'):
            if self.env.context.get('payslip_generate_pdf_direct'):
                self._generate_pdf()
            else:
                self.write({'queued_for_pdf': True})
                payslip_cron = self.env.ref('hr_payroll.ir_cron_generate_payslip_pdfs', raise_if_not_found=False)
                if payslip_cron:
                    payslip_cron._trigger()

