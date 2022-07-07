import base64

from odoo import fields, models
import requests
import logging
import hashlib
import hmac

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    piriod_id = fields.Char(string='ID de la factura piriod')
    piriod_pdf_invoice = fields.Binary(string='PDF de la factura piriod')

    def get_piriod_invoice(self, piriod_invoice_id):
        companys = self.env['res.company'].sudo().search([])
        for company in companys:
            api = company.piriod_connection_url
            token = company.token
            organization = company.organization_id
        credentials = {
            'Authorization': f'Token {token}',
            'x-simple-workspace': f'{organization}'
        }
        _logger.info(token)
        r = requests.get(f'{api}/invoices/{piriod_invoice_id}/', headers=credentials)
        return r

    def get_piriod_invoice_pdf(self, piriod_invoice_id):
        companys = self.env['res.company'].sudo().search([])
        for company in companys:
            api = company.piriod_connection_url
            token = company.token
            organization = company.organization_id
        credentials = {
            'Authorization': f'Token {token}',
            'x-simple-workspace': f'{organization}'
        }
        r = requests.get(f'{api}/invoices/{piriod_invoice_id}/pdf/', headers=credentials)
        return r

    def get_piriod_invoice_xml(self, invoice_json):
        companys = self.env['res.company'].sudo().search([])
        for company in companys:
            api = company.piriod_connection_url
            token = company.token
            organization = company.organization_id
        credentials = {
            'Authorization': f'Token {token}',
            'x-simple-workspace': f'{organization}'
        }
        return base64.b64encode(requests.get(invoice_json['local_file']).content)

    def signature_is_valid(self, piriod_signature):
        WH_SECRET = 'whsecret_q48kQSw4m3t5MvzOuJpk6MeLv6i3FLX2WFDsJBpRLWrIWgsLpEDoz43'
        if not WH_SECRET == piriod_signature:
            return False
        return True


    def create_piriod_invoice(self, invoice_json, invoice_pdf_json):  # , invoice_pdf_xml
        if invoice_json and invoice_pdf_json:
            odoo_partner = self.env['res.partner'].search([('name', '=', invoice_json["customer"]["name"])])
            if not odoo_partner:
                odoo_partner = self.env['res.partner'].create_piriod_customer(invoice_json["customer"])
            odoo_document = self.env['l10n_latam.document.type'].search([('code', '=', invoice_json["document"]["code"])])
            if not odoo_document:
                odoo_document = self.env['l10n_latam.document.type'].create_piriod_document(invoice_json["document"])
            lines = self.env['account.move.line'].create_piriod_lines(invoice_json["lines"])
            data = {
                'move_type':'out_invoice',
                'piriod_id': invoice_json["id"],
                'partner_id': odoo_partner.id,
                'invoice_date': invoice_json["date"],
                'invoice_date_due': invoice_json["due_date"],
                'currency_id': 45,
                'l10n_latam_document_type_id': odoo_document.id,
                'piriod_pdf_invoice': invoice_pdf_json["file"],
                'invoice_line_ids': lines
            }
            odoo_invoice = self.env['account.move'].sudo().create(data)
            folio_piriod_ext = invoice_json['number']
            new_name = odoo_invoice.sequence_prefix + str(folio_piriod_ext).zfill(6)
            odoo_invoice.write({'name': new_name, 'payment_reference': new_name, 'sequence_number': folio_piriod_ext})
            if odoo_invoice:
                # obtener pdf/xml
                print('d')
                invoice_json_id = invoice_json["id"]
                pdf_result = self.get_piriod_invoice_pdf(invoice_json_id)
                if pdf_result:
                    pdf_b64 = pdf_result.json()['file']
                    attachment_name_pdf = str(folio_piriod_ext) + ".pdf"
                    attachment_name_xml = str(folio_piriod_ext) + ".xml"
                    self.env['ir.attachment'].create({
                        'type': 'binary',
                        'name': attachment_name_pdf,
                        'res_model': 'account.move',
                        'datas': pdf_b64,
                        'res_id': odoo_invoice.id,
                    })
                    xml_b64 = self.get_piriod_invoice_xml(invoice_json)
                    self.env['ir.attachment'].create({
                        'type': 'binary',
                        'name': attachment_name_xml,
                        'res_model': 'account.move',
                        'datas': xml_b64,
                        'res_id': odoo_invoice.id,
                    })

            print(odoo_invoice.id)
        return odoo_invoice