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
from findatapy.timeseries import Calculations

from findatapy.util.loggermanager import LoggerManager

logger = LoggerManager().getLogger(__name__)

chart = Chart(engine="plotly")
market = Market(market_data_generator=MarketDataGenerator())
calculations = Calculations()

# Choose run_example = 0 for everything
# run_example = 1 - create daily total return indices from FX spot data +
# deposit for AUDJPY, and compare
# run_example = 2 - create intraday total return indices from FX spot data +
# deposit for GBPUSD, and compare with daily

run_example = 0

from finmarketpy.curve.fxspotcurve import FXSpotCurve

# Create total return indices plot for AUDJPY (from perspective of a USD investor)
# Compare with AUDJPY FX spot and BBG constructed AUDJPY total return indices
if run_example == 1 or run_example == 0:
    # Get AUDJPY total returns from perspective of USD investor (via AUDUSD &
    # JPYUSD and AUD, USD & JPY overnight deposit rates)
    md_request = MarketDataRequest(start_date="01 Jan 1999",
                                   finish_date="01 Dec 2020",
                                   data_source="bloomberg", cut="NYC",
                                   category="fx",
                                   tickers=["AUDJPY"],
                                   cache_algo="cache_algo_return",
                                   abstract_curve=FXSpotCurve(
                                       construct_via_currency="USD",
                                       depo_tenor="ON"))

    df_tot = market.fetch_market(md_request=md_request)
    df_tot.columns = [x + "-tot-cuemacro" for x in df_tot.columns]

    # Get spot data
    md_request.abstract_curve = None

    df_spot = market.fetch_market(md_request=md_request)
    df_spot.columns = [x + "-spot" for x in df_spot.columns]

    # Get Bloomberg calculated total return indices (for spot)
    md_request.category = "fx-tot"

    df_bbg_tot = market.fetch_market(md_request)
    df_bbg_tot.columns = [x + "-bbg" for x in df_bbg_tot.columns]

    # Get Bloomberg calculated total return indices (for 1M forwards rolled)
    md_request.category = "fx-tot-forwards"

    df_bbg_tot_forwards = market.fetch_market(md_request)
    df_bbg_tot_forwards.columns = [x + "-bbg" for x in
                                   df_bbg_tot_forwards.columns]

    # Combine into a single data frame and plot, we note that the Cuemacro
    # constructed indices track the Bloomberg indices relatively well (both
    # from spot and 1M forwards). Also note the large difference with spot indices
    # CAREFUL to fill down, before reindexing because 1M forwards indices are
    # likely to have different publishing dates
    df = calculations.join([df_tot, df_bbg_tot, df_spot, df_bbg_tot_forwards],
                           how="outer").fillna(method="ffill")
    df = calculations.create_mult_index_from_prices(df)

    chart.plot(df)

# Create total return indices plot for GBPUSD with intraday and daily data
# (from perspective of a USD investor)
# Compare intraday and daily total return indices
if run_example == 2 or run_example == 0:
    import pytz

    # Get GBPUSD total returns from perspective of USD investor (via GBP and USD rates)
    md_request = MarketDataRequest(start_date="01 Jan 2019",
                                   finish_date="01 Jul 2019",
                                   data_source="bloomberg", cut="NYC",
                                   category="fx",
                                   tickers=["GBPUSD"],
                                   cache_algo="cache_algo_return",
                                   abstract_curve=FXSpotCurve(
                                       construct_via_currency="USD",
                                       depo_tenor="ON"))

    df_tot = market.fetch_market(md_request=md_request)
    df_tot.columns = [x + "-tot-cuemacro" for x in df_tot.columns]
    df_tot = df_tot.tz_localize(pytz.utc)
    df_tot.index = df_tot.index + pd.Timedelta(
        hours=22)  # Roughly NY close 2200 GMT

    md_request.abstract_curve = None

    # Get intraday spot data
    md_request.freq = "tick"
    md_request.data_source = "dukascopy"

    df_intraday_spot = market.fetch_market(md_request=md_request)
    df_intraday_spot = pd.DataFrame(
        df_intraday_spot.resample("1min").last().dropna())

    # Get Bloomberg calculated total return indices (for spot)
    md_request.category = "fx-tot"
    md_request.freq = "daily"
    md_request.data_source = "bloomberg"

    df_bbg_tot = market.fetch_market(md_request)
    df_bbg_tot.columns = [x + "-bbg" for x in df_bbg_tot.columns]
    df_bbg_tot = df_bbg_tot.tz_localize(pytz.utc)
    df_bbg_tot.index = df_bbg_tot.index + pd.Timedelta(
        hours=22)  # Roughly NY close 2200 GMT

    md_request = MarketDataRequest(start_date="01 Jan 2019",
                                   finish_date="01 Jul 2019",
                                   data_source="bloomberg", cut="NYC",
                                   category="base-depos",
                                   tickers=["GBPON", "USDON"],
                                   cache_algo="cache_algo_return")

    # Join daily deposit data with intraday spot data
    # OK to fill down, because deposit data isn"t very volatile
    df_deposit_rates = market.fetch_market(md_request).tz_localize(pytz.utc)

    df_intraday_market = df_intraday_spot.join(df_deposit_rates, how="left")
    df_intraday_market = df_intraday_market.fillna(method="ffill").fillna(
        method="bfill")

    df_intraday_tot = FXSpotCurve().construct_total_return_index(
        "GBPUSD", df_intraday_market, depo_tenor="ON")

    df_intraday_spot.columns = [x + "-intraday-spot" for x in
                                df_intraday_spot.columns]
    df_intraday_tot.columns = [x + "-intraday-tot" for x in
                               df_intraday_spot.columns]

    # Combine into a single data frame and plot
    df = calculations.join(
        [df_bbg_tot, df_tot, df_intraday_tot, df_intraday_spot],
        how="outer").fillna(method="ffill")
    df = calculations.create_mult_index_from_prices(df)

    chart.plot(df)
