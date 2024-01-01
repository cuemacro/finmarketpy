__author__ = "saeedamen"

#
# Copyright 2020 Cuemacro
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.
#


"""
Shows how to use finmarketpy to create total return indices for FX spot (ie. 
calculates spot returns + carry returns)
"""

import pandas as pd

# For plotting
from chartpy import Chart, Style

# For loading market data
from findatapy.market import Market, MarketDataGenerator, MarketDataRequest
from findatapy.timeseries import Calculations, Calendar

from findatapy.util.loggermanager import LoggerManager

logger = LoggerManager().getLogger(__name__)

chart = Chart(engine='plotly')
market = Market(market_data_generator=MarketDataGenerator())
calculations = Calculations()

# Choose run_example = 0 for everything
# run_example = 1 - get forwards prices for AUDUSD interpolated for an odd date/broken date
# run_example = 2 - get implied deposit rate

run_example = 0

from finmarketpy.curve.rates.fxforwardspricer import FXForwardsPricer

###### Value forwards for AUDUSD for odd days
if run_example == 1 or run_example == 0:

    cross = 'AUDUSD'
    fx_forwards_tenors = ['1W', '2W', '3W', '1M']

    fx_forwards_to_print = ['1W', '2W']

    # Get AUDUSD data for spot, forwards + depos
    md_request = MarketDataRequest(start_date='01 Jan 2020', finish_date='01 Feb 2020',
                                   data_source='bloomberg', cut='NYC', category='fx-forwards-market',
                                   tickers=cross,
                                   cache_algo='cache_algo_return', fx_forwards_tenor=fx_forwards_tenors,
                                   base_depos_currencies=[cross[0:3], cross[3:6]])

    market_df = market.fetch_market(md_request=md_request)

    fx_forwards_price = FXForwardsPricer()

    delivery_dates = Calendar().get_delivery_date_from_horizon_date(market_df.index, "8D", cal=cross)
    interpolated_forwards_df = fx_forwards_price.price_instrument(cross, market_df.index, delivery_dates,
        market_df=market_df, fx_forwards_tenor_for_interpolation =['1W', '2W'])

    interpolated_forwards_df[cross + ".delivery"] = delivery_dates.values

    print(interpolated_forwards_df)

    market_cols = [cross + ".close"]

    for f in fx_forwards_to_print:
        market_cols.append(cross + f + '.close')

    print(market_df[market_cols])

if run_example == 2 or run_example == 0:

    cross = 'AUDUSD'
    fx_forwards_tenors = ['1W', '2W', '3W', '1M']
    fx_forwards_to_print = ['1M']

    # Get AUDUSD data for forwards (spot, forwards points and base depos)
    md_request = MarketDataRequest(start_date='01 Jan 2020', finish_date='01 Feb 2020',
                                   data_source='bloomberg', cut='NYC', category='fx-forwards-market',
                                   tickers=cross,
                                   cache_algo='cache_algo_return', fx_forwards_tenor=fx_forwards_tenors,
                                   base_depos_tenor=fx_forwards_tenors,
                                   base_depos_currencies=[cross[0:3], cross[3:6]])

    market_df = market.fetch_market(md_request=md_request)

    fx_forwards_price = FXForwardsPricer()

    implied_depo_df = fx_forwards_price.calculate_implied_depo(cross, 'AUD', market_df=market_df,
                               fx_forwards_tenor=fx_forwards_tenors,
                               depo_tenor='1M')

    print(implied_depo_df)

    market_cols = [cross + ".close"]

    for f in fx_forwards_to_print:
        market_cols.append(cross + f + '.close')

    market_cols.append("USD1M.close")
    print(market_df[market_cols])

    # Download implied deposits (via FX forwards) for base currency (AUD) from Bloomberg
    # Note: some implied deposits tenors might have no data in it
    tickers = []

    for t in fx_forwards_tenors:
        tickers.append(cross[0:3] + "I" + t)

    md_request = MarketDataRequest(start_date='01 Jan 2020', finish_date='01 Feb 2020',
                                   data_source='bloomberg', cut='NYC',
                                   tickers=tickers,
                                   vendor_tickers= [x + " CMPN Curncy" for x in tickers],
                                   cache_algo='cache_algo_return')

    implied_depo_bbg_df = market.fetch_market(md_request=md_request)

    chart.plot(calculations.join([implied_depo_bbg_df, implied_depo_df]), how='outer')

