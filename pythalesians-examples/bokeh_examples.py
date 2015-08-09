__author__ = 'saeedamen'

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
    gp.html_file_output = "apple.htm"
    gp.title = "S&P500 vs Apple"

    # plot first with PyThalesians and then Plotly (via Cufflinks)
    # just needs 1 word to change
    # (although, note that AdapterCufflinks does have some extra parameters that can be set in
    # GraphProperties)
    gp.display_legend = False

    pf = PlotFactory()
    pf.plot_generic_graph(df, type = 'line', adapter = 'pythalesians', gp = gp)
    pf.plot_generic_graph(df, type = 'line', adapter = 'bokeh', gp = gp)