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
bokeh_examples

Shows how to plot using Bokeh library.

"""

import datetime
from pythalesians.market.loaders.lighttimeseriesfactory import LightTimeSeriesFactory
from pythalesians.market.requests.timeseriesrequest import TimeSeriesRequest
from pythalesians.timeseries.calcs.timeseriescalcs import TimeSeriesCalcs

from pythalesians.graphics.graphs.plotfactory import PlotFactory
from pythalesians.graphics.graphs.graphproperties import GraphProperties

if True:
    time_series_request = TimeSeriesRequest(
                start_date = "01 Jan 2013",                     # start date
                finish_date = datetime.date.today(),            # finish date
                freq = 'daily',                                 # daily data
                data_source = 'google',                         # use Bloomberg as data source
                tickers = ['Apple', 'S&P500 ETF'],                  # ticker (Thalesians)
                fields = ['close'],                                 # which fields to download
                vendor_tickers = ['aapl', 'spy'],                   # ticker (Google)
                vendor_fields = ['Close'],                          # which Bloomberg fields to download
                cache_algo = 'internet_load_return')                # how to return data

    ltsf = LightTimeSeriesFactory()
    tsc = TimeSeriesCalcs()

    df = tsc.create_mult_index_from_prices(ltsf.harvest_time_series(time_series_request))

    gp = GraphProperties()
    gp.html_file_output = "output_data/apple.htm"
    gp.title = "S&P500 vs Apple"

    # plot first with PyThalesians and then Bokeh
    # just needs 1 word to change
    gp.display_legend = False

    pf = PlotFactory()
    pf.plot_generic_graph(df, type = 'line', adapter = 'pythalesians', gp = gp)
    pf.plot_generic_graph(df, type = 'line', adapter = 'bokeh', gp = gp)

# test simple Bokeh bar charts - monthly returns over past 6 months
if True:
    from datetime import timedelta
    ltsf = LightTimeSeriesFactory()

    end = datetime.datetime.utcnow()
    start = end - timedelta(days=180)

    tickers = ['S&P500', 'FTSE', 'Nikkei']
    vendor_tickers = ['SPX Index', 'UKX Index', 'NKY Index']

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

    # resample for end of month
    daily_vals = daily_vals.resample('BM')

    daily_vals = daily_vals / daily_vals.shift(1) - 1
    daily_vals.index = [str(x.year) + '/' + str(x.month) for x in daily_vals.index]
    daily_vals = daily_vals.drop(daily_vals.head(1).index)

    pf = PlotFactory()

    gp = GraphProperties()

    gp.source = 'Thalesians/BBG (created with PyThalesians Python library)'
    gp.html_file_output = "output_data/equities.htm"
    gp.title = 'Recent monthly changes in equity markets'
    gp.scale_factor = 2
    gp.display_legend = True
    gp.chart_type = ['bar', 'scatter', 'line']
    gp.x_title = 'Dates'
    gp.y_title = 'Pc'

    # plot using Bokeh then PyThalesians
    pf.plot_bar_graph(daily_vals * 100, adapter = 'bokeh', gp = gp)
    pf.plot_bar_graph(daily_vals * 100, adapter = 'pythalesians', gp = gp)

# plot daily changes in FX
if True:
    from datetime import timedelta
    ltsf = LightTimeSeriesFactory()

    end = datetime.datetime.utcnow()
    start = end - timedelta(days=5)

    tickers = ['EUR', 'GBP', 'AUD', 'NZD', 'CAD', 'CHF', 'NOK', 'SEK', 'JPY']
    vendor_tickers = [x + 'USD BGN Curncy' for x in tickers]

    time_series_request = TimeSeriesRequest(
        start_date = start,                                             # start date
        finish_date = end,                                              # finish date
        freq = 'daily',                                                 # daily data
        data_source = 'bloomberg',                                      # use Bloomberg as data source
        tickers = tickers,                                              # ticker (Thalesians)
        fields = ['close'],                                             # which fields to download
        vendor_tickers = vendor_tickers,                # ticker (Bloomberg)
        vendor_fields = ['PX_LAST'],                    # which Bloomberg fields to download
        cache_algo = 'internet_load_return')                # how to return data

    daily_vals = ltsf.harvest_time_series(time_series_request)

    daily_vals = daily_vals / daily_vals.shift(1) - 1

    last_row_name = daily_vals.index[-1]
    daily_vals = daily_vals.T.sort(columns=last_row_name).T

    daily_vals.columns = [x.replace('.close', '') for x in daily_vals.columns.values]

    daily_vals = daily_vals.tail(1)
    daily_vals = daily_vals.T

    pf = PlotFactory()

    gp = GraphProperties()

    gp.source = 'Thalesians/BBG (created with PyThalesians Python library)'
    gp.html_file_output = "output_data/FX.htm"
    gp.file_output = "output_data/daily-fx-changes.png"
    gp.title = 'FX changes today (vs USD)'
    gp.scale_factor = 3
    gp.display_legend = True
    gp.x_title = 'Dates'
    gp.y_title = 'Pc'

    # plot using Bokeh then PyThalesians
    pf.plot_bar_graph(daily_vals * 100, adapter = 'bokeh', gp = gp)
    pf.plot_bar_graph(daily_vals * 100, adapter = 'pythalesians', gp = gp)