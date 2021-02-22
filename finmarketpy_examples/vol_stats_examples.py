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
Here we show how to use VolStats to calculate various volatility metrics (like realized volatility, volatility risk 
premium and the implied volatility addons)

Note, you will need to have a Bloomberg terminal (with blpapi Python library) to download the FX market data in order
to run most of these examples (FX spot, FX forwards, FX implied_vol volatility quotes and deposits)
"""

import pandas as pd

# For plotting
from chartpy import Chart, Style

# For loading market data
from findatapy.market import Market, MarketDataGenerator, MarketDataRequest
from findatapy.util.loggermanager import LoggerManager

# For doing the various volatility _calculations
from finmarketpy.curve.volatility.volstats import VolStats

logger = LoggerManager().getLogger(__name__)

chart = Chart(engine='plotly')
market = Market(market_data_generator=MarketDataGenerator())

# Choose run_example = 0 for everything
# run_example = 1 - calculating difference between realized and implied volatility over Brexit for GBPUSD
# run_example = 2 - calculating realized volatility using different minute frequencies over Brexit for GBPUSD
# run_example = 3 - calculating implied volatility addon associated with days
# run_example = 4 - compare recent implied vs realized volatility for EURUSD

run_example = 0

###### Looking at realized and implied volatility over GBPUSD in the overnight (ON) tenor
if run_example == 1 or run_example == 0:
    # Download the whole all market data for GBPUSD for pricing options (vol surface)
    md_request = MarketDataRequest(start_date='01 Jun 2016', finish_date='02 Jul 2016',
                                   data_source='bloomberg', cut='10AM', category='fx-vol-market',
                                   tickers=['GBPUSD'],
                                   cache_algo='cache_algo_return')

    market_df = market.fetch_market(md_request)

    # Download FX tick data for GBPUSD over Brexit vote and then convert into 1 minute data (open/high/low/close)
    # which are necessary for calculating realised volatility
    md_request = MarketDataRequest(start_date='01 Jun 2016', finish_date='02 Jul 2016',
                                   data_source='dukascopy', freq='tick', category='fx', fields=['bid', 'ask'],
                                   tickers=['GBPUSD'],
                                   cache_algo='cache_algo_return')

    from findatapy.timeseries import Calculations
    calc = Calculations()

    tick_data = market.fetch_market(md_request)
    intraday_spot_df = calc.resample_tick_data_ohlc(tick_data, 'GBPUSD', freq='1min')

    vol_stats = VolStats(market_df=market_df, intraday_spot_df=intraday_spot_df)

    realized_vol = vol_stats.calculate_realized_vol('GBPUSD', tenor_label="ON", freq='intraday', freq_min_mult=1,
                                                    hour_of_day=10, minute_of_day=0, field='close', timezone_hour_minute='America/New_York') * 100

    implied_vol = pd.DataFrame(market_df['GBPUSDVON.close'])

    vrp = vol_stats.calculate_vol_risk_premium('GBPUSD', tenor_label='ON', implied_vol=implied_vol, realized_vol=realized_vol)

    style = Style()

    style.title = 'GBPUSD ON volatility over Brexit'
    style.scale_factor = 3
    style.source = 'Bloomberg'

    # Plot all the volatility metrics
    chart.plot(vrp, style=style)

    # Plot the implied volatility bumped forward a day against the realized volatility calculated over that day
    chart.plot(vrp[['GBPUSDUON.close', 'GBPUSDHON.close']], style=style)

###### Calculating realized volatility over Brexit vote in GBPUSD in ON/overnight tenor
# Showing the difference between time frequencies
if run_example == 2 or run_example == 0:

    # Download FX tick data for GBPUSD over Brexit vote and then convert into 1 minute data (open/high/low/close)
    # which are necessary for calculating realised volatility
    md_request = MarketDataRequest(start_date='01 Jun 2016', finish_date='02 Jul 2016',
                                   data_source='dukascopy', freq='tick', category='fx', fields=['bid', 'ask'],
                                   tickers=['GBPUSD'],
                                   cache_algo='cache_algo_return')

    from findatapy.timeseries import Calculations
    calc = Calculations()

    intraday_spot_df = calc.resample_tick_data_ohlc(market.fetch_market(md_request), 'GBPUSD', freq='1min')['GBPUSD.close']

    vol_stats = VolStats()

    # Resample spot data at different minute intervals, and then calculate realized vols
    minute_frequencies = [1, 2, 5, 10, 15, 30, 60]

    realized_vol = []

    for min in minute_frequencies:
        min_df = pd.DataFrame(intraday_spot_df.resample(str(min) + 'min').last().dropna())

        rv = vol_stats.calculate_realized_vol('GBPUSD', spot_df=min_df,
                tenor_label="ON", freq='intraday', freq_min_mult=min,
                hour_of_day=10, minute_of_day=0, field='close', timezone_hour_minute='America/New_York') * 100

        rv.columns=[str(min) + 'min']

        realized_vol.append(rv)

    realized_vol = calc.join(realized_vol, how='outer')
    style = Style()

    style.title = 'GBPUSD ON realized volatility over Brexit with different minute sampling frequencies'
    style.scale_factor = 3
    style.source = 'Bloomberg'
    style.color = 'Blues'

    # Plot the volatilities with different sampling frequencies
    chart.plot(realized_vol, style=style)

###### Look at the addon in the ON GBPUSD implied vol around Brexit, note the first month will be empty given the nature
# of the model
if run_example == 3 or run_example == 0:
    # Download the whole all market data for GBPUSD for pricing options (vol surface)
    # Note: 10AM prints for vol no longer published by Bloomberg, so later values are a weighted average of TOK and LDN
    # closes
    md_request = MarketDataRequest(start_date='01 May 2016', finish_date='02 Jul 2016',
                                   data_source='bloomberg', cut='10AM', category='fx-vol-market',
                                   tickers=['GBPUSD'],
                                   cache_algo='cache_algo_return')

    market_df = market.fetch_market(md_request)

    from findatapy.timeseries import Calculations
    calc = Calculations()

    vol_stats = VolStats(market_df=market_df)

    implied_addon = vol_stats.calculate_implied_vol_addon('GBPUSD', tenor_label='ON').dropna()

    style = Style()

    style.title = 'GBPUSD ON implied volatility addon over Brexit'
    style.scale_factor = 3
    style.source = 'Bloomberg'

    # Plot the implied volatility addon, note the large addon just before Brexit vote!
    chart.plot(implied_addon, style=style)

###### Look at the statistics for recent period for EURUSD comparing implied vs realized
if run_example == 4 or run_example == 0:

    import datetime
    from datetime import timedelta

    # Download past few months of data (BBG usually keeps a few months of intraday data)
    # for FX vol and FX spot. We are downloading intraday vol data, because we want to get a snapshot
    # at 1000 ET, which is the time at which FX options expire, so our dataset will cover every event
    today = datetime.datetime.utcnow().date()
    month_before = today - timedelta(days=60)

    # month_before = '01 Nov 2020'; today = '01 Dec 2020'

    asset = 'EURUSD'

    # Download the whole all market data for pricing options (vol surface)
    md_request = MarketDataRequest(start_date=month_before, finish_date=today,
                                   data_source='bloomberg', freq='intraday', fields='open',
                                   tickers=[asset + 'VON'], vendor_tickers=[asset + 'VON BGN Curncy'],
                                   cache_algo='cache_algo_return')

    from findatapy.timeseries import Calculations, Filter
    calc = Calculations()
    filter = Filter()

    freq_min_mult = 5

    # Resample into 1 minute data and fill down all points
    implied_vol_df = market.fetch_market(md_request)[asset +'VON.open'].resample('1min').first().fillna(method='ffill')

    # Filter data by 1000 New York time, and return back to UTC, remove any out of trading hours
    # Then strip of time of day from the timestamp
    implied_vol_df = filter.filter_time_series_by_time_of_day_timezone(10, 0, implied_vol_df, timezone_of_snap='America/New_York')
    implied_vol_df = filter.remove_out_FX_out_of_hours(implied_vol_df)
    implied_vol_df.index = pd.to_datetime(implied_vol_df.index.date)
    implied_vol_df = pd.DataFrame(implied_vol_df)
    implied_vol_df.columns = [asset + 'VON.close']

    # Download FX intraday spot data, which will be used to calculate realized volatility
    md_request.tickers = asset; md_request.vendor_tickers = asset + ' BGN Curncy'
    intraday_spot_df = market.fetch_market(md_request).resample(str(freq_min_mult) + 'min').first()
    intraday_spot_df = filter.remove_out_FX_out_of_hours(intraday_spot_df).dropna()
    intraday_spot_df.columns = [asset + '.close']

    vol_stats = VolStats()

    # Calculate realized vol with the intraday data, with daily cutoffs
    realized_vol = vol_stats.calculate_realized_vol(
        asset, tenor_label='ON', spot_df=intraday_spot_df, hour_of_day=10, minute_of_day=0,
        freq='intraday', timezone_hour_minute='America/New_York', freq_min_mult=freq_min_mult) * 100.0
    implied_vol_addon = vol_stats.calculate_implied_vol_addon(asset, implied_vol=implied_vol_df, tenor_label='ON',
                                                adj_ON_friday=True).dropna()

    vrp = vol_stats.calculate_vol_risk_premium(asset, tenor_label='ON', implied_vol=implied_vol_df, realized_vol=realized_vol,
                                                adj_ON_friday=True)

    style = Style()

    style.title = asset + ' ON implied volatility vs realized'
    style.scale_factor = 3
    style.source = 'Bloomberg'

    to_plot = vrp[[asset + 'UON.close', asset +'HON.close']].dropna()

    chart.plot(to_plot, style=style)

    style.title = asset + 'ON implied volatility addon'
    chart.plot(implied_vol_addon, style=style)

