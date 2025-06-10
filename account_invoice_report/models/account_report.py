from odoo import models, _
from odoo.tools import format_date, date_utils, get_lang
from collections import defaultdict
from odoo.exceptions import UserError, RedirectWarning

import json
import datetime


class JournalReportCustomHandler(models.AbstractModel):
    _inherit = 'account.journal.report.handler'

    def _get_tax_grids_summary(self, options, data):
        """
        Fetches the details of all grids that have been used in the provided journal.
        The result is grouped by the country in which the tag exists in case of multivat environment.
        Returns a dictionary with the following structure:
        {
            Country : {
                tag_name: {+, -, impact},
                tag_name: {+, -, impact},
                tag_name: {+, -, impact},
                ...
            },
            Country : [
                tag_name: {+, -, impact},
                tag_name: {+, -, impact},
                tag_name: {+, -, impact},
                ...
            ],
            ...
        }
        """
        report = self.env.ref('account_reports.journal_report')
        # Use the same option as we use to get the tax details, but this time to generate the query used to fetch the
        # grid information
        tax_report_options = self._get_generic_tax_report_options(options, data)
        tables, where_clause, where_params = report._query_get(tax_report_options, 'strict_range')
        lang = self.env.user.lang or get_lang(self.env).code
        country_name = f"COALESCE(country.name->>'{lang}', country.name->>'en_US')"
        tag_name = f"COALESCE(tag.name->>'{lang}', tag.name->>'en_US')" if \
            self.pool['account.account.tag'].name.translate else 'tag.name'

        query = f"""
            WITH tag_info (country_name, tag_id, tag_name, tag_sign, balance) as (
                SELECT
                    COALESCE(country.name->>'en_US', country.name::text) AS country_name, -- Cast country.name (jsonb) to text
                    tag.id,
                    {tag_name} AS name,
                    CASE WHEN tag.tax_negate IS TRUE THEN '-' ELSE '+' END,
                    SUM(COALESCE("account_move_line".balance, 0)
                        * CASE WHEN "account_move_line".tax_tag_invert THEN -1 ELSE 1 END
                        ) AS balance
                FROM account_account_tag tag
                JOIN account_account_tag_account_move_line_rel rel ON tag.id = rel.account_account_tag_id
                JOIN res_country country ON country.id = tag.country_id
                , {tables}
                WHERE {where_clause}
                  AND applicability = 'taxes'
                  AND "account_move_line".id = rel.account_move_line_id
                GROUP BY COALESCE(country.name->>'en_US', country.name::text), tag.id -- Group by the same expression
            )
            SELECT
                country_name,
                tag_id,
                REGEXP_REPLACE(tag_name, '^[+-]', '') AS name, -- Remove the sign from the grid name
                balance,
                tag_sign AS sign
            FROM tag_info
            ORDER BY country_name, name
        """

        self._cr.execute(query, where_params)
        query_res = self.env.cr.fetchall()

        res = defaultdict(lambda: defaultdict(dict))
        opposite = {'+': '-', '-': '+'}
        for country_name, tag_id, name, balance, sign in query_res:
            res[country_name][name]['tag_id'] = tag_id
            res[country_name][name][sign] = report.format_value(balance, blank_if_zero=False, figure_type='monetary')
            # We need them formatted, to ensure they are displayed correctly in the report. (E.g. 0.0, not 0)
            if not opposite[sign] in res[country_name][name]:
                res[country_name][name][opposite[sign]] = report.format_value(0, blank_if_zero=False,
                                                                              figure_type='monetary')
            res[country_name][name][sign + '_no_format'] = balance
            res[country_name][name]['impact'] = report.format_value(
                res[country_name][name].get('+_no_format', 0) - res[country_name][name].get('-_no_format', 0),
                blank_if_zero=False, figure_type='monetary')

        return res
