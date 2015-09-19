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
HistEconDataFactory

Provides functions for getting historical economic data. Uses aliases for tickers, to make it relatively easy to use,
rather than having to remember all the underlying vendor tickers. Can use Fred, Quandl or Bloomberg.

The files below, contain default tickers and country groups. However, you can add whichever tickers you'd like.
- conf/all_econ_tickers.csv
- conf/econ_country_codes.csv
- conf/econ_country_groups.csv

These can be automatically generated via conf/econ_tickers.xlsm

"""

from pythalesians.util.loggermanager import LoggerManager

from pythalesians.market.requests.timeseriesrequest import TimeSeriesRequest
from pythalesians.market.loaders.lighttimeseriesfactory import LightTimeSeriesFactory

from pythalesians.util.constants import Constants

import pandas

import datetime

class HistEconDataFactory:

    def __init__(self):
        self.logger = LoggerManager().getLogger(__name__)

        self._all_econ_tickers = pandas.read_csv(Constants().all_econ_tickers)
        self._econ_country_codes = pandas.read_csv(Constants().econ_country_codes)
        self._econ_country_groups = pandas.read_csv(Constants().econ_country_groups)

        self.time_series_factory = LightTimeSeriesFactory()

        # if Constants().default_time_series_factory == 'lighttimeseriesfactory':
        #     self.time_series_factory = LightTimeSeriesFactory()
        # else:
        #     self.time_series_factory = CachedTimeSeriesFactory()
        # return

    def get_economic_data_history(self, start_date, finish_date, country_group, data_type,
        source = 'fred', cache_algo = "internet_load_return"):

        #vendor_country_codes = self.fred_country_codes[country_group]
        #vendor_pretty_country = self.fred_nice_country_codes[country_group]

        if isinstance(country_group, list):
            pretty_country_names = country_group
        else:
            # get all the country names in the country_group
            pretty_country_names = list(self._econ_country_groups[
                self._econ_country_groups["Country Group"] == country_group]['Country'])

        # construct the pretty tickers
        pretty_tickers = [x + '-' + data_type for x in pretty_country_names]

        # get vendor tickers
        vendor_tickers = []

        for pretty_ticker in pretty_tickers:
            vendor_ticker = list(self._all_econ_tickers[
                                         self._all_econ_tickers["Full Code"] == pretty_ticker][source].values)

            if vendor_ticker == []:
                vendor_ticker = None
                self.logger.error('Could not find match for ' + pretty_ticker)
            else:
                vendor_ticker = vendor_ticker[0]

            vendor_tickers.append(vendor_ticker)

        vendor_fields = ['close']

        if source == 'bloomberg': vendor_fields = ['PX_LAST']

        time_series_request = TimeSeriesRequest(
                start_date = start_date,                            # start date
                finish_date = finish_date,                          # finish date
                category = 'economic',
                freq = 'daily',                                     # intraday data
                data_source = source,                               # use Bloomberg as data source
                cut = 'LOC',
                tickers = pretty_tickers,
                fields = ['close'],                                 # which fields to download
                vendor_tickers = vendor_tickers,
                vendor_fields = vendor_fields,                      # which Bloomberg fields to download
                cache_algo = cache_algo)                            # how to return data

        return self.time_series_factory.harvest_time_series(time_series_request)

    def grasp_coded_entry(self, df, index):
        df = df.ix[index:].stack()
        df = df.reset_index()
        df.columns = ['Date', 'Name', 'Val']

        countries = df['Name']

        countries = [x.split('-', 1)[0] for x in countries]

        df['Code'] = sum(
            [list(self._econ_country_codes[self._econ_country_codes["Country"] == x]['Code']) for x in countries],
            [])

        return df

if __name__ == '__main__':
    pass
    # see examples/histecondata_examples for ideas on how to call


