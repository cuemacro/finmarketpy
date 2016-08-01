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
tick_examples

Gives several examples of how to get tick data from Bloomberg

"""

# for logging
from chartesians.graphs.plotfactory import PlotFactory

from pythalesians.market.loaders.lighttimeseriesfactory import LightTimeSeriesFactory
from pythalesians.market.requests.timeseriesrequest import TimeSeriesRequest
from pythalesians.timeseries.calcs.timeseriescalcs import TimeSeriesCalcs
from pythalesians.timeseries.calcs.timeseriesfilter import TimeSeriesFilter
from pythalesians.util.loggermanager import LoggerManager
from chartesians.graphs.graphproperties import GraphProperties

if True:
    logger = LoggerManager().getLogger(__name__)

    from datetime import timedelta
    import datetime
    import pandas
    import pytz

    # just change "False" to "True" to run any of the below examples

    ###### download second data from Bloomberg for EUR/USD, USD/JPY (inverted) and GBP/USD around last payroll
    if True:
        finish_date = datetime.datetime.utcnow()
        start_date = finish_date - timedelta(days=60)

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

        ltsf = LightTimeSeriesFactory()
        ts_filter = TimeSeriesFilter()

        df_event_times = ltsf.harvest_time_series(time_series_request)

        utc_time = pytz.utc
        df_event_times = pandas.DataFrame(index = df_event_times['NFP.release-date-time-full'])
        df_event_times.index = df_event_times.index.tz_localize(utc_time)    # work in UTC time
        df_event_times = ts_filter.filter_time_series_by_date(start_date, finish_date, df_event_times)

        # get last NFP time
        start_date = df_event_times.index[-1] - timedelta(minutes=1)
        finish_date = start_date + timedelta(minutes=4)

        tickers = ['EURUSD', 'JPYUSD', 'GBPUSD']
        vendor_tickers = ['EURUSD BGN Curncy', 'USDJPY BGN Curncy', 'GBPUSD BGN Curncy']

        # Bloomberg will give tick data which is downsampled within the LightTimeSeriesFactory class
        time_series_request = TimeSeriesRequest(
                    start_date = start_date,                        # start date
                    finish_date = finish_date,                      # finish date
                    freq = 'second',                                # second data
                    data_source = 'bloomberg',                      # use Bloomberg as data source
                    tickers = tickers,                              # ticker (Thalesians)
                    fields = ['close'],                             # which fields to download
                    vendor_tickers = vendor_tickers,
                    vendor_fields = ['close'],                      # which Bloomberg fields to download
                    cache_algo = 'internet_load_return')            # how to return data

        df = ltsf.harvest_time_series(time_series_request)
        df.columns = [x.replace('.close', '') for x in df.columns.values]

        # Bloomberg does not give the milisecond field when you make a tick request, so might as well downsample to S

        df['JPYUSD'] = 1 / df['JPYUSD']

        gp = GraphProperties()
        pf = PlotFactory()
        gp.scale_factor = 3
        gp.title = 'FX around last NFP date'
        gp.source = 'Thalesians/BBG (created with PyThalesians Python library)'

        tsc = TimeSeriesCalcs()
        df = tsc.create_mult_index_from_prices(df)

        pf.plot_line_graph(df, adapter = 'pythalesians', gp = gp)

    ###### download tick data from Bloomberg for EUR/USD around last FOMC and then downsample to plot
    if True:
        finish_date = datetime.datetime.utcnow()
        start_date = finish_date - timedelta(days=60)

        # fetch Fed times from Bloomberg
        time_series_request = TimeSeriesRequest(
                start_date = start_date,                # start date
                finish_date = finish_date,              # finish date
                category = "events",
                freq = 'daily',                         # daily data
                data_source = 'bloomberg',              # use Bloomberg as data source
                tickers = ['FOMC'],
                fields = ['release-date-time-full'],                    # which fields to download
                vendor_tickers = ['FDTR Index'], # ticker (Bloomberg)
                vendor_fields = ['ECO_FUTURE_RELEASE_DATE_LIST'],   # which Bloomberg fields to download
                cache_algo = 'internet_load_return')                # how to return data

        ltsf = LightTimeSeriesFactory()
        ts_filter = TimeSeriesFilter()

        df_event_times = ltsf.harvest_time_series(time_series_request)

        utc_time = pytz.utc
        df_event_times = pandas.DataFrame(index = df_event_times['FOMC.release-date-time-full'])
        df_event_times.index = df_event_times.index.tz_localize(utc_time)    # work in UTC time
        df_event_times = ts_filter.filter_time_series_by_date(start_date, finish_date, df_event_times)

        # get last NFP time
        start_date = df_event_times.index[-1] - timedelta(minutes=1)
        finish_date = start_date + timedelta(minutes=4)

        tickers = ['EURUSD']
        vendor_tickers = ['EURUSD BGN Curncy']

        time_series_request = TimeSeriesRequest(
                    start_date = start_date,                        # start date
                    finish_date = finish_date,                      # finish date
                    freq = 'tick',                                # second data
                    data_source = 'bloomberg',                      # use Bloomberg as data source
                    tickers = tickers,                              # ticker (Thalesians)
                    fields = ['close'],                             # which fields to download
                    vendor_tickers = vendor_tickers,
                    vendor_fields = ['close'],                      # which Bloomberg fields to download
                    cache_algo = 'internet_load_return')            # how to return data

        df = ltsf.harvest_time_series(time_series_request)
        df.columns = [x.replace('.close', '') for x in df.columns.values]

        # Bloomberg does not give the milisecond field when you make a tick request, so might as well downsample to seconds
        df = df.resample('1s')

        gp = GraphProperties()
        pf = PlotFactory()
        gp.scale_factor = 3
        gp.title = 'FX around last FOMC date'
        gp.source = 'Thalesians/BBG (created with PyThalesians Python library)'

        tsc = TimeSeriesCalcs()
        df = tsc.create_mult_index_from_prices(df)

        pf.plot_line_graph(df, adapter = 'pythalesians', gp = gp)

