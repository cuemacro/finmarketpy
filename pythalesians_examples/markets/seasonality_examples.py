__author__ = 'saeedamen'

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
seasonality_examples

Shows how to calculate some seasonal patterns in markets using PyThalesians (Seasonality class)

"""

# loading data
import datetime

from pythalesians_graphics.graphs.plotfactory import PlotFactory

from pythalesians.economics.seasonality.seasonality import Seasonality
from pythalesians.market.loaders.lighttimeseriesfactory import LightTimeSeriesFactory
from pythalesians.market.requests.timeseriesrequest import TimeSeriesRequest
from pythalesians.timeseries.calcs.timeseriescalcs import TimeSeriesCalcs
from pythalesians.util.loggermanager import LoggerManager
from pythalesians_graphics.graphs.graphproperties import GraphProperties

seasonality = Seasonality()
tsc = TimeSeriesCalcs()
logger = LoggerManager().getLogger(__name__)

pf = PlotFactory()

# just change "False" to "True" to run any of the below examples

###### calculate seasonal moves in SPX (using Quandl data)
if True:
    time_series_request = TimeSeriesRequest(
                start_date = "01 Jan 1970",                     # start date
                finish_date = datetime.date.today(),            # finish date
                freq = 'daily',                                 # daily data
                data_source = 'bloomberg',                         # use Quandl as data source
                tickers = ['S&P500'],
                fields = ['close'],                                 # which fields to download
                vendor_tickers = ['SPX Index'],  # ticker (Quandl)
                vendor_fields = ['PX_LAST'],                          # which Bloomberg fields to download
                cache_algo = 'internet_load_return')                # how to return data

    ltsf = LightTimeSeriesFactory()

    df = ltsf.harvest_time_series(time_series_request)

    df_ret = tsc.calculate_returns(df)

    day_of_month_seasonality = seasonality.bus_day_of_month_seasonality(df_ret, partition_by_month = False)
    day_of_month_seasonality = tsc.convert_month_day_to_date_time(day_of_month_seasonality)

    gp = GraphProperties()
    gp.date_formatter = '%b'
    gp.title = 'S&P500 seasonality'
    gp.scale_factor = 3
    gp.file_output = "output_data/S&P500 DOM seasonality.png"

    pf.plot_line_graph(day_of_month_seasonality, adapter='pythalesians', gp = gp)

###### calculate seasonal moves in EUR/USD (using Quandl data)
if True:
    time_series_request = TimeSeriesRequest(
                start_date = "01 Jan 1970",                     # start date
                finish_date = datetime.date.today(),            # finish date
                freq = 'daily',                                 # daily data
                data_source = 'quandl',                         # use Quandl as data source
                tickers = ['EURUSD',                            # ticker (Thalesians)
                           'GBPUSD'],
                fields = ['close'],                                 # which fields to download
                vendor_tickers = ['FRED/DEXUSEU', 'FRED/DEXUSUK'],  # ticker (Quandl)
                vendor_fields = ['close'],                          # which Bloomberg fields to download
                cache_algo = 'internet_load_return')                # how to return data

    ltsf = LightTimeSeriesFactory()

    df = ltsf.harvest_time_series(time_series_request)

    df_ret = tsc.calculate_returns(df)

    day_of_month_seasonality = seasonality.bus_day_of_month_seasonality(df_ret, partition_by_month = False)
    day_of_month_seasonality = tsc.convert_month_day_to_date_time(day_of_month_seasonality)

    gp = GraphProperties()
    gp.date_formatter = '%b'
    gp.title = 'FX spot moves by day of month'
    gp.scale_factor = 3
    gp.file_output = "output_data/FX spot DOM seasonality.png"

    pf.plot_line_graph(day_of_month_seasonality, adapter='pythalesians', gp = gp)

###### calculate seasonal moves in FX vol (using Bloomberg data)
if False:
    tickers = [ 'EURUSD',                                       # ticker (Thalesians)
                'GBPUSD',
                'USDJPY']

    time_series_request = TimeSeriesRequest(
                start_date = "01 Jan 1999",                     # start date
                finish_date = datetime.date.today(),            # finish date
                freq = 'daily',                                 # daily data
                data_source = 'bloomberg',                      # use bloomberg as data source
                tickers = tickers,
                fields = ['close'],                                 # which fields to download
                vendor_tickers = [x + 'V1M BGN Curncy' for x in tickers],  # ticker (Bloomberg)
                    vendor_fields = ['PX_LAST'],                    # which Bloomberg fields to download
                cache_algo = 'internet_load_return')                # how to return data

    ltsf = LightTimeSeriesFactory()

    df = ltsf.harvest_time_series(time_series_request)

    df_ret = tsc.calculate_returns(df)

    day_of_month_seasonality = seasonality.bus_day_of_month_seasonality(df_ret, partition_by_month = False)
    day_of_month_seasonality = tsc.convert_month_day_to_date_time(day_of_month_seasonality)

    gp = GraphProperties()
    gp.date_formatter = '%b'
    gp.title = 'FX vols moves by day of month'
    gp.scale_factor = 3
    gp.file_output = "output_data/FX vol DOM seasonality.png"

    pf.plot_line_graph(day_of_month_seasonality, adapter='pythalesians', gp = gp)

###### calculate seasonal moves in stocks
if True:
    tickers = [ 'S&P500' ]
    vendor_tickers = ['SPX Index']

    time_series_request = TimeSeriesRequest(
                start_date = "01 Jan 1996",                     # start date
                finish_date = datetime.date.today(),            # finish date
                freq = 'daily',                                 # daily data
                data_source = 'bloomberg',                      # use bloomberg as data source
                tickers = tickers,
                fields = ['close'],                                 # which fields to download
                vendor_tickers = vendor_tickers,  # ticker (Bloomberg)
                vendor_fields = ['PX_LAST'],                    # which Bloomberg fields to download
                cache_algo = 'internet_load_return')                # how to return data

    ltsf = LightTimeSeriesFactory()

    df = ltsf.harvest_time_series(time_series_request)

    df_ret = tsc.calculate_returns(df)

    day_of_month_seasonality = seasonality.bus_day_of_month_seasonality(df_ret, partition_by_month = False)
    day_of_month_seasonality = tsc.convert_month_day_to_date_time(day_of_month_seasonality)

    gp = GraphProperties()
    gp.date_formatter = '%b'
    gp.title = 'Equities moves by day of month (past 20Y)'
    gp.scale_factor = 1
    gp.file_output = "output_data/equity_moves.png"

    pf.plot_line_graph(day_of_month_seasonality, adapter='pythalesians', gp = gp)