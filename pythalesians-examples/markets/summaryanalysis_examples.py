__author__ = 'saeedamen'

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
summaryanalysis_examples

Gives several examples of basic summary type of analysis on data, such as choosing top daily moves.

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
from datetime import timedelta

if True:
    logger = LoggerManager().getLogger(__name__)

    import datetime

    # just change "False" to "True" to run any of the below examples

    ###### download daily data from Bloomberg for USD/BRL and get biggest downmoves
    if True:
        tsc = TimeSeriesCalcs()

        time_series_request = TimeSeriesRequest(
                start_date = "01 Jan 2005",                     # start date
                finish_date = datetime.datetime.utcnow(),       # finish date
                freq = 'daily',                                 # daily data
                data_source = 'bloomberg',                      # use Bloomberg as data source
                tickers = ['USDBRL'] ,                          # ticker (Thalesians)
                fields = ['close'],                             # which fields to download
                vendor_tickers = ['USDBRL BGN Curncy'],         # ticker (Bloomberg)
                vendor_fields = ['PX_LAST'],                    # which Bloomberg fields to download
                cache_algo = 'internet_load_return')            # how to return data

        ltsf = LightTimeSeriesFactory()

        df = ltsf.harvest_time_series(time_series_request)
        df.columns = [x.replace('.close', '') for x in df.columns.values]

        df = tsc.calculate_returns(df) * 100
        df = df.dropna()

        df_sorted = tsc.get_bottom_valued_sorted(df, "USDBRL", n = 20)
        # df = tsc.get_top_valued_sorted(df, "USDBRL", n = 20) # get biggest up moves

        # get values on day after
        df2 = df.shift(-1)
        df2 = df2.ix[df_sorted.index]
        df2.columns = ['T+1']

        df_sorted.columns = ['T']

        df_sorted = df_sorted.join(df2)
        df_sorted.index = [str(x.year) + '/' + str(x.month) + '/' + str(x.day) for x in df_sorted.index]

        gp = GraphProperties()
        gp.title = 'Largest daily falls in USDBRL'
        gp.scale_factor = 3
        gp.display_legend = True
        gp.chart_type = 'bar'
        gp.x_title = 'Dates'
        gp.y_title = 'Pc'
        gp.file_output = "usdbrl-biggest-downmoves.png"

        pf = PlotFactory()
        pf.plot_line_graph(df_sorted, adapter = 'pythalesians', gp=gp)
