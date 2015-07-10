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
LoaderDukascopy

Class for downloading tick data from DukasCopy (note: past month of data is not available). Selecting very large
histories is not recommended as you will likely run out memory given the amount of data requested.

Parsing of files is rewritten version https://github.com/nelseric/ticks/
- parsing has been speeded up considerably
- on-the-fly downloading/parsing

"""

import requests
import pandas

import os
from datetime import timedelta

try:
    from numba import jit
finally:
    pass

# decompress binary files fetched from Dukascopy
try:
    import lzma
except ImportError:
    from backports import lzma

# for parsing binary files fetched from Dukascopy
import pythalesians.market.loaders.lowlevel.brokers.parserows

# abstract class on which this is based
from pythalesians.market.loaders.lowlevel.loadertemplate import LoaderTemplate

# for logging and constants
from pythalesians.util.loggermanager import LoggerManager
from pythalesians.util.constants import Constants

class LoaderDukasCopy(LoaderTemplate):
    tick_name  = "{symbol}/{year}/{month}/{day}/{hour}h_ticks.bi5"

    def __init__(self):
        super(LoaderTemplate, self).__init__()
        self.logger = LoggerManager().getLogger(__name__)

        import logging
        logging.getLogger("requests").setLevel(logging.WARNING)

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
        self.logger.info("Request Dukascopy data")

        # doesn't support non-tick data
        if (time_series_request.freq in ['daily', 'weekly', 'monthly', 'quarterly', 'yearly', 'intraday', 'minute', 'hourly']):
            self.logger.warning("Dukascopy loader is for tick data only")

            return None

        # assume one ticker only (LightTimeSeriesFactory only calls one ticker at a time)
        if (time_series_request.freq in ['tick']):
            # time_series_request_vendor.tickers = time_series_request_vendor.tickers[0]

            data_frame = self.get_tick(time_series_request, time_series_request_vendor)

            if data_frame is not None: data_frame.tz_localize('UTC')

        self.logger.info("Completed request from Dukascopy")

        return data_frame

    def kill_session(self):
        return

    def get_tick(self, time_series_request, time_series_request_vendor):

        data_frame = self.download_tick(time_series_request_vendor)

        # convert from vendor to Thalesians tickers/fields
        if data_frame is not None:
            returned_fields = data_frame.columns
            returned_tickers = [time_series_request_vendor.tickers[0]] * (len(returned_fields))

        if data_frame is not None:
            fields = self.translate_from_vendor_field(returned_fields, time_series_request)
            tickers = self.translate_from_vendor_ticker(returned_tickers, time_series_request)

            ticker_combined = []

            for i in range(0, len(fields)):
                ticker_combined.append(tickers[i] + "." + fields[i])

            data_frame.columns = ticker_combined
            data_frame.index.name = 'Date'

        return data_frame

    def download_tick(self, time_series_request):

        symbol = time_series_request.tickers[0]
        df_list = []

        self.logger.info("About to download from Dukascopy... for " + symbol)

        # single threaded
        df_list = [self.fetch_file(time, symbol) for time in
                   self.hour_range(time_series_request.start_date, time_series_request.finish_date)]

        # parallel (has pickle issues)
        # time_list = self.hour_range(time_series_request.start_date, time_series_request.finish_date)
        # df_list = Parallel(n_jobs=-1)(delayed(self.fetch_file)(time, symbol) for time in time_list)

        try:
            return pandas.concat(df_list)
        except:
            return None

    def fetch_file(self, time, symbol):
        if time.hour % 24 == 0: self.logger.info("Downloading... " + str(time))

        tick_path = self.tick_name.format(
                symbol = symbol,
                year = str(time.year).rjust(4, '0'),
                month = str(time.month).rjust(2, '0'),
                day = str(time.day).rjust(2, '0'),
                hour = str(time.hour).rjust(2, '0')
            )

        tick = self.fetch_tick(Constants().dukascopy_base_url + tick_path)

        if Constants().dukascopy_write_temp_tick_disk:
            out_path = Constants().temp_pythalesians_folder + "/dkticks/" + tick_path

            if not os.path.exists(out_path):
                if not os.path.exists(os.path.dirname(out_path)):
                    os.makedirs(os.path.dirname(out_path))

            self.write_tick(tick, out_path)

        try:
            return self.retrieve_df(lzma.decompress(tick), symbol, time)
        except:
            return None

    def fetch_tick(self, tick_url):
        i = 0
        tick_request = None

        # try up to 5 times to download
        while i < 5:
            try:
                tick_request = requests.get(tick_url)
                i = 5
            except:
                i = i + 1

        if (tick_request is None):
            self.logger("Failed to download from " + tick_url)
            return None

        return tick_request.content

    def write_tick(self, content, out_path):
        data_file = open(out_path, "wb+")
        data_file.write(content)
        data_file.close()

    def chunks(self, list, n):
        if n < 1:
            n = 1
        return [list[i:i + n] for i in range(0, len(list), n)]

    def retrieve_df(self, data, symbol, epoch):
        date, tuple = pythalesians.market.loaders.lowlevel.brokers.parserows.parse_tick_data(data, epoch)

        df = pandas.DataFrame(data = tuple, columns=['temp', 'bid', 'ask', 'bidv', 'askv'], index = date)
        df.drop('temp', axis = 1)
        df.index.name = 'Date'

        divisor = 100000

        # where JPY is the terms currency we have different divisor
        if symbol[3:6] == 'JPY':
            divisor = 1000

        # prices are returned without decimal point
        df['bid'] =  df['bid'] /  divisor
        df['ask'] =  df['ask'] / divisor

        return df

    def hour_range(self, start_date, end_date):
          delta_t = end_date - start_date

          delta_hours = (delta_t.days *  24.0) + (delta_t.seconds / 3600.0)
          for n in range(int (delta_hours)):
              yield start_date + timedelta(0, 0, 0, 0, 0, n) # Hours

    def get_daily_data(self):
        pass

        # out_path_list = []
        # tick_path_list = []
        # tick_list = []
        #
        # symbol = time_series_request.tickers[0]
        # time_list = []
        #
        # self.logger.info("About to download from Dukascopy... for " + symbol)
        #
        # runs = 0
        #
        # # make parallel
        # for time in self.hour_range(time_series_request.start_date, time_series_request.finish_date):
        #     time_list.append(time)
        #
        #     tick_path = self.tick_name.format(
        #         symbol = symbol,
        #         year = str(time.year).rjust(4, '0'),
        #         month = str(time.month).rjust(2, '0'),
        #         day = str(time.day).rjust(2, '0'),
        #         hour = str(time.hour).rjust(2, '0')
        #     )
        #
        #
        #     tick_path_list.append(tick_path)
        #
        #     out_path = Constants().temp_pythalesians_folder + "/dkticks/" + tick_path
        #     out_path_list.append(out_path)
        #
        # self.logger.info("Completed download from Dukascopy... now parsing")
        #
        # df_list = []
        #
        # runs = 0
        #
        # for i in range(0, len(out_path_list)):
        #     if runs % 24 == 0: self.logger.info("Downloading... " + str(time))
        #
        #     out_path = out_path_list[i]
        #     tick_path = tick_path_list[i]
        #     if not os.path.exists(out_path):
        #         print(tick_path)
        #         if not os.path.exists(os.path.dirname(out_path)):
        #             os.makedirs(os.path.dirname(out_path))
        #
        #     tick_url = "http://www.dukascopy.com/datafeed/" + tick_path
        #
        #     tick = self.fetch_tick(tick_url)
        #
        #     if write_tick_disk:
        #         self.write_tick(tick, out_path)
        #     else:
        #         tick_list.append(tick)
        #
        #     runs = runs + 1
        #
        # runs = 0
        #
        # for i in range(0, len(out_path_list)):
        #     if runs % 24 == 0:
        #         self.logger.info("Parsing... " + str(time))
        #
        #     runs = runs + 1
        #
        #     if write_tick_disk:
        #         tick = open(out_path_list[i], "rb+").read()
        #     else:
        #         tick = tick_list[i]
        #
        #     time = time_list[i]
        #     data = lzma.decompress(tick)
        #     df_list.append(self.retrieve_df(data, symbol, time))

if __name__ == '__main__':
    from pythalesians.market.requests.timeseriesrequest import TimeSeriesRequest
    import datetime

    dc = LoaderDukasCopy()

    time_series_request = TimeSeriesRequest(
                start_date = "01 Jun 2015",                     # start date
                finish_date = "02 Jun 2015",            # finish date
                freq = 'tick',                                  # tick data
                data_source = 'dukascopy',                      # use Bloomberg as data source
                tickers = ['EURUSD'],                           # ticker (Thalesians)
                fields = ['bid', 'ask'],              # which fields to download
                vendor_tickers = ['EURUSD',          # ticker (Bloomberg)
                                  'GBPUSD'],
                vendor_fields = ['bid', 'ask'],   # which Bloomberg fields to download
                cache_algo = 'internet_load_return')                # how to return data

    dc.load_ticker(time_series_request)