__author__ = 'saeedamen'  # Saeed Amen

#
# Copyright 2016-2020 Cuemacro - https://www.cuemacro.com / @cuemacro
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
Shows how to use finmarketpy to create total return indices for FX spot (ie. calculates spot returns + carry returns)
"""

# For plotting
from chartpy import Chart, Style

# For loading market data
from findatapy.market import Market, MarketDataGenerator, MarketDataRequest
from findatapy.timeseries import Calculations

from findatapy.util.loggermanager import LoggerManager

logger = LoggerManager().getLogger(__name__)

chart = Chart(engine='plotly')
market = Market(market_data_generator=MarketDataGenerator())
calculations = Calculations()

# Choose run_example = 0 for everything
# run_example = 1 - create total return indices from FX spot data + deposit for AUDJPY, and compare

run_example = 0

from finmarketpy.curve.fxspotcurve import FXSpotCurve

###### Create total return indices plot for AUDJPY (from perspective of a USD investor)
###### Compare with AUDJPY FX spot and BBG constructed AUDJPY total return indices
if run_example == 1 or run_example == 0:

    # Get AUDJPY total returns from perspective of USD investor (via AUDUSD & JPYUSD and AUD, USD & JPY overnight deposit rates)
    md_request = MarketDataRequest(start_date='01 Jan 1999', finish_date='01 Dec 2020',
                                   data_source='bloomberg', cut='NYC', category='fx',
                                   tickers=['AUDJPY'],
                                   cache_algo='cache_algo_return',
                                   abstract_curve=FXSpotCurve(construct_via_currency='USD', depo_tenor='ON'))

    df_tot = market.fetch_market(md_request=md_request)
    df_tot.columns = [x + '-tot-cuemacro' for x in df_tot.columns]

    # Get spot data
    md_request.abstract_curve = None

    df_spot = market.fetch_market(md_request=md_request)
    df_spot.columns = [x + '-spot' for x in df_spot.columns]

    # Get Bloomberg calculated total return indices (for spot)
    md_request.category = 'fx-tot'

    df_bbg_tot = market.fetch_market(md_request)
    df_bbg_tot.columns = [x + '-bbg' for x in df_bbg_tot.columns]

    # Get Bloomberg calculated total return indices (for 1M forwards rolled)
    md_request.category = 'fx-tot-forwards'

    df_bbg_tot_forwards = market.fetch_market(md_request)
    df_bbg_tot_forwards.columns = [x + '-bbg' for x in df_bbg_tot_forwards.columns]

    # Combine into a single data frame and plot, we note that the Cuemacro constructed indices track the Bloomberg
    # indices relatively well (both from spot and 1M forwards). Also note the large difference with spot indices
    # CAREFUL to fill down, before reindexing because 1M forwards indices are likely to have different publishing dates
    df = calculations.pandas_outer_join([df_tot, df_bbg_tot, df_spot, df_bbg_tot_forwards]).fillna(method='ffill')
    df = calculations.create_mult_index_from_prices(df)

    chart.plot(df)