__author__ = 'saeedamen'  # Saeed Amen

#
# Copyright 2016-2021 Cuemacro - https://www.cuemacro.com / @cuemacro
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the
# License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the License for the specific language governing permissions and limitations under the License.
#

class MarketConstants(object):
    """Has various constants required for the finmarketpy project. These have been defined as static variables.

    """
    import platform

    ###### SETUP ENVIRONMENT VARIABLES ######
    plat = str(platform.platform()).lower()

    if 'linux' in plat: 
        generic_plat = 'linux'
    elif 'windows' in plat: 
        generic_plat = 'windows'
    elif ('darwin' in plat or 'macos' in plat): 
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

    spot_depo_tenor = 'ON'

    currencies_with_365_basis =  ['AUD', 'CAD', 'GBP', 'NZD']

    # Whether to output additional fields related to calculation of total return indices
    output_calculation_fields = False

### FX Forwards ########################################################################################################
    fx_forwards_points_divisor_1 = ['IDR']
    fx_forwards_points_divisor_100 = ['JPY']
    fx_forwards_points_divisor_1000 = []

    # Forwards typically used for interpolation (note: eg. TN and SN are swaps)
    fx_forwards_tenor_for_interpolation = ["1W", "2W", "3W", "1M", "2M", "3M", "4M", "6M", "9M", "1Y", "2Y", "3Y", "5Y"]

    # What contract will we generally be trading?
    fx_forwards_trading_tenor = '1M'

    # When constructing total return index 'mult' or 'add'
    fx_forwards_cum_index = 'mult'

    # What is the point at which we roll?
    fx_forwards_roll_event = 'month-end' # 'month-end', 'quarter-end', 'year-end', 'delivery-date'

    # How many days before that point should we roll?
    fx_forwards_roll_days_before = 5

    # Typically when do we roll the contract?
    fx_forwards_roll_months = 1

### FX Options ########################################################################################################
    fx_options_points_divisor_100 = ['JPY']
    fx_options_points_divisor_1000 = []

    # Option tenors typically used for interpolation (note: eg. TN and SN are swaps)
    fx_options_tenor_for_interpolation = ["ON", "1W", "2W", "3W", "1M", "2M", "3M", "4M", "6M", "9M", "1Y"]#, "2Y", "3Y"]

    # What contract will we generally be trading?
    fx_options_trading_tenor = "1M"

    # When constructing total return index 'mult' or 'add'
    fx_options_cum_index = "mult"

    # For total return index use option price in base currency/for
    fx_options_index_premium_output = "pct-for"

    fx_options_index_strike = "atm"
    fx_options_index_contract_type = "european-call"

    fx_options_freeze_implied_vol = False

    # What is the point at which we roll?
    fx_options_roll_event = "expiry-date"  # 'month-end', 'expiry-date', 'no-roll'

    # How many days before that point should we roll?
    fx_options_roll_days_before = 5

    # Typically when do we roll the contract?
    fx_options_roll_months = 1

    # For fitting vol surface

    # 'CLARK5', 'CLARK', 'BBG', 'SABR' and 'SABR3'
    fx_options_vol_function_type = "CLARK5"
    fx_options_depo_tenor = "1M"

    # 'fwd-delta-neutral' or 'fwd-delta-neutral-premium-adj' or 'spot' or 'fwd'
    fx_options_atm_method = "fwd-delta-neutral-premium-adj"

    # 'fwd-delta' or 'fwd-delta-prem-adj' or 'spot-delta-prem-adj' or 'spot-delta'
    fx_options_delta_method = "spot-delta-prem-adj"
    fx_options_alpha = 0.5

    # 'pct-for' (in base currency pct) or 'pct-dom' (in terms currency pct)
    fx_options_premium_output = "pct-for"
    fx_options_delta_output = "pct-fwd-delta-prem-adj"

    # 'nelmer-mead' or 'nelmer-mead-numba' (faster but less accurate) or 'cg' (conjugate gradient tends to be slower, but more accurate)
    fx_options_solver = "nelmer-mead-numba"
    fx_options_pricing_engine = "financepy" # 'financepy' or 'finmarketpy'

    fx_options_tol = 1e-8

    override_fields = {}

    # Overwrite field variables with those listed in MarketCred or we can pass through an override_fields dictionary
    def __init__(self, override_fields={}):
        try:
            from finmarketpy.util.marketcred import MarketCred
            cred_keys = MarketCred.__dict__.keys()

            for k in MarketConstants.__dict__.keys():
                if k in cred_keys and '__' not in k:
                    setattr(MarketConstants, k, getattr(MarketCred, k))
        except:
            pass

        # Store overrided fields
        if override_fields == {}:
            override_fields = MarketConstants.override_fields
        else:
            MarketConstants.override_fields = override_fields

        for k in override_fields.keys():
            if '__' not in k:
                setattr(MarketConstants, k, override_fields[k])