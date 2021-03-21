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
Examples for downloading economic data events from Bloomberg
"""

# for logging
import pandas
import pytz

from chartpy import Chart, Style

from findatapy.market import Market, MarketDataGenerator, MarketDataRequest
from findatapy.timeseries import Calculations
from findatapy.util import LoggerManager

from finmarketpy.economics import EventStudy

# choose run_example = 0 for everything
# run_example = 1 - download recent NFP times and do event study for USD/JPY

run_example = 0

###### download recent NFP times and do event study for USD/JPY (using Bloomberg data)
if run_example == 1 or run_example == 0:

    logger = LoggerManager().getLogger(__name__)

    import datetime

    from datetime import timedelta

    ###### Get intraday data for USD/JPY from the past few months from Bloomberg, NFP date/times from Bloomberg
    ###### then plot intraday price action around NFP for EUR/USD

    start_date = datetime.date.today() - timedelta(days=180)
    finish_date = datetime.datetime.utcnow().date()

    market = Market(market_data_generator=MarketDataGenerator())

    # Fetch NFP times from Bloomberg
    md_request = MarketDataRequest(
        start_date=start_date,              # start date
        finish_date=finish_date,            # finish date
        category="events",
        freq='daily',                       # daily data
        data_source='bloomberg',            # use Bloomberg as data source
        tickers=['NFP'],
        fields=['release-date-time-full'],  # which fields to download
        vendor_tickers=['NFP TCH Index'],   # ticker (Bloomberg)
        cache_algo='cache_algo_return')  # how to return data

    df_event_times = market.fetch_market(md_request)
    df_event_times = pandas.DataFrame(index=df_event_times['NFP.release-date-time-full'])

    # Need same timezone for event times as market data (otherwise can cause problems with Pandas)
    df_event_times = df_event_times.tz_localize('utc')

    # Fetch USD/JPY spot
    md_request = MarketDataRequest(
        start_date=start_date,      # start date
        finish_date=finish_date,    # finish date
        category='fx',
        freq='intraday',                # intraday
        data_source='bloomberg',        # use Bloomberg as data source
        tickers=['USDJPY'],             # ticker (finmarketpy)
        fields=['close'],               # which fields to download
        cache_algo='cache_algo_return')  # how to return data

    df = None
    df = market.fetch_market(md_request)

    calc = Calculations()
    df = calc.calculate_returns(df)

    es = EventStudy()

    # Work out cumulative asset price moves moves over the event
    df_event = es.get_intraday_moves_over_custom_event(df, df_event_times)

    # Create an average move
    df_event['Avg'] = df_event.mean(axis=1)

    # Plotting spot over economic data event
    style = Style()
    style.scale_factor = 3
    style.file_output = 'usdjpy-nfp.png'

    style.title = 'USDJPY spot moves over recent NFP'

    # Plot in shades of blue (so earlier releases are lighter, later releases are darker)
    style.color = 'Blues';
    style.color_2 = []
    style.y_axis_2_series = []
    style.display_legend = False

    # Last release will be in red, average move in orange
    style.color_2_series = [df_event.columns[-2], df_event.columns[-1]]
    style.color_2 = ['red', 'orange']  # red, pink
    style.linewidth_2 = 2
    style.linewidth_2_series = style.color_2_series

    chart = Chart(engine='matplotlib')
    chart.plot(df_event * 100, style=style)
