import base64
import csv
import io
from odoo import models
from odoo.exceptions import UserError
from datetime import datetime


class AccountBatchPayment(models.Model):
    _inherit = 'account.batch.payment'

    def export_bice_proveedores_file(self):
        self.ensure_one()

        output_buffer = io.StringIO()
        writer = csv.writer(output_buffer, delimiter=';', quoting=csv.QUOTE_MINIMAL, lineterminator='\r\n')

        for payment in self.payment_ids:
            partner = payment.partner_id

            if not partner.vat:
                raise UserError(f"El proveedor {partner.name} no tiene RUT configurado.")

            rut = partner.vat.replace('.', '').replace('-', '').zfill(10)
            name = partner.name or ''
            amount = str(int(payment.amount))
            bank_account = partner.bank_ids and partner.bank_ids[0] or False
            account_number = bank_account.acc_number if bank_account else ''
            bank_code = bank_account.bank_id.l10n_cl_sbif_code if bank_account and bank_account.bank_id else '000'
            account_type = getattr(bank_account, 'x_studio_tipo_de_cuenta', 'Cuenta Corriente') if bank_account else 'Cuenta Corriente'
            currency = '0'
            office_origin = '1'
            office_dest = '1'
            ref = payment.ref or ''
            email = partner.email or ''
            extra = ''  # Campo en blanco final

            writer.writerow([
                name,
                rut,
                account_number,
                amount,
                bank_code,
                account_type,
                currency,
                office_origin,
                office_dest,
                ref,
                email,
                extra
            ])

        export_file = base64.b64encode(output_buffer.getvalue().encode('utf-8'))
        filename = f"nomina_bice_proveedores_{datetime.now().strftime('%Y%m%d')}.csv"

        wizard = self.env['bice.export.wizard'].create({
            'file_data': export_file,
            'file_name': filename,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content/?model=bice.export.wizard&id={wizard.id}&field=file_data&filename_field=file_name&download=true",
            'target': 'new',
        }
