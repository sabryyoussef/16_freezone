
from odoo import api, fields, models
import re

class Partner(models.Model):
    _inherit = 'res.partner'

    first_name = fields.Char(string="First Name", tracking=True)
    middle_name = fields.Char(string="Middle Name", tracking=True)
    last_name = fields.Char(string="Last Name", tracking=True)
    mobile = fields.Char(string="Mobile", tracking=True)
    mobile_country_id = fields.Many2one("res.country", required=True, tracking=True)


    @api.onchange('first_name', 'middle_name', 'last_name')
    def change_partner_name(self):
        for rec in self:
            rec.name = ' '.join(filter(None, [rec.first_name, rec.middle_name, rec.last_name]))

    @api.depends('is_company', 'name', 'type', 'company_name', 'commercial_company_name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = self.name


    @api.constrains('mobile', 'mobile_country_id')
    def _check_mobile_format(self):
        # Dictionary of country codes, their corresponding phone codes, and expected mobile number lengths (excluding the '+' and country code)
        country_phone_codes = {
            'AF': {'code': '93', 'length': [9]},  # Afghanistan
            'AL': {'code': '355', 'length': [9]},  # Albania
            'DZ': {'code': '213', 'length': [9]},  # Algeria
            'AD': {'code': '376', 'length': [6]},  # Andorra
            'AO': {'code': '244', 'length': [9]},  # Angola
            'AR': {'code': '54', 'length': [10]},  # Argentina
            'AM': {'code': '374', 'length': [8]},  # Armenia
            'AU': {'code': '61', 'length': [9]},  # Australia
            'AT': {'code': '43', 'length': [10]},  # Austria
            'AZ': {'code': '994', 'length': [9]},  # Azerbaijan
            'BH': {'code': '973', 'length': [8]},  # Bahrain
            'BD': {'code': '880', 'length': [10]},  # Bangladesh
            'BY': {'code': '375', 'length': [9]},  # Belarus
            'BE': {'code': '32', 'length': [9]},  # Belgium
            'BZ': {'code': '501', 'length': [7]},  # Belize
            'BJ': {'code': '229', 'length': [8]},  # Benin
            'BT': {'code': '975', 'length': [8]},  # Bhutan
            'BO': {'code': '591', 'length': [8]},  # Bolivia
            'BA': {'code': '387', 'length': [8]},  # Bosnia and Herzegovina
            'BW': {'code': '267', 'length': [7]},  # Botswana
            'BR': {'code': '55', 'length': [11]},  # Brazil
            'BN': {'code': '673', 'length': [7]},  # Brunei
            'BG': {'code': '359', 'length': [9]},  # Bulgaria
            'BF': {'code': '226', 'length': [8]},  # Burkina Faso
            'BI': {'code': '257', 'length': [8]},  # Burundi
            'KH': {'code': '855', 'length': [9]},  # Cambodia
            'CM': {'code': '237', 'length': [9]},  # Cameroon
            'CA': {'code': '1', 'length': [10]},  # Canada
            'CV': {'code': '238', 'length': [7]},  # Cape Verde
            'CF': {'code': '236', 'length': [9]},  # Central African Republic
            'TD': {'code': '235', 'length': [9]},  # Chad
            'CL': {'code': '56', 'length': [9]},  # Chile
            'CN': {'code': '86', 'length': [11]},  # China
            'CO': {'code': '57', 'length': [10]},  # Colombia
            'KM': {'code': '269', 'length': [7]},  # Comoros
            'CG': {'code': '242', 'length': [9]},  # Congo
            'CR': {'code': '506', 'length': [8]},  # Costa Rica
            'HR': {'code': '385', 'length': [9]},  # Croatia
            'CU': {'code': '53', 'length': [10]},  # Cuba
            'CY': {'code': '357', 'length': [8]},  # Cyprus
            'CZ': {'code': '420', 'length': [9]},  # Czech Republic
            'DK': {'code': '45', 'length': [8]},  # Denmark
            'DJ': {'code': '253', 'length': [8]},  # Djibouti
            'DM': {'code': '1', 'length': [10]},  # Dominica
            'DO': {'code': '1', 'length': [10]},  # Dominican Republic
            'EC': {'code': '593', 'length': [9]},  # Ecuador
            'EG': {'code': '20', 'length': [10]},  # Egypt
            'SV': {'code': '503', 'length': [8]},  # El Salvador
            'GQ': {'code': '240', 'length': [9]},  # Equatorial Guinea
            'ER': {'code': '291', 'length': [7]},  # Eritrea
            'EE': {'code': '372', 'length': [8]},  # Estonia
            'ET': {'code': '251', 'length': [9]},  # Ethiopia
            'FJ': {'code': '679', 'length': [7]},  # Fiji
            'FI': {'code': '358', 'length': [9]},  # Finland
            'FR': {'code': '33', 'length': [9]},  # France
            'GA': {'code': '241', 'length': [9]},  # Gabon
            'GM': {'code': '220', 'length': [7]},  # Gambia
            'GE': {'code': '995', 'length': [9]},  # Georgia
            'DE': {'code': '49', 'length': [10,11]},  # Germany
            'GH': {'code': '233', 'length': [9]},  # Ghana
            'GR': {'code': '30', 'length': [10]},  # Greece
            'GD': {'code': '1', 'length': [10]},  # Grenada
            'GT': {'code': '502', 'length': [8]},  # Guatemala
            'GN': {'code': '224', 'length': [9]},  # Guinea
            'GW': {'code': '245', 'length': [7]},  # Guinea-Bissau
            'GY': {'code': '592', 'length': [7]},  # Guyana
            'HT': {'code': '509', 'length': [8]},  # Haiti
            'HN': {'code': '504', 'length': [8]},  # Honduras
            'HK': {'code': '852', 'length': [8]},  # Hong Kong
            'HU': {'code': '36', 'length': [9]},  # Hungary
            'IS': {'code': '354', 'length': [7]},  # Iceland
            'IN': {'code': '91', 'length': [10]},  # India
            'ID': {'code': '62', 'length': [10]},  # Indonesia
            'IR': {'code': '98', 'length': [10]},  # Iran
            'IQ': {'code': '964', 'length': [10]},  # Iraq
            'IE': {'code': '353', 'length': [9]},  # Ireland
            'IL': {'code': '972', 'length': [9]},  # Israel
            'IT': {'code': '39', 'length': [10]},  # Italy
            'JM': {'code': '1', 'length': [10]},  # Jamaica
            'JP': {'code': '81', 'length': [10]},  # Japan
            'JO': {'code': '962', 'length': [9]},  # Jordan
            'KZ': {'code': '7', 'length': [10]},  # Kazakhstan
            'KE': {'code': '254', 'length': [9]},  # Kenya
            'KI': {'code': '686', 'length': [5]},  # Kiribati
            'KP': {'code': '850', 'length': [10]},  # North Korea
            'KR': {'code': '82', 'length': [10]},  # South Korea
            'KW': {'code': '965', 'length': [8]},  # Kuwait
            'KG': {'code': '996', 'length': [9]},  # Kyrgyzstan
            'LA': {'code': '856', 'length': [9]},  # Laos
            'LV': {'code': '371', 'length': [8]},  # Latvia
            'LB': {'code': '961', 'length': [8]},  # Lebanon
            'LS': {'code': '266', 'length': [8]},  # Lesotho
            'LR': {'code': '231', 'length': [7]},  # Liberia
            'LY': {'code': '218', 'length': [9]},  # Libya
            'LI': {'code': '423', 'length': [9]},  # Liechtenstein
            'LT': {'code': '370', 'length': [8]},  # Lithuania
            'LU': {'code': '352', 'length': [9]},  # Luxembourg
            'MO': {'code': '853', 'length': [8]},  # Macau
            'MK': {'code': '389', 'length': [8]},  # North Macedonia
            'MG': {'code': '261', 'length': [9]},  # Madagascar
            'MW': {'code': '265', 'length': [9]},  # Malawi
            'MY': {'code': '60', 'length': [10]},  # Malaysia
            'MV': {'code': '960', 'length': [7]},  # Maldives
            'ML': {'code': '223', 'length': [8]},  # Mali
            'MT': {'code': '356', 'length': [8]},  # Malta
            'MH': {'code': '692', 'length': [7]},  # Marshall Islands
            'MR': {'code': '222', 'length': [8]},  # Mauritania
            'MU': {'code': '230', 'length': [8]},  # Mauritius
            'MX': {'code': '52', 'length': [10]},  # Mexico
            'FM': {'code': '691', 'length': [7]},  # Micronesia
            'MD': {'code': '373', 'length': [8]},  # Moldova
            'MC': {'code': '377', 'length': [8]},  # Monaco
            'MN': {'code': '976', 'length': [8]},  # Mongolia
            'ME': {'code': '382', 'length': [8]},  # Montenegro
            'MA': {'code': '212', 'length': [9]},  # Morocco
            'MZ': {'code': '258', 'length': [9]},  # Mozambique
            'MM': {'code': '95', 'length': [9]},  # Myanmar
            'NA': {'code': '264', 'length': [9]},  # Namibia
            'NR': {'code': '674', 'length': [7]},  # Nauru
            'NP': {'code': '977', 'length': [10]},  # Nepal
            'NL': {'code': '31', 'length': [9]},  # Netherlands
            'NZ': {'code': '64', 'length': [9]},  # New Zealand
            'NI': {'code': '505', 'length': [8]},  # Nicaragua
            'NE': {'code': '227', 'length': [8]},  # Niger
            'NG': {'code': '234', 'length': [10]},  # Nigeria
            'NO': {'code': '47', 'length': [8]},  # Norway
            'OM': {'code': '968', 'length': [8]},  # Oman
            'PK': {'code': '92', 'length': [10]},  # Pakistan
            'PW': {'code': '680', 'length': [7]},  # Palau
            'PA': {'code': '507', 'length': [8]},  # Panama
            'PG': {'code': '675', 'length': [8]},  # Papua New Guinea
            'PY': {'code': '595', 'length': [9]},  # Paraguay
            'PE': {'code': '51', 'length': [9]},  # Peru
            'PH': {'code': '63', 'length': [10]},  # Philippines
            'PL': {'code': '48', 'length': [9]},  # Poland
            'PT': {'code': '351', 'length': [9]},  # Portugal
            'QA': {'code': '974', 'length': [8]},  # Qatar
            'RO': {'code': '40', 'length': [10]},  # Romania
            'RU': {'code': '7', 'length': [10]},  # Russia
            'RW': {'code': '250', 'length': [9]},  # Rwanda
            'KN': {'code': '1', 'length': [10]},  # Saint Kitts and Nevis
            'LC': {'code': '1', 'length': [10]},  # Saint Lucia
            'VC': {'code': '1', 'length': [10]},  # Saint Vincent and the Grenadines
            'WS': {'code': '685', 'length': [7]},  # Samoa
            'SM': {'code': '378', 'length': [10]},  # San Marino
            'ST': {'code': '239', 'length': [7]},  # Sao Tome and Principe
            'SA': {'code': '966', 'length': [9]},  # Saudi Arabia
            'SN': {'code': '221', 'length': [9]},  # Senegal
            'RS': {'code': '381', 'length': [9]},  # Serbia
            'SC': {'code': '248', 'length': [7]},  # Seychelles
            'SL': {'code': '232', 'length': [8]},  # Sierra Leone
            'SG': {'code': '65', 'length': [8]},  # Singapore
            'SK': {'code': '421', 'length': [9]},  # Slovakia
            'SI': {'code': '386', 'length': [9]},  # Slovenia
            'SB': {'code': '677', 'length': [7]},  # Solomon Islands
            'SO': {'code': '252', 'length': [9]},  # Somalia
            'ZA': {'code': '27', 'length': [9]},  # South Africa
            'SS': {'code': '211', 'length': [9]},  # South Sudan
            'ES': {'code': '34', 'length': [9]},  # Spain
            'LK': {'code': '94', 'length': [9]},  # Sri Lanka
            'SD': {'code': '249', 'length': [9]},  # Sudan
            'SR': {'code': '597', 'length': [7]},  # Suriname
            'SZ': {'code': '268', 'length': [8]},  # Swaziland
            'SE': {'code': '46', 'length': [9]},  # Sweden
            'CH': {'code': '41', 'length': [9]},  # Switzerland
            'SY': {'code': '963', 'length': [9]},  # Syria
            'TW': {'code': '886', 'length': [9]},  # Taiwan
            'TJ': {'code': '992', 'length': [9]},  # Tajikistan
            'TZ': {'code': '255', 'length': [9]},  # Tanzania
            'TH': {'code': '66', 'length': [9]},  # Thailand
            'TL': {'code': '670', 'length': [8]},  # Timor-Leste
            'TG': {'code': '228', 'length': [8]},  # Togo
            'TO': {'code': '676', 'length': [5]},  # Tonga
            'TT': {'code': '1', 'length': [10]},  # Trinidad and Tobago
            'TN': {'code': '216', 'length': [8]},  # Tunisia
            'TR': {'code': '90', 'length': [10]},  # Turkey
            'TM': {'code': '993', 'length': [8]},  # Turkmenistan
            'TV': {'code': '688', 'length': [6]},  # Tuvalu
            'UG': {'code': '256', 'length': [9]},  # Uganda
            'UA': {'code': '380', 'length': [9]},  # Ukraine
            'AE': {'code': '971', 'length': [9]},  # United Arab Emirates
            'GB': {'code': '44', 'length': [10]},  # United Kingdom
            'US': {'code': '1', 'length': [10]},  # United States
            'UY': {'code': '598', 'length': [9]},  # Uruguay
            'UZ': {'code': '998', 'length': [9]},  # Uzbekistan
            'VU': {'code': '678', 'length': [7]},  # Vanuatu
            'VA': {'code': '379', 'length': [10]},  # Vatican City
            'VE': {'code': '58', 'length': [10]},  # Venezuela
            'VN': {'code': '84', 'length': [9]},  # Vietnam
            'YE': {'code': '967', 'length': [9]},  # Yemen
            'ZM': {'code': '260', 'length': [9]},  # Zambia
            'ZW': {'code': '263', 'length': [9]},  # Zimbabwe
            'BB': {'code': '1246', 'length': [7]},  # barbados
            'CI': {'code': '225', 'length': [10]},  # cote d'ivoire
        }

        for partner in self:
            if partner.mobile and partner.mobile_country_id:
                country_code = partner.mobile_country_id.code
                country_name = partner.mobile_country_id.name
                if not country_code:
                    raise models.ValidationError('The country code is missing for the selected country.')

                phone_info = country_phone_codes.get(country_code)

                if not phone_info:
                    raise models.ValidationError(
                        f'The phone code for country {country_name} ({country_code}) is not defined.')

                phone_code = phone_info['code']
                expected_length = phone_info['length']

                # Remove any spaces or '-' in the mobile number
                cleaned_mobile = re.sub(r'[\s-]+', '', partner.mobile)

                # Ensure the mobile number starts with '+'
                cleaned_mobile = re.sub(r'^\+*', '+', cleaned_mobile)

                # Check if the mobile number starts with the country phone code
                if not cleaned_mobile.startswith(f'+{phone_code}'):
                    raise models.ValidationError(
                        f'Mobile number must start with the country phone code +{phone_code} for {country_name}.')

                # Extract the digits after the country code
                mobile_number_without_code = cleaned_mobile[len(f'+{phone_code}'):]

                # Check if the length of the mobile number after the country code matches the expected length

                if country_name == 'Lebanon' and len(mobile_number_without_code) == 7:
                    pass
                elif len(mobile_number_without_code) not in expected_length:
                    raise models.ValidationError(
                        f'Mobile number for {country_name} must be {expected_length} digits long after the country code.')

                # Ensure the remaining part is all digits
                if not mobile_number_without_code.isdigit():
                    raise models.ValidationError(
                        f'Mobile number for {country_name} must contain only digits after the country code.')




