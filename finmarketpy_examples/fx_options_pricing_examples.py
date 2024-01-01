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
Shows how to use finmarketpy to price FX options (uses FinancePy underneath - 
it is recommended you pull the latest version of FinancePy from GitHub).

Note, you will need to have a Bloomberg terminal (with blpapi Python library) 
to download the FX market data in order to plot these vol surface (FX spot, 
FX forwards, FX implied_vol volatility quotes and deposits)
"""

import pandas as pd

# For plotting
from chartpy import Chart, Style

# For loading market data
from findatapy.market import Market, MarketDataGenerator, MarketDataRequest

from findatapy.util.loggermanager import LoggerManager

from finmarketpy.curve.rates.fxforwardspricer import FXForwardsPricer
from finmarketpy.curve.volatility.fxvolsurface import FXVolSurface
from finmarketpy.curve.volatility.fxoptionspricer import FXOptionsPricer

logger = LoggerManager().getLogger(__name__)

chart = Chart(engine="plotly")

market = Market(market_data_generator=MarketDataGenerator())

# Choose run_example = 0 for everything
# run_example = 1 - price GBPUSD options
# run_example = 2 - price USDJPY options
# run_example = 3 - price AUDUSD options
# run_example = 4 - more pricing of AUDUSD options
# run_example = 5 - pricing of EURUSD options
# run_example = 6 - another USDJPY option
# run_example = 7 - price USDBRL options

run_example = 0

if __name__ == "__main__":

    # Fetch market data for pricing GBPUSD FX options over Brexit vote
    # (ie. FX spot, FX forwards, FX deposits and FX vol quotes)
    # Construct volatility surface using FinancePy library underneath,
    # using polynomial interpolation and then price some options over these
    # dates eg. atm, 25d-call etc.
    if run_example == 1 or run_example == 0:
        horizon_date = "23 Jun 2016"
        cross = "GBPUSD"

        # Download the whole all market data for GBPUSD for pricing options (vol surface)
        md_request = MarketDataRequest(start_date=horizon_date,
                                       finish_date=horizon_date,
                                       data_source="bloomberg", cut="NYC",
                                       category="fx-vol-market",
                                       tickers=cross,
                                       base_depos_currencies=[cross[0:3],
                                                              cross[3:6]],
                                       cache_algo="cache_algo_return")

        df = market.fetch_market(md_request)

        fx_vol_surface = FXVolSurface(market_df=df, asset=cross)

        fx_op = FXOptionsPricer(fx_vol_surface=fx_vol_surface)

        # Price several different options

        print("atm 1M european call")
        print(fx_op.price_instrument(cross, pd.Timestamp(horizon_date), "atm",
                                     contract_type="european-call",
                                     tenor="1M").to_string())

        print("25d 1W european put")
        print(fx_op.price_instrument(cross, pd.Timestamp(horizon_date),
                                     "25d-otm", contract_type="european-put",
                                     tenor="1W").to_string())

        # Try a broken date 12D option (note, for broken dates, currently doesn"t interpolate key strikes)
        # Specify expiry date instead of the tenor for broken dates
        print("1.50 12D european call")
        print(fx_op.price_instrument(cross, pd.Timestamp(horizon_date), 1.50,
                                     expiry_date=pd.Timestamp(
                                         horizon_date) + pd.Timedelta(days=12),
                                     contract_type="european-call").to_string())

    ###### Fetch market data for pricing USDJPY FX options over Brexit vote (ie. FX spot, FX forwards, FX deposits and FX vol quotes)
    ###### Construct volatility surface using FinancePy library underneath, using polynomial interpolation
    ###### Then price a series of 1W ATM call options
    if run_example == 2 or run_example == 0:
        start_date = "02 Nov 2020";
        finish_date = "05 Nov 2020"
        horizon_date = pd.bdate_range(start_date, finish_date, freq="B")

        cross = "USDJPY"

        # Download the whole all market data for GBPUSD for pricing options (vol surface)
        md_request = MarketDataRequest(start_date=start_date,
                                       finish_date=finish_date,
                                       data_source="bloomberg", cut="NYC",
                                       category="fx-vol-market",
                                       tickers=cross,
                                       cache_algo="cache_algo_return",
                                       base_depos_currencies=[cross[0:3],
                                                              cross[3:6]])

        df = market.fetch_market(md_request)

        # Skip 3W/4M because this particular close (NYC) doesn"t have that in USDJPY market data
        tenors = ["ON", "1W", "2W", "1M", "2M", "3M", "6M", "9M", "1Y", "2Y",
                  "3Y"]
        fx_vol_surface = FXVolSurface(market_df=df, asset=cross, tenors=tenors)

        fx_op = FXOptionsPricer(fx_vol_surface=fx_vol_surface)

        print("atm 1W european put")
        print(fx_op.price_instrument(cross, horizon_date, "atm",
                                     contract_type="european-put",
                                     tenor="1W", depo_tenor="1W").to_string())

        print("25d 3M european call")
        print(fx_op.price_instrument(cross, horizon_date, "25d-otm",
                                     contract_type="european-call",
                                     tenor="3M", depo_tenor="3M").to_string())

        print("10d 1M european put")
        print(fx_op.price_instrument(cross, horizon_date, "10d-otm",
                                     contract_type="european-put",
                                     tenor="1M", depo_tenor="1M").to_string())

    ###### Fetch market data for pricing AUDUSD options on 18 Apr 2007, just before credit crisis
    ###### Construct volatility surface using FinancePy library underneath, using polynomial interpolation and
    ###### Then price some options over these dates eg. atm, 25d-call etc.
    if run_example == 3 or run_example == 0:
        horizon_date = "18 Apr 2007"
        cross = "AUDUSD"

        # Download the whole all market data for GBPUSD for pricing options (vol surface)
        md_request = MarketDataRequest(start_date=horizon_date,
                                       finish_date=horizon_date,
                                       data_source="bloomberg", cut="LDN",
                                       category="fx-vol-market",
                                       tickers=cross,
                                       base_depos_currencies=[cross[0:3],
                                                              cross[3:6]],
                                       cache_algo="cache_algo_return")

        df = market.fetch_market(md_request)

        fx_vol_surface = FXVolSurface(market_df=df, asset=cross,
                                      tenors=["ON", "1W", "1M"])

        fx_op = FXOptionsPricer(fx_vol_surface=fx_vol_surface)

        # Try a broken date 15D option (note, for broken dates, currently doesn"t interpolate key strikes)
        # Specify expiry date instead of the tenor for broken dates
        print("atm 15D european call")
        print(fx_op.price_instrument(cross, pd.Timestamp(horizon_date), 0.8124,
                                     expiry_date=pd.Timestamp(
                                         horizon_date) + pd.Timedelta(days=15),
                                     contract_type="european-call").to_string())

    ###### Fetch market data for pricing AUDUSD options during start of 2008 Credit Crisis
    if run_example == 4 or run_example == 0:
        horizon_date = "17 Aug 2007"
        cross = "AUDUSD"

        # Download the whole all market data for GBPUSD for pricing options (vol surface)
        md_request = MarketDataRequest(start_date=horizon_date,
                                       finish_date=horizon_date,
                                       data_source="bloomberg", cut="BGN",
                                       category="fx-vol-market",
                                       tickers=cross,
                                       base_depos_currencies=[cross[0:3],
                                                              cross[3:6]],
                                       cache_algo="cache_algo_return")

        df = market.fetch_market(md_request)

        fx_vol_surface = FXVolSurface(market_df=df, asset=cross,
                                      tenors=["1W", "1M", "3M"])
        fx_vol_surface.build_vol_surface(pd.Timestamp(horizon_date))

        fx_op = FXOptionsPricer(fx_vol_surface=fx_vol_surface)

        # Price several different options

        # Try a broken date 15D option (note, for broken dates, currently doesn"t interpolate key strikes)
        # Specify expiry date instead of the tenor for broken dates
        print("atm 15D european call")

        print(fx_op.price_instrument(cross, pd.Timestamp(horizon_date), 0.8535,
                                     expiry_date=pd.Timestamp("05 Sep 2007"),
                                     contract_type="european-call").to_string())

    ###### Fetch market data for pricing EURUSD options during start of 2006
    if run_example == 5 or run_example == 0:
        horizon_date = "04 Jan 2006"
        cross = "EURUSD"

        # Download the whole all market data for GBPUSD for pricing options (vol surface)
        md_request = MarketDataRequest(start_date=horizon_date,
                                       finish_date=horizon_date,
                                       data_source="bloomberg", cut="BGN",
                                       category="fx-vol-market",
                                       tickers=cross,
                                       base_depos_currencies=[cross[0:3],
                                                              cross[3:6]],
                                       cache_algo="cache_algo_return")

        df = market.fetch_market(md_request)

        fx_vol_surface = FXVolSurface(market_df=df, asset=cross,
                                      tenors=["1W", "1M", "3M"])

        fx_op = FXOptionsPricer(fx_vol_surface=fx_vol_surface)

        # Price several different options

        # Try a broken date 15D option (note, for broken dates, currently doesn"t interpolate key strikes)
        # Specify expiry date instead of the tenor for broken dates
        print("atm 1W european call")
        print(fx_op.price_instrument(cross, pd.Timestamp(horizon_date), "atm",
                                     tenor="1W", depo_tenor="1W",
                                     contract_type="european-call").to_string())

    ###### Fetch market data for pricing USDJPY ATM 1W
    if run_example == 6 or run_example == 0:
        horizon_date = "30 March 2007"
        cross = "USDJPY"

        # Download the whole all market data for GBPUSD for pricing options (vol surface)
        md_request = MarketDataRequest(start_date=horizon_date,
                                       finish_date=horizon_date,
                                       data_source="bloomberg", cut="LDN",
                                       category="fx-vol-market",
                                       fx_vol_tenor=["1W"],
                                       tickers=cross,
                                       base_depos_currencies=[cross[0:3],
                                                              cross[3:6]],
                                       cache_algo="cache_algo_return")

        df = market.fetch_market(md_request)

        fx_vol_surface = FXVolSurface(market_df=df, asset=cross, tenors=["1W"],
                                      solver="nelmer-mead-numba")

        fx_op = FXOptionsPricer(fx_vol_surface=fx_vol_surface)

        market_df = fx_vol_surface.get_all_market_data()

        # Print 1W data
        print(market_df[[x for x in market_df.columns if "1W" in x]][
                  market_df.index == horizon_date].to_string())

        # Print ATM vol
        fx_vol_surface.build_vol_surface(horizon_date)
        fx_vol_surface.extract_vol_surface(num_strike_intervals=None)

        print("ATM vol " + str(fx_vol_surface.get_atm_vol(tenor="1W")))

        # Specify expiry date instead of the tenor for broken dates
        print("atm 1W european straddle")
        print(fx_op.price_instrument(cross, pd.Timestamp(horizon_date), "atm",
                                     tenor="1W", depo_tenor="1W",
                                     contract_type="european-straddle").to_string())

    ###### Price USDBRL option around 2018 2nd round of presidential election
    if run_example == 7 or run_example == 0:
        horizon_date = "26 Oct 2018"
        cross = "USDBRL"
        non_usd = "BRL"

        # Download the whole all market data for USDBRL for pricing options (vol surface)
        md_request = MarketDataRequest(start_date=horizon_date,
                                       finish_date=horizon_date,
                                       data_source="bloomberg", cut="NYC",
                                       category="fx-vol-market",
                                       tickers=cross,
                                       base_depos_currencies=[cross[0:3]],
                                       cache_algo="cache_algo_return")

        df = market.fetch_market(md_request)

        # Compute implied deposit BRL 1M from USDBRL forwards (and USD 1M depo)
        fx_forwards_price = FXForwardsPricer()

        implied_depo_df = fx_forwards_price.calculate_implied_depo(cross,
                                                                   non_usd,
                                                                   market_df=df,
                                                                   fx_forwards_tenor=[
                                                                       "1W",
                                                                       "1M"],
                                                                   depo_tenor=[
                                                                       "1W",
                                                                       "1M"])

        implied_depo_df.columns = [x.replace("-implied-depo", "") for x in
                                   implied_depo_df.columns]
        df = df.join(implied_depo_df, how="left")

        # USDBRL quoted ATMF implied vol (as opposed to delta neutral) hence "fwd" parameter
        fx_op = FXOptionsPricer(
            fx_vol_surface=FXVolSurface(market_df=df, asset=cross,
                                        atm_method="fwd", depo_tenor="1M"))

        # Price several different options
        print(df)

        print("atm 1M european put")
        print(fx_op.price_instrument(cross, pd.Timestamp(horizon_date), "atm",
                                     contract_type="european-put",
                                     tenor="1M").to_string())

        # TODO: calendar around election results in slightly different pricing
        # print(fx_op.price_instrument(cross, pd.Timestamp(horizon_date), "25d-otm", contract_type="european-put", tenor="1W").to_string())
        # print(fx_op.price_instrument(cross, pd.Timestamp(horizon_date), 3.5724, contract_type="european-put", expiry_date=pd.Timestamp("2 Nov 2018")).to_string())

    ###### Price GBPUSD option around Brexit with unquoted deltas
    if run_example == 8 or run_example == 0:
        horizon_date = "23 Jun 2016"
        cross = "GBPUSD"

        # Download the whole all market data for GBPUSD for pricing options (vol surface)
        md_request = MarketDataRequest(start_date=horizon_date,
                                       finish_date=horizon_date,
                                       data_source="bloomberg", cut="NYC",
                                       category="fx-vol-market",
                                       tickers=cross,
                                       base_depos_currencies=[cross[0:3],
                                                              cross[3:6]],
                                       cache_algo="cache_algo_return")

        df = market.fetch_market(md_request)

        fx_vol_surface = FXVolSurface(market_df=df, asset=cross)

        fx_op = FXOptionsPricer(fx_vol_surface=fx_vol_surface)

        # Price several different options
        print("atm 1M european call")
        print(fx_op.price_instrument(cross, pd.Timestamp(horizon_date), "atm",
                                     contract_type="european-call",
                                     tenor="1M").to_string())

        print("25d 1W european put")
        print(fx_op.price_instrument(cross, pd.Timestamp(horizon_date),
                                     "25d-otm", contract_type="european-put",
                                     tenor="1W").to_string())
