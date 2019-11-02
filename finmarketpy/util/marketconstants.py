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
    import platform

    ###### SETUP ENVIRONMENT VARIABLES ######
    plat = str(platform.platform()).lower()

    if 'linux' in plat: 
        generic_plat = 'linux'
    elif 'windows' in plat: 
        generic_plat = 'windows'
    elif 'darwin' in plat: 
        generic_plat = 'mac'

    # "thread" or "multiprocessing" (experimental!) library to use when backtesting
    backtest_thread_technique = "multiprocessing"

    multiprocessing_library = 'multiprocess'  # 'multiprocessing_on_dill' or 'multiprocess' or 'multiprocessing' or 'pathos'

    # how many threads to use for backtesting (don't do too many on slow machines!)
    # also some data sources will complain if you start too many parallel threads to call data!
    # for some data providers might get better performance from 1 thread only!
    backtest_thread_no = {'linux': 8,
                          'windows' : 1,
                          'mac' : 8}

    hdf5_file_econ_file = "x"

    db_database_econ_file = ''
    db_server = '127.0.0.1'
    db_port = '27017'

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