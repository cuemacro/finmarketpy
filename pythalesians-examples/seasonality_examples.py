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
from pythalesians.market.loaders.lighttimeseriesfactory import LightTimeSeriesFactory
from pythalesians.market.requests.timeseriesrequest import TimeSeriesRequest

# process data
from pythalesians.economics.seasonality.seasonality import Seasonality
from pythalesians.timeseries.calcs.timeseriescalcs import TimeSeriesCalcs

# displaying data
from pythalesians.graphics.graphs.plotfactory import PlotFactory
from pythalesians.graphics.graphs.graphproperties import GraphProperties

# logging
from pythalesians.util.loggermanager import LoggerManager

import datetime

seasonality = Seasonality()
tsc = TimeSeriesCalcs()
logger = LoggerManager().getLogger(__name__)

pf = PlotFactory()

###### calculate seasonal moves in EUR/USD and GBP/USD
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
    gp.title = 'FX spot moves by time of year'

    pf.plot_line_graph(day_of_month_seasonality, adapter='pythalesians', gp = gp)