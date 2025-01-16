# -*- coding: utf-8 -*-
#############################################################################
#############################################################################

{
    'name': "Add Edit Button Odoo V17",
    'version': '17.0',
    'summary': """This module add Edit button Odoo Version 17""",
    'description': """This module has been developed for add Edit Module Button
                   on Odoo V17""",
    'author': "Guilherme Marcondes",
    'maintainer': 'Guilherme Marcondes, guilhermemarcondes4@msn.com',
    'website': "https://github.com/guimarc/odoo-apps",
    'category': 'Tools',
    'data': [
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
    'assets': {
        'web.assets_backend': [
            'edit_button/static/src/views/form/form_controller.js',
            'edit_button/static/src/views/form/form_controller.xml',


        ],
    },
    "images": ["images/screen.png"],
}
