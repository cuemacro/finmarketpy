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
twitterpythalesians_examples

Gives example of how to update Twitter status with text and plot directly (as opposed to via PlotFactory)

"""

from pythalesians.util.twitterpythalesians import TwitterPyThalesians

if False:
    APP_KEY             = "XXXX"
    APP_SECRET          = "XXXX"
    OAUTH_TOKEN	        = "XXXX"
    OAUTH_TOKEN_SECRET	= "XXXX"

    pytwitter = TwitterPyThalesians()
    pytwitter.set_key(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

    from pythalesians.market.requests.timeseriesrequest import TimeSeriesRequest
    from pythalesians.market.loaders.lighttimeseriesfactory import LightTimeSeriesFactory

    import datetime

    from pythalesians.graphics.graphs.plotfactory import PlotFactory
    from pythalesians.graphics.graphs.graphproperties import GraphProperties

    end = datetime.datetime.utcnow()
    start_date = end.replace(hour=0, minute=0, second=0, microsecond=0) # Returns a copy

    time_series_request = TimeSeriesRequest(
                start_date = start_date,         # start date
                finish_date = datetime.datetime.utcnow(),                       # finish date
                freq = 'intraday',                                              # intraday data
                data_source = 'bloomberg',                      # use Bloomberg as data source
                tickers = ['EURUSD'] ,                          # ticker (Thalesians)
                fields = ['close'],                             # which fields to download
                vendor_tickers = ['EURUSD BGN Curncy'],         # ticker (Bloomberg)
                vendor_fields = ['close'],                      # which Bloomberg fields to download
                cache_algo = 'internet_load_return')            # how to return data

    ltsf = LightTimeSeriesFactory()

    df = ltsf.harvest_time_series(time_series_request)
    df.columns = [x.replace('.close', '') for x in df.columns.values]

    gp = GraphProperties()

    gp.title = 'EURUSD stuff!'
    gp.file_output = 'EURUSD.png'
    gp.source = 'Thalesians/BBG (created with PyThalesians Python library)'

    pf = PlotFactory()
    pf.plot_line_graph(df, adapter = 'pythalesians', gp = gp)

    pytwitter.update_status("check out my plot of EUR/USD!", picture = gp.file_output)
