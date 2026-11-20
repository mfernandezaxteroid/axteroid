# -*- coding: utf-8 -*-
{
    'name': 'Integración con app Piriod',
    'version': '19.0.1.0.0',
    'author': 'Open Solutions',
    'description': """
Integración con app Piriod
======================================================
 """,
    'license': 'OPL-1',
    'website': 'https://www.opens.cl',
    'depends': ['account','l10n_cl','l10n_latam_invoice_document'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_company_view.xml',
        #'views/res_config_view.xml'
        ],
    'installable': True,
    'application': True,
    'auto_install': False,
}