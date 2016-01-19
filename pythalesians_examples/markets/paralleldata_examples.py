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
paralleldata_examples

Shows how we can change settings to increase the parallel downloading of data from sources like Bloomberg.

"""
# for logging
from pythalesians.util.loggermanager import LoggerManager

# to download market data
from pythalesians.market.requests.timeseriesrequest import TimeSeriesRequest
from pythalesians.market.loaders.lighttimeseriesfactory import LightTimeSeriesFactory

if __name__ == '__main__':
    # On Windows calling this function is necessary (to prevent repeated respawning of multiprocess functions)
    # On Linux/OSX it does nothing

    # only necessary if you use multiprocessing_on_dill code
    try:
        # the standard multiprocessing library fails in pickling the market data classes
        import multiprocessing_on_dill as multiprocessing
        multiprocessing.freeze_support()
    except: pass

    if True:
        logger = LoggerManager().getLogger(__name__)

        import datetime

        # just change "False" to "True" to run any of the below examples

        ###### download daily data from Bloomberg for FX, with different threading techniques
        if False:

            time_series_request = TimeSeriesRequest(
                    start_date = "01 Jan 1999",                     # start date
                    finish_date = datetime.date.today(),            # finish date
                    freq = 'daily',                                 # daily data
                    data_source = 'bloomberg',                      # use Bloomberg as data source
                    tickers = ['EURUSD',                            # ticker (Thalesians)
                               'GBPUSD',
                               'USDJPY',
                               'AUDUSD'],
                    fields = ['close', 'high', 'low'],              # which fields to download
                    vendor_tickers = ['EURUSD BGN Curncy',          # ticker (Bloomberg)
                                      'GBPUSD BGN Curncy',
                                      'USDJPY BGN Curncy',
                                      'AUDUSD BGN Curncy'],
                    vendor_fields = ['PX_LAST', 'PX_HIGH', 'PX_LOW'],   # which Bloomberg fields to download
                    cache_algo = 'internet_load_return')                # how to return data

            ltsf = LightTimeSeriesFactory()

            from pythalesians.util.constants import Constants

            # use different thread numbers, thread and multiprocessor Python libraries
            # note that speed of download depends on many factors, such as length of time series
            # so not always quickest to use threading!
            thread_no = [1,2,3,4]

            thread_technique = ["thread", "multiprocessor"]
            diag = []

            for tech in thread_technique:
                # change the static variable in Constants which govern the threading we use
                Constants.time_series_factory_thread_technique = tech

                for no in thread_no:
                    for key in Constants.time_series_factory_thread_no:
                        Constants.time_series_factory_thread_no[key] = no

                    import time
                    start = time.time();
                    df = ltsf.harvest_time_series(time_series_request);
                    end = time.time()
                    duration = end - start

                    diag.append("With " + str(no) + " " + tech + " no: " + str(duration) + " seconds")

            for d in diag:
                logger.info(d)

        ###### download intraday data from Bloomberg for FX, with different threading techniques
        if True:

            from datetime import timedelta

            time_series_request = TimeSeriesRequest(
                    start_date = datetime.date.today() - timedelta(days=10),    # start date
                    finish_date = datetime.date.today(),                        # finish date
                    freq = 'intraday',                                          # intraday data
                    data_source = 'bloomberg',                      # use Bloomberg as data source
                    tickers = ['EURUSD',                            # ticker (Thalesians)
                               'GBPUSD',
                               'USDJPY',
                               'AUDUSD'],
                    fields = ['close', 'high', 'low'],              # which fields to download
                    vendor_tickers = ['EURUSD BGN Curncy',          # ticker (Bloomberg)
                                      'GBPUSD BGN Curncy',
                                      'USDJPY BGN Curncy',
                                      'AUDUSD BGN Curncy'],
                    vendor_fields = ['PX_LAST', 'PX_HIGH', 'PX_LOW'],   # which Bloomberg fields to download
                    cache_algo = 'internet_load_return')                # how to return data

            ltsf = LightTimeSeriesFactory()

            from pythalesians.util.constants import Constants

            # use different thread numbers, thread and multiprocessor Python libraries
            # note that speed of download depends on many factors, such as length of time series
            # so not always quickest to use threading!
            thread_no = [1,2,3,4]

            thread_technique = ["thread", "multiprocessor"]
            diag = []

            for tech in thread_technique:
                # change the static variable in Constants which govern the threading we use
                Constants.time_series_factory_thread_technique = tech

                for no in thread_no:
                    for key in Constants.time_series_factory_thread_no: Constants.time_series_factory_thread_no[key] = no

                    import time
                    start = time.time(); df = ltsf.harvest_time_series(time_series_request); end = time.time()
                    duration = end - start

                    diag.append("With " + str(no) + " " + tech + " no: " + str(duration) + " seconds")

            for d in diag:
                logger.info(d)

        ##### load FX data using Quandl
        if True:
            tickers    = ['EURUSD', 'USDJPY', 'GBPUSD', 'AUDUSD', 'USDCAD',
                           'NZDUSD', 'USDCHF', 'USDNOK', 'USDSEK']
            vendor_tickers = ['FRED/DEXUSEU', 'FRED/DEXJPUS', 'FRED/DEXUSUK', 'FRED/DEXUSAL', 'FRED/DEXCAUS',
                              'FRED/DEXUSNZ', 'FRED/DEXSZUS', 'FRED/DEXNOUS', 'FRED/DEXSDUS']

            time_series_request = TimeSeriesRequest(
                        start_date = "01 Jan 1999",                     # start date
                        finish_date = datetime.date.today(),                   # finish date
                        freq = 'daily',                                 # daily data
                        data_source = 'quandl',                         # use Quandl as data source
                        tickers = tickers,                             # ticker (Thalesians)
                        fields = ['close'],                                 # which fields to download
                        vendor_tickers = vendor_tickers,                    # ticker (Quandl)
                        vendor_fields = ['close'],                          # which Bloomberg fields to download
                        cache_algo = 'internet_load_return')                # how to return data


            ltsf = LightTimeSeriesFactory()

            from pythalesians.util.constants import Constants

            # use different thread numbers, thread and multiprocessor Python libraries
            # note that speed of download depends on many factors, such as length of time series
            # so not always quickest to use threading!
            thread_no = [1,2,3,4]

            thread_technique = ["thread", "multiprocessor"]
            diag = []

            for tech in thread_technique:
                # change the static variable in Constants which govern the threading we use
                Constants.time_series_factory_thread_technique = tech

                for no in thread_no:
                    for key in Constants.time_series_factory_thread_no: Constants.time_series_factory_thread_no[key] = no

                    import time
                    start = time.time(); df = ltsf.harvest_time_series(time_series_request); end = time.time()
                    duration = end - start

                    diag.append("With " + str(no) + " " + tech + " no: " + str(duration) + " seconds")

            for d in diag:
                logger.info(d)