# -*- coding: utf-8 -*-
#############################################################################
#############################################################################

{
    'name': "Create SQL Scripts for Encrypt and Decrypt  Personal Information",
    'version': '16.0.1.0.0',
    'summary': """Generate scripts to encrypt and decrypt Personal Information""",
    'description': """This module has been developed for creating sripts to encrypt and decrypt
                    Personal Information""",
    'author': "Guilherme Marcondes",
    'maintainer': 'Guilherme Marcondes, guilhermemarcondes4@msn.com',
    'category': 'Tools',
    'data': [
        'security/ir.model.access.csv',
        'views/encrypt_pi.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
    "images": ["images/screen.png"],
}
