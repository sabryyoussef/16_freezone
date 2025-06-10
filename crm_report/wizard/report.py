import pytz
from odoo import models, fields, api
from odoo import exceptions
from datetime import datetime, timedelta
from collections import defaultdict


class ProductReports(models.TransientModel):
    _name = 'crm.lead.wizard'

    start_date = fields.Date(string="From Date", default=fields.Date.today())
    end_date = fields.Date(string="To Date", default=fields.Date.today())
    marketing_budget = fields.Float(string="Marketing Budget", default=1.0)
    report_type = fields.Selection([
        ('details', 'Details'),
        ('summary', 'Summary'),
        ],
        string='Report Type', default='details', required=True)

    @api.constrains('start_date', 'end_date')
    def _comparison_start_end_date(self):
        if self.start_date > self.end_date:
            raise exceptions.ValidationError('Start Date Must Be Less Than End Date')

    def get_lines_details(self):
        lst = []
        for rec in self:
            query_params = {'date_start': rec.start_date, 'date_end': rec.end_date}
            query = """
                    SELECT  
                       cl.create_date::date AS date,
                       cl.priority As priority,
                       rp.name AS client_name,
                       cl.email_from AS email,
                       cl.phone As phone,
                       rc.name As nationality,
                       cl.service As service,
                       uc.name As campaign,
                       us.name As source,
                       cs.name As stage
                    FROM crm_lead cl
                             LEFT JOIN res_partner rp ON (cl.partner_id = rp.id)
                             LEFT JOIN res_country rc ON (cl.nationality_id = rc.id)
                             LEFT JOIN utm_campaign uc ON (cl.campaign_id = uc.id)
                             LEFT JOIN utm_source us ON (cl.source_id = us.id)
                             LEFT JOIN crm_stage cs ON (cl.stage_id = cs.id)
                    WHERE
                         cl.create_date >= '%(date_start)s' AND
                         cl.create_date <= '%(date_end)s'  
                    ORDER BY cl.create_date;""" % query_params

            self.env.cr.execute(query)
            data = self.env.cr.dictfetchall()
            for line in data:
                nationality_value = line['nationality'].get('en_US', '') if isinstance(line['nationality'], dict) else \
                line['nationality']
                lst.append({
                    'date': line['date'],
                    'priority': line['priority'],
                    'client_name': line['client_name'],
                    'email': line['email'],
                    'phone': line['phone'],
                    'nationality': nationality_value,
                    'service': line['service'],
                    'campaign': line['campaign'],
                    'source': line['source'],
                    'stage': line['stage']['en_US'],
                })
        return lst

    def get_lines_summary(self):
        lst = []
        for rec in self:
            leads_count = self.env['crm.lead'].sudo().search_count([('create_date', '>=', rec.start_date),
                                                                    ('create_date', '<=', rec.end_date)])
            leads_prposal = self.env['crm.lead'].sudo().search_count([('create_date', '>=', rec.start_date),
                                                                      ('create_date', '<=', rec.end_date),
                                                                      ('stage_name', '=', 'Proposal Sent')])
            leads_conversion = self.env['crm.lead'].sudo().search_count([('create_date', '>=', rec.start_date),
                                                                      ('create_date', '<=', rec.end_date),
                                                                      ('stage_name', '=', 'Negotiation')])
            leads_lost = self.env['crm.lead'].sudo().search_count([('create_date', '>=', rec.start_date),
                                                                      ('create_date', '<=', rec.end_date),
                                                                      ('probability', '=', 0.0)])
            query = """
                SELECT SUM(expected_revenue) AS total_profit
                FROM crm_lead
                WHERE create_date >= %s AND create_date <= %s
            """
            self.env.cr.execute(query, (rec.start_date, rec.end_date))
            result = self.env.cr.fetchone()
            leads_total_profit = result[0] if result[0] is not None else 0.0
            lst.append({
                'leads_count': f"{leads_count:,}",
                'leads_prposal': f"{leads_prposal:,}" ,
                'leads_conversion': f"{leads_conversion:,}" ,
                'leads_lost': f"{leads_lost:,}" ,
                'leads_total_profit': f"{leads_total_profit:,}" ,
                'marketing_budget': f"{rec.marketing_budget:,}" ,
                'ROI': f"{((leads_total_profit / rec.marketing_budget) / rec.marketing_budget):,}" ,
            })
        return lst

    def print_xlsx_report(self):
        return self.env.ref('crm_report.report_crm_report_xlsx').report_action(self)

