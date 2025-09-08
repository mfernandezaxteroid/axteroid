import base64
from odoo import models, fields, api
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

            # RUT: sin puntos ni guion, hasta 11 caracteres
            rut = partner.vat.replace('.', '').replace('-', '').zfill(11)

            # Nombre Titular: hasta 40 caracteres, sin puntos, guiones ni tildes
            name = (partner.name or '').replace('.', '').replace('-', '')[:40].ljust(40)

            # Cuenta Titular: hasta 17 caracteres, derecha con espacios
            bank_account = partner.bank_ids[:1]
            account_number = (bank_account.acc_number or '').rjust(17) if bank_account else ''.rjust(17)

            # Monto: hasta 11 dígitos enteros, sin separadores ni decimales
            amount = str(int(payment.amount)).zfill(11)

            # Banco: código SBIF, hasta 3 caracteres, usar '000' si no hay
            bank_code = bank_account.bank_id.l10n_cl_sbif_code if bank_account and bank_account.bank_id and bank_account.bank_id.l10n_cl_sbif_code else '000'
            bank_code = bank_code.zfill(3)

            # Tipo de cuenta: '1'=vista, '2'=ahorro, '3'=corriente/rut
            account_type = partner.account_type or '1'
            account_type = account_type.zfill(1)

            # Moneda, Origen y Destino: siempre fijos
            currency_code = '0'
            office_origin = '1'
            office_dest = '1'

            # Factura (campo obligatorio): hasta 15 caracteres
            invoice_ref = (payment.ref or 'FACTURA').replace(' ', '')[:15].ljust(15)

            # Mail beneficiario (opcional): hasta 50 caracteres
            email = (partner.email or '').ljust(50)

            # Construcción de línea CSV con todos los campos separados por coma
            line = ','.join([
                name.strip(),
                rut.strip(),
                account_number.strip(),
                amount.strip(),
                bank_code.strip(),
                account_type.strip(),
                currency_code,
                office_origin,
                office_dest,
                invoice_ref.strip(),
                email.strip(),
            ])

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
