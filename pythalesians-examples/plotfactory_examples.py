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
plotfactory_examples

Examples to show how to use PlotFactory to make charts (at present only line charts have a lot of support).

"""
import datetime
from pythalesians.market.loaders.lighttimeseriesfactory import LightTimeSeriesFactory
from pythalesians.market.requests.timeseriesrequest import TimeSeriesRequest

from pythalesians.graphics.graphs.plotfactory import PlotFactory
from pythalesians.graphics.graphs.graphproperties import GraphProperties

if True:
    pf = PlotFactory()

    # test simple PyThalesians/Bokeh time series line charts
    if False:
        ltsf = LightTimeSeriesFactory()

        start = '01 Jan 2000'
        end = datetime.datetime.utcnow()
        tickers = ['AUDJPY', 'USDJPY']
        vendor_tickers = ['AUDJPY BGN Curncy', 'USDJPY BGN Curncy']

        time_series_request = TimeSeriesRequest(
                start_date = start,                             # start date
                finish_date = datetime.date.today(),            # finish date
                freq = 'daily',                                 # daily data
                data_source = 'bloomberg',                      # use Bloomberg as data source
                tickers = tickers,                              # ticker (Thalesians)
                fields = ['close'],                             # which fields to download
                vendor_tickers = vendor_tickers,                # ticker (Bloomberg)
                vendor_fields = ['PX_LAST'],                    # which Bloomberg fields to download
                cache_algo = 'internet_load_return')                # how to return data

        daily_vals = ltsf.harvest_time_series(time_series_request)

        pf = PlotFactory()

        gp = GraphProperties()

        gp.title = 'Spot values'
        gp.file_output = 'output_data/demo.png'
        gp.html_file_output = 'output_data/demo.htm'
        gp.source = 'Thalesians/BBG'

        # plot using PyThalesians
        pf.plot_line_graph(daily_vals, adapter = 'pythalesians', gp = gp)

        # plot using Bokeh (still needs a lot of work!)
        pf.plot_line_graph(daily_vals, adapter = 'bokeh', gp = gp)

    # do more complicated charts using several different Matplotib stylesheets (which have been customised)
    if False:
        ltsf = LightTimeSeriesFactory()

        # load market data
        start = '01 Jan 1970'
        end = datetime.datetime.utcnow()
        tickers = ['AUDJPY', 'USDJPY']
        vendor_tickers = ['AUDJPY BGN Curncy', 'USDJPY BGN Curncy']

        time_series_request = TimeSeriesRequest(
                start_date = start,                             # start date
                finish_date = datetime.date.today(),            # finish date
                freq = 'daily',                                 # daily data
                data_source = 'bloomberg',                      # use Bloomberg as data source
                tickers = tickers,                              # ticker (Thalesians)
                fields = ['close'],                             # which fields to download
                vendor_tickers = vendor_tickers,                # ticker (Bloomberg)
                vendor_fields = ['PX_LAST'],                    # which Bloomberg fields to download
                cache_algo = 'internet_load_return')                # how to return data

        daily_vals = ltsf.harvest_time_series(time_series_request)

        # plot data
        gp = GraphProperties()
        pf = PlotFactory()

        gp.title = 'Spot values'
        gp.file_output = 'output_data/demo.png'
        gp.scale_factor = 2
        gp.style_sheet = 'pythalesians'

        # first use PyThalesians matplotlib wrapper
        pf.plot_line_graph(daily_vals, adapter = 'pythalesians', gp = gp)
        pf.plot_generic_graph(daily_vals, gp = gp, type = 'line')

        # use modified 538 Matplotlib stylesheet
        gp.style_sheet = '538-pythalesians'
        pf.plot_line_graph(daily_vals, adapter = 'pythalesians', gp = gp)

        # use miletus matplotlib stylesheet
        gp.style_sheet = 'miletus-pythalesians'
        pf.plot_line_graph(daily_vals, adapter = 'pythalesians', gp = gp)

        # use ggplot matplotlib styleheet
        gp.scale_factor = 1
        gp.display_brand_label = False
        gp.display_source = False
        gp.style_sheet = 'ggplot-pythalesians'
        gp.display_mpld3 = True
        gp.html_file_output = 'output_data/demo.htm'
        pf.plot_line_graph(daily_vals, adapter = 'pythalesians', gp = gp)

        # now use PyThalesians bokeh wrapper (still needs a lot of work!)
        gp.scale_factor = 2
        gp.html_file_output = 'output_data/demo_bokeh.htm'
        pf.plot_line_graph(daily_vals, adapter = 'bokeh', gp = gp)

    # test simple PyThalesians bar charts - calculate yearly returns for various assets
    if False:
        ltsf = LightTimeSeriesFactory()

        start = '01 Jan 2000'
        end = datetime.datetime.utcnow()
        tickers = ['AUDJPY', 'USDJPY', 'EURUSD', 'S&P500']
        vendor_tickers = ['AUDJPY BGN Curncy', 'USDJPY BGN Curncy', 'EURUSD BGN Curncy', 'SPX Index']

        time_series_request = TimeSeriesRequest(
                start_date = start,                             # start date
                finish_date = datetime.date.today(),            # finish date
                freq = 'daily',                                 # daily data
                data_source = 'bloomberg',                      # use Bloomberg as data source
                tickers = tickers,                              # ticker (Thalesians)
                fields = ['close'],                             # which fields to download
                vendor_tickers = vendor_tickers,                # ticker (Bloomberg)
                vendor_fields = ['PX_LAST'],                    # which Bloomberg fields to download
                cache_algo = 'internet_load_return')                # how to return data

        daily_vals = ltsf.harvest_time_series(time_series_request)

        # resample for year end
        daily_vals = daily_vals.resample('A')

        daily_vals = daily_vals / daily_vals.shift(1) - 1
        daily_vals.index = daily_vals.index.year
        daily_vals = daily_vals.drop(daily_vals.head(1).index)

        pf = PlotFactory()

        gp = GraphProperties()

        gp.source = 'Thalesians/BBG'
        gp.title = 'Yearly changes in spot'
        gp.scale_factor = 3
        gp.y_title = "Percent Change"

        daily_vals = daily_vals * 100

        # plot using PyThalesians (stacked & then bar graph)
        pf.plot_stacked_graph(daily_vals, adapter = 'pythalesians', gp = gp)
        pf.plot_bar_graph(daily_vals, adapter = 'pythalesians', gp = gp)

