#!/usr/bin/python
# (C) Copyright IBM Corp. 2023
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""


|-----------------------------------------------------------------------|
|                        History of Changes                             |
|-----------------------------------------------------------------------|
|       Author        |           Date            |         Reason      |
|---------------------+---------------------------+---------------------|
|Guilherme Marcondes  | August 09, 2023           | Initial Commit      |
|-----------------------------------------------------------------------|
"""

from odoo import api, fields, models, _
import logging
import pandas as pd
from RandomWordGenerator import RandomWord
import base64
import xlrd
import os
import tempfile
from datetime import datetime
from odoo.exceptions import UserError

__author__ = "Guilherme Marcondes"
__copyright__ = "Copyright 2023"
__credits__ = ["Guilherme Marcondes"]
__license__ = "AGPL-3"
__version__ = "16.0.1.0.1"
__maintainer__ = "Guilherme Marcondes"
__email__ = "guilhermemarcondes4@msn.com"
__status__ = "Prototype"
_logger = logging.getLogger(__name__)


DOMAIN_TEMPLATE = "[('model_id', '=', model_data_id)]"

class EncryptPI(models.Model):
    """Class to get MQ parameters from a properties file."""

    _name = 'encrypt.pi'
    _description = 'Create Encrypt and Decrypy scripts'

    model_data_id = fields.Many2one('ir.model', string="Model Data")
    field_name = fields.Many2one(
        'ir.model.fields', string='Date Field', help='The date to use for the time period evaluated',
        domain=DOMAIN_TEMPLATE
    )

    def create_sql_script(self):
        try:
            mytempdir = tempfile.mkdtemp(prefix="encrypt_sql-")
            file_name_encrypt = mytempdir+os.path.sep+"encrypt.sql"
            file_name_decrypt = mytempdir+os.path.sep+"decrypt.sql"
            message_encrypt = 'create extension pgcrypto;'+'\n'
            message_decrypt = 'create extension pgcrypto;'+'\n'
            for obj in self:
                model_var = obj.model_data_id.model.replace('.', '_')
                alter_table = "alter table %s add column crypted_%s varchar;" % (model_var,obj.field_name.name)
                crypt_command = "update %s set crypted_%s = pgp_sym_encrypt(%s , 'password_change_me');" % (model_var,obj.field_name.name,
                                                                                                            obj.field_name.name)
                empty_column = "update %s set %s = '';" % (model_var,obj.field_name.name)
                message_encrypt = message_encrypt + alter_table+'\n' + crypt_command +'\n' + empty_column +'\n'

                decrypt_command = "update %s set %s = pgp_sym_decrypt(crypted_%s::BYTEA, 'password_change_me');" % \
                                  (model_var,obj.field_name.name,obj.field_name.name)
                drop_table = "alter table %s drop column crypted_%s;" % (model_var,obj.field_name.name)

                message_decrypt = message_decrypt + decrypt_command+'\n' + drop_table +'\n'

            f = open(file_name_encrypt, "w")
            f.write(message_encrypt)
            file_2 = open(file_name_decrypt, "w")
            file_2.write(message_decrypt)
            f.close()
            file_2.close()
            _logger.info('"Encrypt and Decrypt script were created succcessfully on path %s', mytempdir)
        except Exception as e:
            err = "Unable to Run the create the SQL scripts due " % str(e)
            raise UserError(err)
