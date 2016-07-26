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
plotly_examples

Shows how to plot using Plotly library (uses Jorge Santos' Cufflinks wrapper)

"""

import datetime
from pythalesians.market.loaders.lighttimeseriesfactory import LightTimeSeriesFactory
from pythalesians.market.requests.timeseriesrequest import TimeSeriesRequest
from pythalesians.timeseries.calcs.timeseriescalcs import TimeSeriesCalcs

from pythalesians.graphics.graphs.plotfactory import PlotFactory
from pythalesians.graphics.graphs.graphproperties import GraphProperties


if True:
    import pandas
    df = pandas.read_csv("volsurface.csv")  # load a snapshot for a vol surface from disk

    gp = GraphProperties()
    gp.plotly_plot_mode = "offline_html"    # render Plotly plot locally (rather than via website)
    gp.file_output = "volsurface.png"       # save as static PNG file
    gp.html_file_output = "volsurface.html" # save as interactive HTML file

    gp.title = "GBP/USD vol surface"
    gp.color = 'Blues'

    # plot surface with Plotly
    pf = PlotFactory()
    pf.plot_generic_graph(df, type = 'surface', adapter = 'cufflinks', gp = gp)

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
    gp.title = "S&P500 vs Apple"

    # plot first with PyThalesians and then Plotly (via Cufflinks)
    # just needs 1 word to change
    # (although, note that AdapterCufflinks does have some extra parameters that can be set in GraphProperties)
    gp.plotly_username = 'thalesians'   # note: need to fill in Plotly API key on Constants and change this!
    gp.plotly_world_readable = True
    gp.plotly_plot_mode = "online"      # will render on Plotly website

    pf = PlotFactory()
    pf.plot_generic_graph(df, type = 'line', adapter = 'pythalesians', gp = gp)
    pf.plot_generic_graph(df, type = 'line', adapter = 'cufflinks', gp = gp)

# test simple Plotly bar charts - average differences in EURUSDV1M-1Y vol and USDJPYV1M-1Y slope over past sixth months
if True:
    from datetime import timedelta
    ltsf = LightTimeSeriesFactory()

    end = datetime.datetime.utcnow()
    start = end - timedelta(days=180)

    tickers = ['EURUSDV1M', 'EURUSDV1Y', 'USDJPYV1M', 'USDJPYV1Y']
    vendor_tickers = ['EURUSDV1M BGN Curncy', 'EURUSDV1Y BGN Curncy', 'USDJPYV1M BGN Curncy', 'USDJPYV1Y BGN Curncy']

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

    df = ltsf.harvest_time_series(time_series_request)

    import pandas

    df.columns = [x.replace('.close', '') for x in df.columns.values]

    short_dates = df[["EURUSDV1M", "USDJPYV1M"]]
    long_dates = df[["EURUSDV1Y", "USDJPYV1Y"]]
    short_dates, long_dates = short_dates.align(long_dates, join='left', axis = 0)

    slope = pandas.DataFrame(data = short_dates.values - long_dates.values, index = short_dates.index,
            columns = ["EURUSDV1M-1Y", "USDJPYV1M-1Y"])

    # resample fand calculate average over month
    slope_monthly = slope.resample('M').mean()

    slope_monthly.index = [str(x.year) + '/' + str(x.month) for x in slope_monthly.index]

    pf = PlotFactory()

    gp = GraphProperties()

    gp.source = 'Thalesians/BBG'
    gp.title = 'Vol slopes in EUR/USD and USD/JPY recently'
    gp.scale_factor = 2
    gp.display_legend = True
    gp.chart_type = 'bar'
    gp.x_title = 'Dates'
    gp.y_title = 'Pc'

    # plot using Cufflinks
    pf.plot_bar_graph(slope_monthly, adapter = 'cufflinks', gp = gp)