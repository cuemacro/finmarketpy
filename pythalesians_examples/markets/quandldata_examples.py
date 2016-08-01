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
quandldata_examples

Gives several examples of how to download market data from Quandl using LightTimeSeriesFactory, with multiple fields.
Also uses PlotFactory to do basic plots.

"""

# for logging
from chartesians.graphs.plotfactory import PlotFactory

from pythalesians.market.loaders.lighttimeseriesfactory import LightTimeSeriesFactory
from pythalesians.market.requests.timeseriesrequest import TimeSeriesRequest
from pythalesians.util.loggermanager import LoggerManager

# for making elementary calculations on the time series

if True:
    logger = LoggerManager().getLogger(__name__)

    import datetime

    # just change "False" to "True" to run any of the below examples

    ###### download daily data from quandl for S&P500 and then plot
    if True:

        time_series_request = TimeSeriesRequest(
                start_date = "01 Jan 2014",                     # start date
                finish_date = datetime.date.today(),            # finish date
                freq = 'daily',                                 # daily data
                data_source = 'quandl',                         # use quandl as data source
                tickers = ['S&P500'],                            # ticker (Thalesians)
                fields = ['close', 'open', 'adjusted-close', 'high'],           # which fields to download
                vendor_tickers = ['YAHOO/INDEX_GSPC'],                           # ticker (quandl)
                vendor_fields = ['close', 'open', 'adjusted-close', 'high'],    # which quandl fields to download
                cache_algo = 'internet_load_return')                            # how to return data

        ltsf = LightTimeSeriesFactory()

        df = None
        df = ltsf.harvest_time_series(time_series_request)

        pf = PlotFactory()
        pf.plot_line_graph(df, adapter = 'pythalesians')

    ###### download monthly quandl data for Total US nonfarm payrolls
    if True:
        time_series_request = TimeSeriesRequest(
            start_date="01 Jan 1940",  # start date
            finish_date=datetime.date.today(),  # finish date
            freq='daily',  # daily data
            data_source='quandl',  # use quandl as data source
            tickers=['US Total Nonfarm Payrolls'],  # ticker (Thalesians)
            fields=['close'],  # which fields to download
            vendor_tickers=['FRED/PAYEMS'],  # ticker (quandl)
            vendor_fields=['close'],  # which quandl fields to download
            cache_algo='internet_load_return')  # how to return data

        ltsf = LightTimeSeriesFactory()

        df = None
        df = ltsf.harvest_time_series(time_series_request)

        pf = PlotFactory()
        pf.plot_line_graph(df, adapter='plotly')



