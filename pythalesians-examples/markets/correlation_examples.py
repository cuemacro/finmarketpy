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
correlation_examples

Gives several examples of how to compute and plot correlations of assets.

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

if True:
    logger = LoggerManager().getLogger(__name__)

    import datetime

    # just change "False" to "True" to run any of the below examples

    ###### download daily data from Bloomberg for EUR/USD and GBP/USD spot, then calculate correlation
    if True:

        time_series_request = TimeSeriesRequest(
                start_date = "01 Jan 2014",                     # start date
                finish_date = datetime.date.today(),            # finish date
                freq = 'daily',                                 # daily data
                data_source = 'bloomberg',                      # use Bloomberg as data source
                tickers = ['EURUSD',                            # ticker (Thalesians)
                           'GBPUSD',
                           'AUDUSD'],
                fields = ['close'],                             # which fields to download
                vendor_tickers = ['EURUSD BGN Curncy',          # ticker (Bloomberg)
                                  'GBPUSD BGN Curncy',
                                  'AUDUSD BGN Curncy'],
                vendor_fields = ['PX_LAST'],                    # which Bloomberg fields to download
                cache_algo = 'internet_load_return')                # how to return data

        ltsf = LightTimeSeriesFactory()

        df = None
        df = ltsf.harvest_time_series(time_series_request)

        tsc = TimeSeriesCalcs()
        df = tsc.calculate_returns(df)
        df = tsc.rolling_corr(df['EURUSD.close'], 20, data_frame2 = df[['GBPUSD.close', 'AUDUSD.close']])

        gp = GraphProperties()
        gp.title = "1M FX rolling correlations"
        gp.scale_factor = 3

        pf = PlotFactory()
        pf.plot_line_graph(df, adapter = 'pythalesians', gp = gp)

    ###### download daily data from Bloomberg for AUD/JPY, NZD/JPY spot with S&P500, then calculate correlation
    if True:
        time_series_request = TimeSeriesRequest(
                start_date="01 Jan 2015",  # start date
                finish_date=datetime.date.today(),  # finish date
                freq='daily',  # daily data
                data_source='bloomberg',  # use Bloomberg as data source
                tickers=['AUDJPY',  # ticker (Thalesians)
                         'NZDJPY',
                         'S&P500'],
                fields=['close'],  # which fields to download
                vendor_tickers=['AUDJPY BGN Curncy',  # ticker (Bloomberg)
                                'NZDJPY BGN Curncy',
                                'SPX Index'],
                vendor_fields=['PX_LAST'],  # which Bloomberg fields to download
                cache_algo='internet_load_return')  # how to return data

        ltsf = LightTimeSeriesFactory()

        df = None
        df = ltsf.harvest_time_series(time_series_request)

        tsc = TimeSeriesCalcs()
        df = df.fillna(method='ffill')
        df = tsc.calculate_returns(df)
        df = tsc.rolling_corr(df['S&P500.close'], 20, data_frame2=df[['AUDJPY.close', 'NZDJPY.close']])

        gp = GraphProperties()
        gp.title = "1M FX rolling correlations"
        gp.scale_factor = 3

        pf = PlotFactory()
        pf.plot_line_graph(df, adapter='pythalesians', gp=gp)
