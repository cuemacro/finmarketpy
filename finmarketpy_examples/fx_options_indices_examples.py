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
Shows how to use finmarketpy to total return indices for FX vanilla options 
(uses FinancePy underneath), so we can  see the historical P&L from for 
example, rolling a 1M call option etc.

Note, you will need to have a Bloomberg terminal (with blpapi Python library) 
to download the FX market data in order to generate the FX option prices, 
which are used underneath (FX spot, FX forwards, FX implied volatility quotes 
and deposit rates)
"""

import pandas as pd

# For plotting
from chartpy import Chart, Style

# For loading market data
from findatapy.market import Market, MarketDataGenerator, MarketDataRequest

from findatapy.timeseries import Filter, Calculations, RetStats

from findatapy.util.loggermanager import LoggerManager

from finmarketpy.curve.fxoptionscurve import FXOptionsCurve
from finmarketpy.curve.volatility.fxvolsurface import FXVolSurface
from finmarketpy.curve.volatility.fxoptionspricer import FXOptionsPricer

try:
    from finaddpy.market import CachedMarketDataGenerator as MarketDataGenerator
except:
    pass


logger = LoggerManager().getLogger(__name__)

chart = Chart(engine="plotly")

market = Market(market_data_generator=MarketDataGenerator())

# Choose run_example = 0 for everything
# run_example = 1 - create total return index AUDUSD 1M long calls (and 
# separately long puts) over 2008 financial crisis and further
# run_example = 2 - create total return index USDJPY 1W short straddles 
# over a long sample

run_example = 0


def prepare_indices(cross, df_option_tot=None, df_option_tc=None,
                    df_spot_tot=None):
    df_list = []

    if df_option_tot is not None:
        df_list.append(
            pd.DataFrame(df_option_tot[cross + "-option-tot.close"]))
        df_list.append(
            pd.DataFrame(df_option_tot[cross + "-option-delta-tot.close"]))
        df_list.append(
            pd.DataFrame(df_option_tot[cross + "-delta-pnl-index.close"]))

    if df_option_tc is not None:
        df_list.append(
            pd.DataFrame(df_option_tc[cross + "-option-tot-with-tc.close"]))
        df_list.append(pd.DataFrame(
            df_option_tc[cross + "-option-delta-tot-with-tc.close"]))
        df_list.append(pd.DataFrame(
            df_option_tc[cross + "-delta-pnl-index-with-tc.close"]))

    if df_spot_tot is not None:
        df_list.append(df_spot_tot)

    df = calculations.join(df_list, how="outer").fillna(method="ffill")

    return calculations.create_mult_index_from_prices(df)


if __name__ == "__main__":

    # Fetch market data for pricing AUDUSD options in 2007 (ie. FX spot,
    # FX forwards, FX deposits and FX vol quotes)
    # Construct volatility surface using FinancePy library underneath,
    # using polynomial interpolation
    # Enters a long 1M call, and MTM every day, and at expiry rolls into another long 1M call
    if run_example == 1 or run_example == 0:
        # Warning make sure you choose dates, where there is full vol surface!
        # If points are missing interpolation
        # will fail
        start_date = "01 Jan 2007";
        finish_date = "31 Dec 2020"  # Use smaller window for quicker execution

        cross = "AUDUSD"
        fx_options_trading_tenor = "1M"

        # Download the whole all market data for AUDUSD for pricing options
        # (FX vol surface + spot + FX forwards + depos)
        md_request = MarketDataRequest(start_date=start_date,
                                       finish_date=finish_date,
                                       data_source="bloomberg", cut="BGN",
                                       category="fx-vol-market",
                                       tickers=cross,
                                       fx_vol_tenor=["1W", "1M", "3M"],
                                       cache_algo="cache_algo_return",
                                       base_depos_currencies=[cross[0:3],
                                                              cross[3:6]])

        df_vol_market = market.fetch_market(md_request)
        df_vol_market = df_vol_market.fillna(method="ffill")

        # Remove New Year"s Day and Christmas
        df_vol_market = Filter().filter_time_series_by_holidays(df_vol_market,
                                                                cal="FX")

        # Get a total return index for trading spot
        # This way we can take into account carry when calculating delta
        # hedging P&L
        md_request = MarketDataRequest(start_date=start_date,
                                       finish_date=finish_date,
                                       data_source="bloomberg", cut="NYC",
                                       category="fx-tot",
                                       tickers=cross,
                                       cache_algo="cache_algo_return")

        df_tot = market.fetch_market(md_request)

        df_vol_market = df_vol_market.join(df_tot, how="left")
        df_vol_market = df_vol_market.fillna(method="ffill")

        # We want to roll long 1M ATM call at expiry
        # We"ll mark to market the option price through the month by
        # interpolating between 1W and 1M (and using whole vol curve
        # at each tenor)
        fx_options_curve = FXOptionsCurve(
            fx_options_trading_tenor=fx_options_trading_tenor,
            roll_days_before=0,
            roll_event="expiry-date",
            roll_months=1,
            fx_options_tenor_for_interpolation=["1W", "1M"],
            strike="atm",
            contract_type="european-call",
            depo_tenor_for_option="1M",
            position_multiplier=1.0,
            tot_label="tot",
            output_calculation_fields=True)

        # Let"s trade a long 1M call, and we roll at expiry
        df_cuemacro_option_call_tot = fx_options_curve.construct_total_return_index(
            cross, df_vol_market)

        # Add transaction costs to the option index (bid/ask bp for the option
        # premium and spot FX)
        df_cuemacro_option_call_tc = fx_options_curve.apply_tc_signals_to_total_return_index(
            cross, df_cuemacro_option_call_tot,
            option_tc_bp=5, spot_tc_bp=2)

        # Let"s trade a long 1M OTM put, and we roll at expiry
        df_cuemacro_option_put_tot = fx_options_curve.construct_total_return_index(
            cross, df_vol_market, contract_type="european-put",
            strike="10d-otm", position_multiplier=1.0)

        # Add transaction costs to the option index (bid/ask bp for the option
        # premium and spot FX)
        df_cuemacro_option_put_tc = fx_options_curve.apply_tc_signals_to_total_return_index(
            cross, df_cuemacro_option_put_tot,
            option_tc_bp=5, spot_tc_bp=2)

        # Get total returns for spot
        df_bbg_tot = df_tot  # from earlier!
        df_bbg_tot.columns = [x + "-bbg" for x in df_bbg_tot.columns]

        # Calculate a hedged portfolio of spot + 2*options (can we reduce drawdowns?)
        calculations = Calculations()

        ret_stats = RetStats()

        df_hedged = calculations.join(
            [df_bbg_tot[cross + "-tot.close-bbg"].to_frame(),
             df_cuemacro_option_put_tc[
                 cross + "-option-tot-with-tc.close"].to_frame()], how="outer")
        df_hedged = df_hedged.fillna(method="ffill")
        df_hedged = df_hedged.pct_change()

        df_hedged["Spot + 2*option put hedge"] = df_hedged[
                                                     cross + "-tot.close-bbg"] + \
                                                 df_hedged[
                                                     cross + "-option-tot-with-tc.close"]

        df_hedged.columns = RetStats(returns_df=df_hedged,
                                     ann_factor=252).summary()

        # Plot everything

        # P&L from call
        chart.plot(calculations.create_mult_index_from_prices(
            prepare_indices(cross=cross,
                            df_option_tot=df_cuemacro_option_call_tot,
                            df_option_tc=df_cuemacro_option_call_tc,
                            df_spot_tot=df_bbg_tot)))

        # P&L from put option, put option + TC and total returns from spot
        chart.plot(calculations.create_mult_index_from_prices(
            prepare_indices(cross=cross,
                            df_option_tot=df_cuemacro_option_put_tot,
                            df_option_tc=df_cuemacro_option_put_tc,
                            df_spot_tot=df_bbg_tot)))

        # P&L from put option + TC and total returns from spot
        chart.plot(calculations.create_mult_index_from_prices(
            prepare_indices(cross=cross,
                            df_option_tc=df_cuemacro_option_put_tc,
                            df_spot_tot=df_bbg_tot)))

        # P&L for total returns from spot and total returns from
        # + 2*put option + TC (ie. hedged portfolio)
        chart.plot(calculations.create_mult_index(df_hedged))

        # Plot delta from put option
        chart.plot(df_cuemacro_option_put_tot[cross + "-delta.close"])

    # Fetch market data for pricing EURUSD options from 2006-2020 (ie.
    # FX spot, FX forwards, FX deposits and FX vol quotes)
    # Construct volatility surface using FinancePy library underneath,
    # using polynomial interpolation
    #  Enters a short 1W straddle, and MTM every day, and at expiry rolls
    #  into another 1W straddle
    if run_example == 2 or run_example == 0:
        # Warning make sure you choose dates, where there is full vol surface!
        # If vol points in the tenors you are looking at
        # are missing then interpolation will fail (or if eg. spot data is missing etc.)
        start_date = "08 Mar 2007";
        finish_date = "31 Dec 2020"  # Monday
        # start_date = "09 Mar 2007"; finish_date = "31 Dec 2014"
        # start_date = "04 Jan 2006"; finish_date = "31 Dec 2008"
        # start_date = "01 Jan 2007"; finish_date = "31 Dec 2007" # Use smaller window for quicker execution

        cross = "USDJPY"
        fx_options_trading_tenor = "1W"  # Try changing between 1W and 1M!

        # Download the whole all market data for USDJPY for pricing options
        # (FX vol surface + spot + FX forwards + depos)
        md_request = MarketDataRequest(start_date=start_date,
                                       finish_date=finish_date,
                                       data_source="bloomberg", cut="10AM",
                                       category="fx-vol-market",
                                       tickers=cross,
                                       fx_vol_tenor=["1W", "1M"],
                                       base_depos_tenor=["1W", "1M"],
                                       cache_algo="cache_algo_return",
                                       base_depos_currencies=[cross[0:3],
                                                              cross[3:6]])

        df = market.fetch_market(md_request)

        # Fill data for every workday and use weekend calendar (note: this is
        # a bit of a fudge, filling down)
        # CHECK DATA isn"t missing at start of series
        df = df.resample("B").last().fillna(method="ffill")
        df = df[
            df.index >= "09 Mar 2007"]  # Try starting on a different day of
        # the week & see how it impact P&L?
        cal = "WKD"

        # Remove New Year"s Day and Christmas
        # df = Filter().filter_time_series_by_holidays(df, cal="FX")

        # We want to roll a short 1W option at expiry
        # If we select longer dates, it will mark to market the price through
        # the month by interpolating between eg. 1W and 1M
        # (and using whole vol curve at each tenor)
        fx_options_curve = FXOptionsCurve(
            fx_options_trading_tenor=fx_options_trading_tenor,
            roll_days_before=0,
            roll_event="expiry-date",
            roll_months=1,  # This is ignored if we roll on expiry date
            fx_options_tenor_for_interpolation=["1W", "1M"],
            strike="atm",
            contract_type="european-straddle",
            position_multiplier=-1.0,
            # +1.0 for long options, -1.0 for short options
            output_calculation_fields=True,
            freeze_implied_vol=True,
            cal=cal,
            cum_index="mult")

        # Let"s trade a short straddle, and we roll at expiry
        df_cuemacro_option_straddle_tot = fx_options_curve.construct_total_return_index(
            cross, df,
            depo_tenor_for_option=fx_options_trading_tenor)

        # Add transaction costs to the option index (bid/ask bp for the option
        # premium and spot FX)
        # Have wider spread for straddle (because adding call + put)
        df_cuemacro_option_straddle_tc = fx_options_curve.apply_tc_signals_to_total_return_index(
            cross, df_cuemacro_option_straddle_tot,
            option_tc_bp=10, spot_tc_bp=2)

        # Get total returns for spot
        md_request.abstract_curve = None

        # Get Bloomberg calculated total return indices (for spot)
        md_request.category = "fx-tot"
        md_request.cut = "NYC"

        df_bbg_tot = market.fetch_market(md_request)
        df_bbg_tot.columns = [x + "-bbg" for x in df_bbg_tot.columns]

        calculations = Calculations()

        df_index = calculations.create_mult_index_from_prices(
            prepare_indices(cross=cross,
                            df_option_tc=df_cuemacro_option_straddle_tc,
                            df_spot_tot=df_bbg_tot))

        from finmarketpy.economics.quickchart import QuickChart

        QuickChart(engine="plotly").plot_chart_with_ret_stats(
              df=df_index,
              plotly_plot_mode="offline_html",
              scale_factor=-1.5)
