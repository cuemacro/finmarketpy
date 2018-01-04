__author__ = 'saeedamen' # Saeed Amen

#
# Copyright 2016 Cuemacro
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the
# License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the License for the specific language governing permissions and limitations under the License.
#

"""
MarketConstants

Has various constants required for the finmarketpy project. These have been defined as static variables.

"""

class MarketConstants(object):

    hdf5_file_econ_file = "x"
    db_database_econ_file = ''
    db_server = '127.0.0.1'
    db_username = 'admin_root'
    db_password = 'TOFILL'

    write_engine = 'arctic'

    # overwrite field variables with those listed in MarketCred
    def __init__(self):
        try:
            from finmarketpy.util.marketcred import MarketCred
            cred_keys = MarketCred.__dict__.keys()

            for k in MarketConstants.__dict__.keys():
                if k in cred_keys and '__' not in k:
                    setattr(MarketConstants, k, getattr(MarketCred, k))
        except:
            pass