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
LoaderBBG

Abstract class for download of Bloomberg daily, intraday data and reference data.

Implemented by
- LoaderBBGCOM (old style Windows 32bit COM access to Bloomberg)
- LoaderBBGOpen (adapted version of new Bloomberg Open API for Python - recommended - although requires compilation)

"""

import datetime
import abc

import pandas

from pythalesians.util.loggermanager import LoggerManager
from pythalesians.market.loaders.lowlevel.loadertemplate import LoaderTemplate

class LoaderBBG(LoaderTemplate):

    def __init__(self):
        super(LoaderBBG, self).__init__()
        self.logger = LoggerManager().getLogger(__name__)

    # implement method in abstract superclass
    def load_ticker(self, time_series_request):
        """
        load_ticker - Retrieves market data from external data source (in this case Bloomberg)

        Parameters
        ----------
        time_series_request : TimeSeriesRequest
            contains all the various parameters detailing time series start and finish, tickers etc

        Returns
        -------
        DataFrame
        """

        time_series_request_vendor = self.construct_vendor_time_series_request(time_series_request)

        data_frame = None
        self.logger.info("Request Bloomberg data")

        # do we need daily or intraday data?
        if (time_series_request.freq in ['daily', 'weekly', 'monthly', 'quarterly', 'yearly']):

            # for events times/dates separately needs ReferenceDataRequest (when specified)
            if 'release-date-time-full' in time_series_request.fields:
                # experimental
                datetime_data_frame = self.get_reference_data(time_series_request_vendor, time_series_request)

                # remove fields 'release-date-time-full' from our request (and the associated field in the vendor)
                index = time_series_request.fields.index('release-date-time-full')
                time_series_request_vendor.fields.pop(index)
                time_series_request.fields.pop(index)

                # download all the other event fields (uses HistoricalDataRequest to Bloomberg)
                # concatenate with date time fields
                if len(time_series_request_vendor.fields) > 0:
                    events_data_frame = self.get_daily_data(time_series_request, time_series_request_vendor)

                    col = events_data_frame.index.name
                    events_data_frame = events_data_frame.reset_index(drop = False)

                    data_frame = pandas.concat([events_data_frame, datetime_data_frame], axis = 1)
                    temp = data_frame[col]
                    del data_frame[col]
                    data_frame.index = temp
                else:
                    data_frame = datetime_data_frame

            # for all other daily/monthly/quarter data, we can use HistoricalDataRequest to Bloomberg
            else:
                data_frame = self.get_daily_data(time_series_request, time_series_request_vendor)

        # assume one ticker only
        # for intraday data we use IntradayDataRequest to Bloomberg
        if (time_series_request.freq in ['tick', 'intraday', 'second', 'minute', 'hourly']):
            time_series_request_vendor.tickers = time_series_request_vendor.tickers[0]

            if time_series_request.freq in ['tick', 'second']:
                data_frame = self.download_tick(time_series_request_vendor)
            else:
                data_frame = self.download_intraday(time_series_request_vendor)

            if data_frame is not None:
                if data_frame.empty:
                    self.logger.info("No tickers returned for: " + time_series_request_vendor.tickers)

                    return None

                cols = data_frame.columns.values
                data_frame = data_frame.tz_localize('UTC')
                cols = time_series_request.tickers[0] + "." + cols
                data_frame.columns = cols

        self.logger.info("Completed request from Bloomberg.")

        return data_frame

    def get_daily_data(self, time_series_request, time_series_request_vendor):
        data_frame = self.download_daily(time_series_request_vendor)

        # convert from vendor to Thalesians tickers/fields
        if data_frame is not None:
            if data_frame.empty:
                self.logger.info("No tickers returned for...")

                try:
                    self.logger.info(str(time_series_request_vendor.tickers))
                except: pass

                return None

            returned_fields = data_frame.columns.get_level_values(0)
            returned_tickers = data_frame.columns.get_level_values(1)

            # TODO if empty try downloading again a year later
            fields = self.translate_from_vendor_field(returned_fields, time_series_request)
            tickers = self.translate_from_vendor_ticker(returned_tickers, time_series_request)

            ticker_combined = []

            for i in range(0, len(fields)):
                ticker_combined.append(tickers[i] + "." + fields[i])

            data_frame.columns = ticker_combined
            data_frame.index.name = 'Date'

        return data_frame

    def get_reference_data(self, time_series_request_vendor, time_series_request):
        end = datetime.datetime.today()
        end = end.replace(year = end.year + 1)

        time_series_request_vendor.finish_date = end

        self.logger.debug("Requesting ref for " + time_series_request_vendor.tickers[0] + " etc.")

        data_frame = self.download_ref(time_series_request_vendor)

        self.logger.debug("Waiting for ref...")

        # convert from vendor to Thalesians tickers/fields
        if data_frame is not None:
            returned_fields = data_frame.columns.get_level_values(0)
            returned_tickers = data_frame.columns.get_level_values(1)

        if data_frame is not None:
            # TODO if empty try downloading again a year later
            fields = self.translate_from_vendor_field(returned_fields, time_series_request)
            tickers = self.translate_from_vendor_ticker(returned_tickers, time_series_request)

            ticker_combined = []

            for i in range(0, len(fields)):
                ticker_combined.append(tickers[i] + "." + fields[i])

            data_frame.columns = ticker_combined

            # TODO coerce will be deprecated from pandas
            data_frame = data_frame.convert_objects(convert_dates = 'coerce', convert_numeric= 'coerce')

        return data_frame

    # implement method in abstract superclass
    @abc.abstractmethod
    def kill_session(self):
        return

    @abc.abstractmethod
    def download_tick(self, time_series_request):
        return

    @abc.abstractmethod
    def download_intraday(self, time_series_request):
        return

    @abc.abstractmethod
    def download_daily(self, time_series_request):
        return

    @abc.abstractmethod
    def download_ref(self, time_series_request):
        return
