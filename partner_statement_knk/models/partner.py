# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import models, fields, _
from odoo.tools import float_is_zero


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _get_partner_move_lines(self, account_type, date_from, period_length):
        # This method can receive the context key 'include_nullified_amount' {Boolean}
        # Do an invoice and a payment and unreconcile. The amount will be nullified
        # By default, the partner wouldn't appear in this report.
        # The context key allow it to appear
        # In case of a period_length of 30 days as of 2019-02-08, we want the following periods:
        # Name       Stop         Start
        # 1 - 30   : 2019-02-07 - 2019-01-09
        # 31 - 60  : 2019-01-08 - 2018-12-10
        # 61 - 90  : 2018-12-09 - 2018-11-10
        # 91 - 120 : 2018-11-09 - 2018-10-11
        # +120     : 2018-10-10
        ctx = self._context
        periods = {}
        date_from = fields.Date.from_string(date_from)
        start = date_from
        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length)
            period_name = str((5-(i+1)) * period_length + 1) + \
                '-' + str((5-i) * period_length)
            period_stop = (start - relativedelta(days=1)).strftime('%Y-%m-%d')
            if i == 0:
                period_name = '+' + str(4 * period_length)
            periods[str(i)] = {
                'name': period_name,
                'stop': period_stop,
                'start': (i != 0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop

        res = []
        total = []
        partner_clause = ''
        cr = self.env.cr
        user_company = self.env.company
        user_currency = user_company.currency_id
        company_ids = self._context.get('company_ids') or [user_company.id]
        move_state = ['draft', 'posted']
        # if target_move == 'posted':
        #     move_state = ['posted']
        arg_list = (tuple(move_state), tuple(
            account_type), date_from, date_from,)
        if 'partner_ids' in ctx:
            if ctx['partner_ids']:
                partner_clause = 'AND (l.partner_id IN %s)'
                arg_list += (tuple(ctx['partner_ids']),)
            else:
                partner_clause = 'AND l.partner_id IS NULL'
        if ctx.get('partner_categories'):
            partner_clause += 'AND (l.partner_id IN %s)'
            partner_ids = self.env['res.partner'].search(
                [('category_id', 'in', ctx['partner_categories'].ids)]).ids
            arg_list += (tuple(partner_ids or [0]),)
        arg_list += (date_from, tuple(company_ids))

        query = '''
            SELECT DISTINCT l.partner_id, res_partner.name AS name, UPPER(res_partner.name) AS UPNAME, CASE WHEN prop.value_text IS NULL THEN 'normal' ELSE prop.value_text END AS trust
            FROM account_move_line AS l
              LEFT JOIN res_partner ON l.partner_id = res_partner.id
              LEFT JOIN ir_property prop ON (prop.res_id = 'res.partner,'||res_partner.id AND prop.name='trust' AND prop.company_id=%s),
              account_account, account_move am
            WHERE (l.account_id = account_account.id)
                AND (l.move_id = am.id)
                AND (am.state IN %s)
                AND (account_account.account_type IN %s)
                AND (
                        l.reconciled IS FALSE
                        OR l.id IN(
                            SELECT credit_move_id FROM account_partial_reconcile where max_date > %s
                            UNION ALL
                            SELECT debit_move_id FROM account_partial_reconcile where max_date > %s
                        )
                    )
                    ''' + partner_clause + '''
                AND (l.date <= %s)
                AND l.company_id IN %s
            ORDER BY UPPER(res_partner.name)'''
        arg_list = (self.env.company.id,) + arg_list
        cr.execute(query, arg_list)

        partners = cr.dictfetchall()
        # put a total of 0
        for i in range(7):
            total.append(0)

        # Build a string like (1,2,3) for easy use in SQL query
        partner_ids = [partner['partner_id'] for partner in partners]
        lines = dict((partner['partner_id'], []) for partner in partners)
        if not partner_ids:
            return [], [], {}

        # Use one query per period and store results in history (a list variable)
        # Each history will contain: history[1] = {'<partner_id>': <partner_debit-credit>}
        history = []
        for i in range(5):
            args_list = (tuple(move_state), tuple(
                account_type), tuple(partner_ids),)
            dates_query = '(COALESCE(l.date_maturity,l.date)'

            if periods[str(i)]['start'] and periods[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s)'
                args_list += (periods[str(i)]['start'],
                              periods[str(i)]['stop'])
            elif periods[str(i)]['start']:
                dates_query += ' >= %s)'
                args_list += (periods[str(i)]['start'],)
            else:
                dates_query += ' <= %s)'
                args_list += (periods[str(i)]['stop'],)
            args_list += (date_from, tuple(company_ids))

            query = '''SELECT l.id
                    FROM account_move_line AS l, account_account, account_move am
                    WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                        AND (am.state IN %s)
                        AND (account_account.account_type IN %s)
                        AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                        AND ''' + dates_query + '''
                    AND (l.date <= %s)
                    AND l.company_id IN %s
                    ORDER BY COALESCE(l.date_maturity, l.date)'''
            cr.execute(query, args_list)
            partners_amount = {}
            aml_ids = cr.fetchall()
            aml_ids = aml_ids and [x[0] for x in aml_ids] or []
            for line in self.env['account.move.line'].browse(aml_ids).with_context(prefetch_fields=False):
                partner_id = line.partner_id.id or False
                if partner_id not in partners_amount:
                    partners_amount[partner_id] = 0.0
                line_amount = line.company_id.currency_id._convert(
                    line.balance, user_currency, user_company, date_from)
                if user_currency.is_zero(line_amount):
                    continue
                for partial_line in line.matched_debit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount += partial_line.company_id.currency_id._convert(
                            partial_line.amount, user_currency, user_company, date_from)
                for partial_line in line.matched_credit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount -= partial_line.company_id.currency_id._convert(
                            partial_line.amount, user_currency, user_company, date_from)

                if not self.env.company.currency_id.is_zero(line_amount):
                    partners_amount[partner_id] += line_amount
                    lines.setdefault(partner_id, [])
                    lines[partner_id].append({
                        'line': line,
                        'amount': line_amount,
                        'period': i + 1,
                    })
            history.append(partners_amount)

        # This dictionary will store the not due amount of all partners
        undue_amounts = {}
        query = '''SELECT l.id
                FROM account_move_line AS l, account_account, account_move am
                WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                    AND (am.state IN %s)
                    AND (account_account.account_type IN %s)
                    AND (COALESCE(l.date_maturity,l.date) >= %s)\
                    AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                AND (l.date <= %s)
                AND l.company_id IN %s
                ORDER BY COALESCE(l.date_maturity, l.date)'''
        cr.execute(query, (tuple(move_state), tuple(account_type),
                           date_from, tuple(partner_ids), date_from, tuple(company_ids)))
        aml_ids = cr.fetchall()
        aml_ids = aml_ids and [x[0] for x in aml_ids] or []
        for line in self.env['account.move.line'].browse(aml_ids):
            partner_id = line.partner_id.id or False
            if partner_id not in undue_amounts:
                undue_amounts[partner_id] = 0.0
            line_amount = line.company_id.currency_id._convert(
                line.balance, user_currency, user_company, date_from)
            if user_currency.is_zero(line_amount):
                continue
            for partial_line in line.matched_debit_ids:
                if partial_line.max_date <= date_from:
                    line_amount += partial_line.company_id.currency_id._convert(
                        partial_line.amount, user_currency, user_company, date_from)
            for partial_line in line.matched_credit_ids:
                if partial_line.max_date <= date_from:
                    line_amount -= partial_line.company_id.currency_id._convert(
                        partial_line.amount, user_currency, user_company, date_from)
            if not self.env.company.currency_id.is_zero(line_amount):
                undue_amounts[partner_id] += line_amount
                lines.setdefault(partner_id, [])
                lines[partner_id].append({
                    'line': line,
                    'amount': line_amount,
                    'period': 6,
                })

        for partner in partners:
            if partner['partner_id'] is None:
                partner['partner_id'] = False
            at_least_one_amount = False
            values = {}
            undue_amt = 0.0
            # Making sure this partner actually was found by the query
            if partner['partner_id'] in undue_amounts:
                undue_amt = undue_amounts[partner['partner_id']]

            total[6] = total[6] + undue_amt
            values['direction'] = undue_amt
            if not float_is_zero(values['direction'], precision_rounding=self.env.company.currency_id.rounding):
                at_least_one_amount = True

            for i in range(5):
                during = False
                if partner['partner_id'] in history[i]:
                    during = [history[i][partner['partner_id']]]
                # Adding counter
                total[(i)] = total[(i)] + (during and during[0] or 0)
                values[str(i)] = during and during[0] or 0.0
                if not float_is_zero(values[str(i)], precision_rounding=self.env.company.currency_id.rounding):
                    at_least_one_amount = True
            values['total'] = sum([values['direction']] +
                                  [values[str(i)] for i in range(5)])
            # Add for total
            total[(i + 1)] += values['total']
            values['partner_id'] = partner['partner_id']
            if partner['partner_id']:
                values['name'] = len(
                    partner['name']) >= 45 and partner['name'][0:40] + '...' or partner['name']
                values['trust'] = partner['trust']
            else:
                values['name'] = _('Unknown Partner')
                values['trust'] = False

            if at_least_one_amount or (self._context.get('include_nullified_amount') and lines[partner['partner_id']]):
                res.append(values)
        return res, total, lines

    def get_opbalance(self, from_date, to_date):
        domain = [('partner_id', '=', self.id), ('move_type', 'in', ('out_invoice', 'out_refund')),
                  ('state', '=', 'posted'), ('payment_state', '=', 'not_paid')]
        if from_date:
            domain += [('invoice_date', '<', from_date)]
        invoices = self.env['account.move'].search(
            domain, order='invoice_date')
        return sum(invoices.mapped("amount_residual"))

    def get_statements(self, from_date, to_date):
        domain = [('partner_id', '=', self.id), ('move_type', 'in', ('out_invoice', 'out_refund')),
                  ('state', '=', 'posted'), ('payment_state', '=', 'not_paid')]
        if from_date and to_date:
            domain += [('invoice_date', '>=', from_date),
                       ('invoice_date', '<=', to_date)]
        return self.env['account.move'].search(domain, order='invoice_date')

    def get_agedheader(self, from_date, to_date):
        res = {}
        period_length = 30
        if not from_date:
            from_date = fields.Date.today()
        start = datetime.strptime(str(from_date), "%Y-%m-%d")
        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length - 1)
            res[str(i)] = {
                'name': (i != 0 and (str((5-(i+1)) * period_length) + '-' + str((5-i) * period_length)) or ('+'+str(4 * period_length))),
                'stop': start.strftime('%Y-%m-%d'),
                'start': (i != 0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop - relativedelta(days=1)
        return res

    def get_ageddata(self, from_date, to_date):
        # target_move = 'posted'
        account_type = ['asset_receivable', 'liability_payable']
        if not from_date:
            from_date = fields.Date.today()
        movelines, total, total = self._get_partner_move_lines(
            account_type, from_date, 30)
        return movelines

    def action_view_statements(self):
        self.ensure_one()
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        action['domain'] = [
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('state', '=', 'posted'),
            ('partner_id', 'child_of', self.id),
            ('payment_state', '=', 'not_paid'),
        ]
        return action
