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
techindicator_examples

Gives examples of how to calculate technical indicators with PyThalesians.

"""

###### Plot EUR/USD and GBP/USD 20D SMA
if True:
    from pythalesians.market.loaders.lighttimeseriesfactory import LightTimeSeriesFactory
    from pythalesians.market.requests.timeseriesrequest import TimeSeriesRequest
    from pythalesians.timeseries.techind.techindicator import TechIndicator
    from pythalesians.timeseries.techind.techparams import TechParams
    from chartesians.graphs.plotfactory import PlotFactory

    import datetime

    time_series_request = TimeSeriesRequest(
        start_date="01 Jan 1970",  # start date
        finish_date=datetime.date.today(),  # finish date
        freq='daily',  # daily data
        data_source='quandl',  # use Quandl as data source
        tickers=['EURUSD',  # ticker (Thalesians)
                 'GBPUSD'],
        fields=['close'],  # which fields to download
        vendor_tickers=['FRED/DEXUSEU', 'FRED/DEXUSUK'],  # ticker (Quandl)
        vendor_fields=['close'],  # which Bloomberg fields to download
        cache_algo='internet_load_return')  # how to return data

    ltsf = LightTimeSeriesFactory()

    daily_vals = ltsf.harvest_time_series(time_series_request)

    techind = TechIndicator()
    tech_params = TechParams()
    tech_params.sma_period = 20

    techind.create_tech_ind(daily_vals, 'SMA', tech_params=tech_params)

    sma = techind.get_techind()
    signal = techind.get_signal()

    combine = daily_vals.join(sma, how='outer')

    pf = PlotFactory()
    pf.plot_line_graph(combine, adapter='pythalesians')
