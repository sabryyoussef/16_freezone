from odoo import api, fields, Command, models, _
from odoo.tools import  float_compare

class Expense(models.Model):
    _inherit = 'hr.expense'

    vendor_id = fields.Many2one('res.partner',domain="[('supplier_rank' ,'>', 0)]")

    def _get_default_expense_sheet_values(self):
        # If there is an expense with total_amount_company == 0, it means that expense has not been processed by OCR yet
        expenses_with_amount = self.filtered(lambda expense: not float_compare(expense.total_amount_company, 0.0, precision_rounding=expense.company_currency_id.rounding) == 0)

        if any(expense.state != 'draft' or expense.sheet_id for expense in expenses_with_amount):
            raise UserError(_("You cannot report twice the same line!"))
        if not expenses_with_amount:
            raise UserError(_("You cannot report the expenses without amount!"))
        if len(expenses_with_amount.mapped('employee_id')) != 1:
            raise UserError(_("You cannot report expenses for different employees in the same report."))
        if any(not expense.product_id for expense in expenses_with_amount):
            raise UserError(_("You can not create report without category."))
        if len(self.company_id) != 1:
            raise UserError(_("You cannot report expenses for different companies in the same report."))

        # Check if two reports should be created
        own_expenses = expenses_with_amount.filtered(lambda x: x.payment_mode == 'own_account')
        company_expenses = expenses_with_amount - own_expenses
        create_two_reports = own_expenses and company_expenses

        sheets = [own_expenses, company_expenses] if create_two_reports else [expenses_with_amount]
        values = []
        for todo in sheets:
            if len(todo) == 1:
                expense_name = todo.name
            else:
                dates = todo.mapped('date')
                min_date = format_date(self.env, min(dates))
                max_date = format_date(self.env, max(dates))
                expense_name = min_date if max_date == min_date else "%s - %s" % (min_date, max_date)

            vals = {
                'company_id': self.company_id.id,
                'employee_id': self[0].employee_id.id,
                'name': expense_name,
                'expense_line_ids': [Command.set(todo.ids)],
                'state': 'draft',
                'vendor_id': self.vendor_id.id,
            }
            values.append(vals)
        return values

class Payment(models.TransientModel):
    _inherit = 'account.payment.register'

    vendor_id = fields.Many2one('res.partner', domain="[('supplier_rank' ,'>', 0)]")

    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = {
            'date': self.payment_date,
            'amount': self.amount,
            'payment_type': self.payment_type,
            'partner_type': self.partner_type,
            'ref': self.communication,
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id.id,
            'partner_id': self.vendor_id.id,
            'partner_bank_id': self.partner_bank_id.id,
            'payment_method_line_id': self.payment_method_line_id.id,
            'destination_account_id': self.line_ids[0].account_id.id,
            'write_off_line_vals': [],
        }

        conversion_rate = self.env['res.currency']._get_conversion_rate(
            self.currency_id,
            self.company_id.currency_id,
            self.company_id,
            self.payment_date,
        )

        if self.payment_difference_handling == 'reconcile':

            if self.early_payment_discount_mode:
                epd_aml_values_list = []
                for aml in batch_result['lines']:
                    if aml._is_eligible_for_early_payment_discount(self.currency_id, self.payment_date):
                        epd_aml_values_list.append({
                            'aml': aml,
                            'amount_currency': -aml.amount_residual_currency,
                            'balance': aml.company_currency_id.round(-aml.amount_residual_currency * conversion_rate),
                        })

                open_amount_currency = self.payment_difference * (-1 if self.payment_type == 'outbound' else 1)
                open_balance = self.company_id.currency_id.round(open_amount_currency * conversion_rate)
                early_payment_values = self.env[
                    'account.move']._get_invoice_counterpart_amls_for_early_payment_discount(epd_aml_values_list,
                                                                                             open_balance)
                for aml_values_list in early_payment_values.values():
                    payment_vals['write_off_line_vals'] += aml_values_list

            elif not self.currency_id.is_zero(self.payment_difference):
                if self.payment_type == 'inbound':
                    # Receive money.
                    write_off_amount_currency = self.payment_difference
                else:  # if self.payment_type == 'outbound':
                    # Send money.
                    write_off_amount_currency = -self.payment_difference

                write_off_balance = self.company_id.currency_id.round(write_off_amount_currency * conversion_rate)
                payment_vals['write_off_line_vals'].append({
                    'name': self.writeoff_label,
                    'account_id': self.writeoff_account_id.id,
                    'partner_id': self.vendor_id.id,
                    'currency_id': self.currency_id.id,
                    'amount_currency': write_off_amount_currency,
                    'balance': write_off_balance,
                })
        return payment_vals


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    vendor_id = fields.Many2one('res.partner', domain="[('supplier_rank' ,'>', 0)]")

    def action_register_payment(self):
        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'context': {
                'active_model': 'account.move',
                'active_ids': self.account_move_id.ids,
                'default_partner_bank_id': self.employee_id.sudo().bank_account_id.id if len(self.employee_id.sudo().bank_account_id.ids) <= 1 else None,
                'default_vendor_id': self.vendor_id.id,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('hr_expense_custom.view_account_payment_register_custom_form').id,
            'views': [(self.env.ref('hr_expense_custom.view_account_payment_register_custom_form').id, 'form')],
        }

    def _prepare_move_vals(self):
        self.ensure_one()
        return {
            'name': '/',
            'date': self.accounting_date or max(self.expense_line_ids.mapped('date')) or fields.Date.context_today(self),
            'invoice_date': self.accounting_date or fields.Date.context_today(self),  # expense payment behave as bills
            'ref': self.name,
            'partner_id': self.vendor_id.id,
            'expense_sheet_id': [Command.set(self.ids)],
        }
