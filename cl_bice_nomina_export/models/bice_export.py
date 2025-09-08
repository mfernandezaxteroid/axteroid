import base64
from odoo import models
from odoo.exceptions import UserError
from datetime import datetime


class AccountBatchPayment(models.Model):
    _inherit = 'account.batch.payment'

    def export_bice_proveedores_file(self):
        self.ensure_one()

        export_lines = []

        for payment in self.payment_ids:
            partner = payment.partner_id

            if not partner.vat:
                raise UserError(f"El proveedor {partner.name} no tiene RUT configurado.")

            rut = partner.vat.replace('.', '').replace('-', '').zfill(10)

            name = partner.name[:40].ljust(40)

            amount = str(int(payment.amount)).zfill(13)

            bank_account = partner.bank_ids and partner.bank_ids[0] or False

            account_number = bank_account.acc_number.rjust(20) if bank_account and bank_account.acc_number else ''.rjust(20)

            bank_code = (
                bank_account.bank_id.l10n_cl_sbif_code
                if bank_account and bank_account.bank_id and bank_account.bank_id.l10n_cl_sbif_code
                else '000'
            )
            bank_code = bank_code.zfill(3)

            # Mapear tipo de cuenta desde el campo personalizado
            raw_account_type = bank_account.x_studio_tipo_de_cuenta if bank_account else ''
            account_type_map = {
                'Cuenta Corriente': '1',
                'Cuenta Vista': '2',
                'Cuenta de ahorro': '3',
                'Cuenta RUT': '3',
            }
            account_type = account_type_map.get(raw_account_type, '1').zfill(2)

            email = (partner.email or '').ljust(50)
            ref = (payment.ref or '').ljust(40)
            process_date = datetime.now().strftime('%d%m%Y')

            line = (
                rut +
                name +
                amount +
                account_number +
                bank_code +
                account_type +
                email +
                ref +
                process_date
            )

            export_lines.append(line)

        output = "\r\n".join(export_lines) + "\r\n"
        filename = f"nomina_bice_proveedores_{datetime.now().strftime('%Y%m%d')}.csv"
        export_file = base64.b64encode(output.encode('utf-8'))

        wizard = self.env['bice.export.wizard'].create({
            'file_data': export_file,
            'file_name': filename,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content/?model=bice.export.wizard&id={wizard.id}&field=file_data&filename_field=file_name&download=true",
            'target': 'new',
        }