class XlsxReport(models.AbstractModel):
    _name = 'report.crm_report.print_items_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, partners):
        worksheet = workbook.add_worksheet('Sales Report')
        table_header = workbook.add_format(
            {'font_size': 16, 'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_color': '#FFFFFF',
             'fg_color': '#737CA1'})
        table_cell = workbook.add_format(
            {'font_size': 13, 'align': 'center', 'valign': 'vcenter', 'font_color': 'black'})
        header_format = workbook.add_format({
            'font_size': 16,
            'border': 1,
            'align': 'center',
            'font_color': 'black',
            'bold': True,
            'valign': 'vcenter',
            'border_color': 'black',
            'fg_color': '#C0C0C0'})
        header_format2 = workbook.add_format({
            'font_size': 18,
            'border': 1,
            'align': 'center',
            'font_color': 'white',
            'bold': True,
            'valign': 'vcenter',
            'border_color': 'black',
            'fg_color': '#C0C0C0'})
        header_format3 = workbook.add_format({
            'font_size': 14,
            'border': 1,
            'align': 'center',
            'font_color': 'black',
            'bold': True,
            'valign': 'vcenter',
            'border_color': 'black', })

        # worksheet.left_to_right()

        domain = []
        worksheet.set_column('A:A', 40)
        worksheet.set_column('B:B', 35)
        worksheet.set_column('C:C', 35)
        worksheet.set_column('D:D', 35)
        worksheet.set_column('E:E', 25)
        worksheet.set_column('G:G', 25)
        worksheet.set_column('F:F', 25)
        worksheet.set_column('H:H', 25)
        worksheet.set_column('I:I', 25)
        worksheet.set_column('J:J', 25)

        if partners.report_type == 'details':
            worksheet.merge_range('C1:E1', 'Lead Details Report', header_format2)
            worksheet.write('C3', 'From Date', header_format)
            worksheet.write('D3', 'To Date', header_format)
            worksheet.write('C5', str(partners.start_date), header_format3)
            worksheet.write('D5', str(partners.end_date), header_format3)

            # Table Header:
            row = 10
            column = 1
            worksheet.merge_range('A10:A11', 'Date', table_header)
            column += 1
            worksheet.merge_range('B10:B11', 'Lead heat', table_header)
            column += 1
            worksheet.merge_range('C10:C11', 'Client Name', table_header)
            column += 1
            worksheet.merge_range('D10:D11', 'Email', table_header)
            column += 1
            worksheet.merge_range('E10:E11', 'Phone Number', table_header)
            column += 1
            worksheet.merge_range('F10:F11', 'Nationality', table_header)
            column += 1
            worksheet.merge_range('G10:G11', 'Service', table_header)
            column += 1
            worksheet.merge_range('H10:H11', 'Campaign Name', table_header)
            column += 1
            worksheet.merge_range('I10:I11', 'Source of lead', table_header)
            column += 1
            worksheet.merge_range('J10:J11', 'Status', table_header)
            column += 1

            row += 1
            column = 0
            for line in partners.get_lines_details():
                worksheet.write(row, column, str(line['date']) or '', table_cell)
                worksheet.write(row, column + 1, line['priority'] or '', table_cell)
                worksheet.write(row, column + 2, str(line['client_name']) or '', table_cell)
                worksheet.write(row, column + 3, line['email'] or '', table_cell)
                worksheet.write(row, column + 4, line['phone'] or '', table_cell)
                worksheet.write(row, column + 5, str(line['nationality']) or '', table_cell)
                worksheet.write(row, column + 6, line['service'] or '', table_cell)
                worksheet.write(row, column + 7, line['campaign'] or '', table_cell)
                worksheet.write(row, column + 8, line['source'] or '', table_cell)
                worksheet.write(row, column + 9, str(line['stage']) or '', table_cell)
                row += 1
        # else:
        #     worksheet.merge_range('C1:E1', 'Summary Report', header_format2)
        #     worksheet.write('C3', 'From Date', header_format)
        #     worksheet.write('D3', 'To Date', header_format)
        #     worksheet.write('C5', str(partners.start_date), header_format3)
        #     worksheet.write('D5', str(partners.end_date), header_format3)
        #
        #     # Table Header:
        #     row = 10
        #     column = 1
        #     worksheet.merge_range('A10:A11', 'Number of leads', table_header)
        #     column += 1
        #     worksheet.merge_range('B10:B11', 'Number of proposal sents', table_header)
        #     column += 1
        #     worksheet.merge_range('C10:C11', 'Number of Conversions', table_header)
        #     column += 1
        #     worksheet.merge_range('D10:D11', 'Number of lost deals', table_header)
        #     column += 1
        #     worksheet.merge_range('E10:E11', 'Total Profit', table_header)
        #     column += 1
        #     worksheet.merge_range('F10:F11', 'Marketing Budget', table_header)
        #     column += 1
        #     worksheet.merge_range('G10:G11', 'ROI', table_header)
        #     column += 1
        #
        #     row += 1
        #     column = 0
        #     for line in partners.get_lines_summary():
        #         worksheet.write(row, column, line['leads_count'] or 0.0, table_cell)
        #         worksheet.write(row, column + 1, line['leads_prposal'] or 0.0, table_cell)
        #         worksheet.write(row, column + 2, line['leads_conversion'] or 0.0, table_cell)
        #         worksheet.write(row, column + 3, line['leads_lost'] or 0.0, table_cell)
        #         worksheet.write(row, column + 4, line['leads_total_profit'] or 0.0, table_cell)
        #         worksheet.write(row, column + 5, line['marketing_budget'] or 0.0, table_cell)
        #         worksheet.write(row, column + 6, line['ROI'] or 0.0, table_cell)
        #         row += 1


