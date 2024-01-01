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
Shows how to use finmarketpy to create total return indices for FX forwards 
with appropriate roll rules
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
# run_example = 1 - creating USDBRL total return index rolling forwards and 
# compare with BBG indices
# run_example = 2 - creating AUDJPY (via AUDUSD and JPYUSD) total return index 
# rolling forwards & compare with BBG indices

run_example = 0

from finmarketpy.curve.fxforwardscurve import FXForwardsCurve

###### Create total return indices plot for USDBRL using forwards
# We shall be using USDBRL 1M forward contracts and rolling them 5 business
# days before month end
if run_example == 1 or run_example == 0:
    cross = "USDBRL"

    # Download more tenors
    fx_forwards_tenors = ["1W", "1M", "2M", "3M"]

    # Get USDBRL data for spot, forwards + depos
    md_request = MarketDataRequest(start_date="02 Jan 2007",
                                   finish_date="01 Jun 2007",
                                   data_source="bloomberg", cut="NYC",
                                   category="fx-forwards-market",
                                   tickers=cross,
                                   fx_forwards_tenor=fx_forwards_tenors,
                                   base_depos_currencies=[cross[0:3],
                                                          cross[3:6]],
                                   cache_algo="cache_algo_return")

    # In case any missing values fill down (particularly can get this for NDFs)
    df_market = market.fetch_market(md_request=md_request).fillna(
        method="ffill")

    fx_forwards_curve = FXForwardsCurve()

    # Let"s trade a 1M forward, and we roll 5 business days (based on both
    # base + terms currency holidays)
    # before month end
    df_cuemacro_tot_1M = fx_forwards_curve.construct_total_return_index(
        cross,
        df_market,
        fx_forwards_trading_tenor="1M",
        roll_days_before=5,
        roll_event="month-end",
        roll_months=1,
        fx_forwards_tenor_for_interpolation=fx_forwards_tenors,
        output_calculation_fields=True)

    df_cuemacro_tot_1M.columns = [
        x.replace("forward-tot", "forward-tot-1M-cuemacro") for x in
        df_cuemacro_tot_1M.columns]

    # Now do a 3M forward, and we roll 5 business days before end of quarter(
    # based on both base + terms currency holidays)
    # before month end
    df_cuemacro_tot_3M = fx_forwards_curve.construct_total_return_index(
        cross,
        df_market,
        fx_forwards_trading_tenor="3M",
        roll_days_before=5,
        roll_event="month-end",
        roll_months=3,
        fx_forwards_tenor_for_interpolation=fx_forwards_tenors,
        output_calculation_fields=True)

    df_cuemacro_tot_3M.columns = [
        x.replace("forward-tot", "forward-tot-3M-cuemacro") for x in
        df_cuemacro_tot_3M.columns]

    # Get spot data
    md_request.abstract_curve = None
    md_request.category = "fx"

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
    # constructed indices track the Bloomberg
    # indices relatively well (both from spot and forwards). Also note the large
    # difference with spot indices
    # CAREFUL to fill down, before reindexing because forwards indices are
    # likely to have different publishing dates
    df = calculations.join([pd.DataFrame(
        df_cuemacro_tot_1M[cross + "-forward-tot-1M-cuemacro.close"]),
                            pd.DataFrame(df_cuemacro_tot_3M[
                                             cross + "-forward-tot-3M-cuemacro.close"]),
                            df_bbg_tot, df_spot, df_bbg_tot_forwards],
                           how="outer").fillna(method="ffill")

    df = calculations.create_mult_index_from_prices(df)

    chart.plot(df)

###### Create total return indices plot for AUDJPY using the underlying USD
# legs (ie. AUDUSD & JPYUSD)
if run_example == 2 or run_example == 0:
    cross = "AUDJPY"

    # Download more tenors
    fx_forwards_tenors = ["1W", "1M", "2M", "3M"]

    # Parameters for how to construct total return indices, and the rolling rule
    # 1M forward contract, and roll it 5 working days before month end
    # We"ll be constructing our total return index from AUDUSD and JPYUSD
    fx_forwards_curve = FXForwardsCurve(
        fx_forwards_trading_tenor="1M",
        roll_days_before=5,
        roll_event="month-end",
        construct_via_currency="USD",
        fx_forwards_tenor_for_interpolation=fx_forwards_tenors,
        roll_months=1,
        output_calculation_fields=True)

    # Get AUDJPY (AUDUSD and JPYUSD) data for spot, forwards + depos and also
    # construct the total returns forward index
    md_request = MarketDataRequest(start_date="02 Jan 2007",
                                   finish_date="01 Jun 2007",
                                   data_source="bloomberg", cut="NYC",
                                   category="fx",
                                   tickers=cross,
                                   fx_forwards_tenor=fx_forwards_tenors,
                                   base_depos_currencies=[cross[0:3],
                                                          cross[3:6]],
                                   cache_algo="cache_algo_return",
                                   abstract_curve=fx_forwards_curve)

    # In case any missing values fill down (particularly can get this for NDFs)
    df_cuemacro_tot_1M = market.fetch_market(md_request=md_request).fillna(
        method="ffill")

    fx_forwards_curve = FXForwardsCurve()

    df_cuemacro_tot_1M.columns = [
        x.replace("forward-tot", "forward-tot-1M-cuemacro") for x in
        df_cuemacro_tot_1M.columns]

    # Get spot data
    md_request.abstract_curve = None
    md_request.category = "fx"

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
    # constructed indices track the Bloomberg
    # indices relatively well (both from spot and forwards). Also note the
    # large difference with spot indices
    # CAREFUL to fill down, before reindexing because forwards indices are
    # likely to have different publishing dates
    df = calculations.join([pd.DataFrame(
        df_cuemacro_tot_1M[cross + "-forward-tot-1M-cuemacro.close"]),
                            df_bbg_tot, df_spot, df_bbg_tot_forwards],
                           how="outer").fillna(method="ffill")

    df = calculations.create_mult_index_from_prices(df)

    chart.plot(df)
