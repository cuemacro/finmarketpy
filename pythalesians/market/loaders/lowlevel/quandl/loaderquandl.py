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
LoaderQuandl

Class for reading in data from Quandl into PyThalesians library

"""

# support Quandl 3.x.x
try:
    import quandl as Quandl
except:
    # if import fails use Quandl 2.x.x
    import Quandl

from pythalesians.util.loggermanager import LoggerManager
from pythalesians.market.loaders.lowlevel.loadertemplate import LoaderTemplate
from pythalesians.util.constants import Constants

class LoaderQuandl(LoaderTemplate):

    def __init__(self):
        super(LoaderQuandl, self).__init__()
        self.logger = LoggerManager().getLogger(__name__)

    # implement method in abstract superclass
    def load_ticker(self, time_series_request):
        time_series_request_vendor = self.construct_vendor_time_series_request(time_series_request)

        self.logger.info("Request Quandl data")

        data_frame = self.download_daily(time_series_request_vendor)

        if data_frame is None or data_frame.index is []: return None

        # convert from vendor to Thalesians tickers/fields
        if data_frame is not None:
            returned_tickers = data_frame.columns

        if data_frame is not None:
            # tidy up tickers into a format that is more easily translatable
            returned_tickers = [x.replace(' - Value', '') for x in returned_tickers]
            returned_tickers = [x.replace(' - VALUE', '') for x in returned_tickers]
            returned_tickers = [x.replace('.', '/') for x in returned_tickers]

            fields = self.translate_from_vendor_field(['close' for x in returned_tickers], time_series_request)
            tickers = self.translate_from_vendor_ticker(returned_tickers, time_series_request)

            ticker_combined = []

            for i in range(0, len(fields)):
                ticker_combined.append(tickers[i] + "." + fields[i])

            data_frame.columns = ticker_combined
            data_frame.index.name = 'Date'

        self.logger.info("Completed request from Quandl.")

        return data_frame

    def download_daily(self, time_series_request):
        trials = 0

        data_frame = None

        while(trials < 5):
            try:
                data_frame = Quandl.get(time_series_request.tickers, authtoken=Constants().quandl_api_key, trim_start=time_series_request.start_date,
                            trim_end=time_series_request.finish_date)

                break
            except:
                trials = trials + 1
                self.logger.info("Attempting... " + str(trials) + " request to download from Quandl")

        if trials == 5:
            self.logger.error("Couldn't download from Quandl after several attempts!")

        return data_frame

