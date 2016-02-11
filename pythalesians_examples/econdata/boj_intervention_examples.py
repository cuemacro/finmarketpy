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
boj_intervention_examples

Shows how to plot data from FRED on BoJ intervention in USDJPY against USDJPY grabbed from Bloomberg

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

    ###### download daily data from Bloomberg for USD/JPY
    ###### download BoJ intervention data from FRED
    if True:

        time_series_request = TimeSeriesRequest(
                start_date = "01 Jan 1995",                     # start date
                finish_date = datetime.date.today(),            # finish date
                freq = 'daily',                                 # daily data
                data_source = 'bloomberg',                      # use Bloomberg as data source
                tickers = ['USDJPY'],                            # ticker (Thalesians)
                fields = ['close'],              # which fields to download
                vendor_tickers = ['USDJPY BGN Curncy'],         # ticker (Bloomberg)
                vendor_fields = ['PX_LAST'],   # which Bloomberg fields to download
                cache_algo = 'internet_load_return')                # how to return data

        ltsf = LightTimeSeriesFactory()

        df = None
        df = ltsf.harvest_time_series(time_series_request)

        df.columns = [x.replace('.close', '') for x in df.columns.values]

        time_series_request.tickers = ['USDJPY purchases (bn USD)']
        time_series_request.vendor_tickers = ['JPINTDUSDJPY']
        time_series_request.data_source = 'fred'

        df_fred = ltsf.harvest_time_series(time_series_request)
        df_fred.columns = [x.replace('.close', '') for x in df_fred.columns.values]

        # convert to USD bn
        # df_fred = (df_fred * 10000000)
        df = df.join(df_fred, how="outer")
        df['USDJPY'] = df['USDJPY'].ffill()

        # data is in 100 million JPY, divide by 10 to get into 1000 million (ie. 1 billion)
        # divide by USD/JPY spot to get into USD
        df['USDJPY purchases (bn USD)'] = (df['USDJPY purchases (bn USD)'] / df['USDJPY']) / 10

        gp = GraphProperties()
        gp.scale_factor = 3

        gp.title = "BoJ USDJPY buying"
        gp.file_output = "output_data/" + datetime.date.today().strftime("%Y%m%d") + " USDJPY BoJ intervention " \
                         + str(gp.scale_factor) + ".png"

        gp.source = 'Thalesians/BBG (created with PyThalesians Python library)'

        gp.y_axis_2_series = ['USDJPY purchases (bn USD)']
        gp.color_2_series = gp.y_axis_2_series
        gp.color_2 = ['blue']

        pf = PlotFactory()
        pf.plot_line_graph(df, adapter = 'pythalesians', gp = gp)
