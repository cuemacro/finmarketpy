__author__ = 'saeedamen' # Saeed Amen / saeed@thalesians.com

#
# Copyright 2015 Thalesians Ltd. - http//www.thalesians.com / @thalesians
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
eventstudy_examples
 
Shows how to do event studies for assets

"""

# for logging
from pythalesians.util.loggermanager import LoggerManager

# to download market data
from pythalesians.market.requests.timeseriesrequest import TimeSeriesRequest
from pythalesians.market.loaders.lighttimeseriesfactory import LightTimeSeriesFactory

# for plotting graphs
from pythalesians.graphics.graphs.plotfactory import PlotFactory
from pythalesians.graphics.graphs.graphproperties import GraphProperties

# for making elementary calculations on the time series
from pythalesians.timeseries.calcs.timeseriescalcs import TimeSeriesCalcs

# for time series
import pandas
import pytz

if True:
    logger = LoggerManager().getLogger(__name__)

    import datetime

    from datetime import timedelta

    # just change "False" to "True" to run any of the below examples

    ###### get intraday data for USD/JPY from the past few months from Bloomberg, NFP date/times from Bloomberg
    ###### then plot intraday price action around NFP for EUR/USD
    if True:
        start_date = datetime.date.today() - timedelta(days=180)
        finish_date = datetime.date.today()

        time_series_request = TimeSeriesRequest(
                start_date = start_date,                    # start date
                finish_date = finish_date,                  # finish date
                freq = 'intraday',                          # intraday
                data_source = 'bloomberg',                  # use Bloomberg as data source
                tickers = ['USDJPY'],                       # ticker (Thalesians)
                fields = ['close'],                         # which fields to download
                vendor_tickers = ['USDJPY BGN Curncy'],     # ticker (Bloomberg)
                vendor_fields = ['PX_LAST'],                # which Bloomberg fields to download
                cache_algo = 'internet_load_return')           # how to return data

        ltsf = LightTimeSeriesFactory()

        df = None
        df = ltsf.harvest_time_series(time_series_request)

        utc_time = pytz.utc
        df.index = df.index.tz_localize(utc_time)       # work in UTC time

        tsc = TimeSeriesCalcs()
        df = tsc.calculate_returns(df)

        # fetch NFP times from Bloomberg
        time_series_request = TimeSeriesRequest(
                start_date = start_date,                # start date
                finish_date = finish_date,              # finish date
                category = "events",
                freq = 'daily',                         # daily data
                data_source = 'bloomberg',              # use Bloomberg as data source
                tickers = ['NFP'],
                fields = ['release-date-time-full'],                    # which fields to download
                vendor_tickers = ['NFP TCH Index'], # ticker (Bloomberg)
                vendor_fields = ['ECO_FUTURE_RELEASE_DATE_LIST'],   # which Bloomberg fields to download
                cache_algo = 'internet_load_return')                # how to return data

        df_event_times = ltsf.harvest_time_series(time_series_request)

        df_event_times = pandas.DataFrame(index = df_event_times['NFP.release-date-time-full'])
        df_event_times.index = df_event_times.index.tz_localize(utc_time)    # work in UTC time

        from pythalesians.economics.events.eventstudy import EventStudy

        es = EventStudy()

        # work out cumulative asset price moves moves over the event
        df_event = es.get_intraday_moves_over_custom_event(df, df_event_times)

        # create an average move
        df_event['Avg'] = df_event.mean(axis = 1)

        # plotting spot over economic data event
        gp = GraphProperties()
        gp.scale_factor = 3

        gp.title = 'USDJPY spot moves over recent NFP'

        # plot in shades of blue (so earlier releases are lighter, later releases are darker)
        gp.color = 'Blues'; gp.color_2 = []
        gp.y_axis_2_series = []
        gp.display_legend = False

        # last release will be in red, average move in orange
        gp.color_2_series = [df_event.columns[-2], df_event.columns[-1]]
        gp.color_2 = ['red', 'orange'] # red, pink
        gp.linewidth_2 = 2
        gp.linewidth_2_series = gp.color_2_series

        pf = PlotFactory()
        pf.plot_line_graph(df_event * 100, adapter = 'pythalesians', gp = gp)