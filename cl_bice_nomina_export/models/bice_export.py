import base64
from odoo import models
from odoo.exceptions import UserError
from datetime import datetime
import unicodedata
import re  # <-- asegúrate de tener este import también

def clean_reference(text):
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    text = re.sub(r'[^A-Za-z0-9]', '', text)
    return text[:15].ljust(15)

class AccountBatchPayment(models.Model):
    _inherit = 'account.batch.payment'

    def export_bice_proveedores_file(self):
        self.ensure_one()
        export_lines = []

        for payment in self.payment_ids:
            partner = payment.partner_id

            if not partner.vat:
                raise UserError(f"El proveedor {partner.name} no tiene RUT configurado.")

            if not partner.bank_ids:
                raise UserError(f"El proveedor {partner.name} no tiene cuenta bancaria configurada.")

            bank_account = partner.bank_ids[0]

            # Nombre Titular: hasta 40 caracteres, sin tildes, guiones ni puntos
            name = partner.name or ''
            name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
            name = name.replace('.', '').replace('-', '').upper()[:40].ljust(40)

            # RUT Titular: sin puntos ni guion
            rut = partner.vat.replace('.', '').replace('-', '')[:11]

            # Monto sin ceros a la izquierda
            amount = str(int(round(payment.amount)))

            # Cuenta Titular: hasta 17 caracteres
            account_number = bank_account.acc_number[:17].rjust(17) if bank_account.acc_number else ''.rjust(17)

            # Código Banco (SBIF)
            bank_code = (
                bank_account.bank_id.l10n_cl_sbif_code
                if bank_account.bank_id and bank_account.bank_id.l10n_cl_sbif_code
                else '000'
            )
            bank_code = str(int(bank_code))

            # Tipo de cuenta desde campo personalizado
            raw_account_type = bank_account.x_studio_tipo_de_cuenta or ''
            account_type_map = {
                'Cuenta Corriente': '3',
                'Cuenta Vista': '1',
                'Cuenta de ahorro': '2',
                'Cuenta RUT': '3',
            }
            account_type = account_type_map.get(raw_account_type, '3').zfill(1)

            # Moneda (fijo)
            currency = '0'

            # Oficinas (fijo)
            office_origin = '1'
            office_destiny = '1'

            # Referencia (factura, etc): hasta 15 caracteres # 
            ref = clean_reference(payment.ref or '')

            # Email (opcional): hasta 50 caracteres
            email = (partner.email or '').strip()[:50].ljust(50)

            # Línea completa con separador ";"
            line = ";".join([
                name,
                rut,
                account_number,
                amount,
                bank_code,
                account_type,
                currency,
                office_origin,
                office_destiny,
                ref,
                email
            ])
            export_lines.append(line)

        # Ensamblar CSV sin encabezado, con \r\n
        output = "\r\n".join(export_lines) + "\r\n"
        filename = f"{datetime.now().strftime('%Y%m%d')}_Proveedores.csv"
        export_file = base64.b64encode(output.encode('latin-1'))

        wizard = self.env['bice.export.wizard'].create({
            'file_data': export_file,
            'file_name': filename,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content/?model=bice.export.wizard&id={wizard.id}&field=file_data&filename_field=file_name&download=true",
            'target': 'new',
        }
