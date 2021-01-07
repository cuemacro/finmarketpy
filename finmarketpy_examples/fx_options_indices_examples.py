__author__ = 'saeedamen'

#
# Copyright 2020 Cuemacro
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
Shows how to use finmarketpy to total return indices for FX vanilla options (uses FinancePy underneath), so we can 
see the historical P&L from for example, rolling a 1M call option etc.

Note, you will need to have a Bloomberg terminal (with blpapi Python library) to download the FX market data in order
to generate the FX option prices, which are used underneath (FX spot, FX forwards, FX implied volatility quotes and deposit rates)
"""

import pandas as pd

# For plotting
from chartpy import Chart, Style

# For loading market data
from findatapy.market import Market, MarketDataGenerator, MarketDataRequest

from findatapy.timeseries import Filter, Calculations

from findatapy.util.loggermanager import LoggerManager

from finmarketpy.curve.fxoptionscurve import FXOptionsCurve
from finmarketpy.curve.volatility.fxvolsurface import FXVolSurface
from finmarketpy.curve.volatility.fxoptionspricer import FXOptionsPricer

logger = LoggerManager().getLogger(__name__)

chart = Chart(engine='plotly')
market = Market(market_data_generator=MarketDataGenerator())

# Choose run_example = 0 for everything
# run_example = 1 - create total return index AUDUSD 1M calls

run_example = 1

###### Fetch market data for pricing AUDUSD options in 2007 (ie. FX spot, FX forwards, FX deposits and FX vol quotes)
###### Construct volatility surface using FinancePy library underneath, using polynomial interpolation
###### Enters a 1M call, and MTM every day, and at expiry rolls into another 1M call
if run_example == 1 or run_example == 0:

    # start_date = '01 Jan 2004'; finish_date = '31 Dec 2008'
    start_date = '01 Jan 2007'; finish_date = '31 Dec 2007' # Use smaller window for quicker execution

    cross = 'AUDUSD'
    fx_options_trading_tenor = '1M'

    # Download the whole all market data for AUDUSD for pricing options (FX vol surface + spot + FX forwards + depos)
    md_request = MarketDataRequest(start_date=start_date, finish_date=finish_date,
                                   data_source='bloomberg', cut='BGN', category='fx-vol-market',
                                   tickers=cross,
                                   cache_algo='cache_algo_return', base_depos_currencies=[cross[0:3], cross[3:6]])

    df = market.fetch_market(md_request)
    df = df.fillna(method='ffill')

    # Remove New Year's Day and Christmas
    df = Filter().filter_time_series_by_holidays(df, cal='FX')

    # In case any missing values fill down (particularly can get this for NDFs)
    df_market = market.fetch_market(md_request=md_request).fillna(method='ffill')

    # We want to roll long 1M ATM call at expiry
    # We'll mark to market the price through the month by interpolating between 1W and 1M (and using whole vol curve
    # at each tenor)
    fx_options_curve = FXOptionsCurve(fx_options_trading_tenor=fx_options_trading_tenor,
        roll_days_before=0,
        roll_event='expiry-date',
        roll_months=1,
        fx_options_tenor_for_interpolation=['1W', '1M'],
        strike='atm',
        contract_type='european-call',
        position_multiplier=1.0,
        output_calculation_fields=True)

    # Let's trade a long 1M call, and we roll at expiry
    df_cuemacro_option_call_tot = fx_options_curve.construct_total_return_index(cross, df)

    # Add transaction costs to the option index (bid/ask bp for the option premium and spot FX)
    df_cuemacro_option_call_tc = fx_options_curve.apply_tc_to_total_return_index(cross, df_cuemacro_option_call_tot,
                                                                            option_tc_bp=5, spot_tc_bp=2)

    # Let's trade a short 1M put, and we roll at expiry
    df_cuemacro_option_put_tot = fx_options_curve.construct_total_return_index(
        cross, df, contract_type='european-put', position_multiplier=-1.0)

    # Add transaction costs to the option index (bid/ask bp for the option premium and spot FX)
    df_cuemacro_option_put_tc = fx_options_curve.apply_tc_to_total_return_index(cross, df_cuemacro_option_put_tot,
                                                                                 option_tc_bp=5, spot_tc_bp=2)

    # Get total returns for spot
    md_request.abstract_curve = None

    # Get Bloomberg calculated total return indices (for spot)
    md_request.category = 'fx-tot'
    md_request.cut = 'NYC'

    df_bbg_tot = market.fetch_market(md_request)
    df_bbg_tot.columns = [x + '-bbg' for x in df_bbg_tot.columns]

    calculations = Calculations()

    def prepare_indices(df_tot, df_tc, df_spot_tot):
        df = calculations.pandas_outer_join([pd.DataFrame(df_tot[cross + '-option-tot.close']),
                                             pd.DataFrame(df_tot[cross + '-option-delta-tot.close']),
                                             pd.DataFrame(df_tc[cross + '-option-tot-with-tc.close']),
                                             pd.DataFrame(df_tc[cross + '-option-delta-tot-with-tc.close']),
                                             pd.DataFrame(df_tot[cross + '-delta-pnl-index.close']),
                                             pd.DataFrame(df_tc[cross + '-delta-pnl-index-with-tc.close']),
                                             df_spot_tot]).fillna(method='ffill')

        return calculations.create_mult_index_from_prices(df)

    chart.plot(calculations.create_mult_index_from_prices(
        prepare_indices(df_cuemacro_option_call_tot, df_cuemacro_option_call_tc, df_bbg_tot)))

    chart.plot(calculations.create_mult_index_from_prices(
        prepare_indices(df_cuemacro_option_put_tot, df_cuemacro_option_put_tc, df_bbg_tot)))