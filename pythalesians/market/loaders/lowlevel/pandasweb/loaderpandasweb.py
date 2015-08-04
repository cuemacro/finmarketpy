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
LoaderPandasWeb

Class for reading in data from various web sources into PyThalesians library including

- Yahoo! Finance - yahoo
- Google Finance - google
- St. Louis FED (FRED) - fred
- Kenneth French data library - famafrench
- World Bank - wb

"""

import pandas.io.data as web
import pandas

from pythalesians.util.loggermanager import LoggerManager
from pythalesians.market.loaders.lowlevel.loadertemplate import LoaderTemplate


class LoaderPandasWeb(LoaderTemplate):

    def __init__(self):
        super(LoaderPandasWeb, self).__init__()
        self.logger = LoggerManager().getLogger(__name__)

    # implement method in abstract superclass
    def load_ticker(self, time_series_request):
        time_series_request_vendor = self.construct_vendor_time_series_request(time_series_request)

        self.logger.info("Request Pandas Web data")

        data_frame = self.download_daily(time_series_request_vendor)

        if time_series_request_vendor.data_source == 'fred':
            returned_fields = ['close' for x in data_frame.columns.values]
            returned_tickers = data_frame.columns.values
        else:
            data_frame = data_frame.to_frame().unstack()

            print(data_frame.tail())

            if data_frame.index is []: return None

            # convert from vendor to Thalesians tickers/fields
            if data_frame is not None:
                returned_fields = data_frame.columns.get_level_values(0)
                returned_tickers = data_frame.columns.get_level_values(1)

        if data_frame is not None:
            fields = self.translate_from_vendor_field(returned_fields, time_series_request)
            tickers = self.translate_from_vendor_ticker(returned_tickers, time_series_request)

            ticker_combined = []

            for i in range(0, len(fields)):
                ticker_combined.append(tickers[i] + "." + fields[i])

            ticker_requested = []

            for f in time_series_request.fields:
                for t in time_series_request.tickers:
                    ticker_requested.append(t + "." + f)

            data_frame.columns = ticker_combined
            data_frame.index.name = 'Date'

            # only return the requested tickers
            data_frame = pandas.DataFrame(data = data_frame[ticker_requested],
                                          index = data_frame.index, columns = ticker_requested)

        self.logger.info("Completed request from Pandas Web.")

        return data_frame

    def download_daily(self, time_series_request):
        return web.DataReader(time_series_request.tickers, time_series_request.data_source, time_series_request.start_date, time_series_request.finish_date)
