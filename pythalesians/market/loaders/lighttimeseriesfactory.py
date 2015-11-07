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
LightTimeSeriesFactory

Returns market data time series by directly calling data sources like Bloomberg, Yahoo and Quandl (planning to add more).
Provides a common wrapper for all these data sources.

"""

import copy

from pythalesians.util.configmanager import ConfigManager
from pythalesians.util.loggermanager import LoggerManager
from pythalesians.util.constants import Constants
from pythalesians.market.requests.timeseriesrequest import TimeSeriesRequest
from pythalesians.timeseries.calcs.timeseriesfilter import TimeSeriesFilter
from pythalesians.market.loaders.timeseriesio import TimeSeriesIO

class LightTimeSeriesFactory:
    _time_series_cache = {} # shared across all instances of object!

    def __init__(self):
        # self.config = ConfigManager()
        self.logger = LoggerManager().getLogger(__name__)
        self.time_series_filter = TimeSeriesFilter()
        self.time_series_io = TimeSeriesIO()
        self._bbg_default_api = Constants().bbg_default_api
        self._intraday_code = -1

        return

    def set_bloomberg_com_api(self):
        """
        set_bloomberg_com_api - Sets Bloomberg API to COM library
        """

        self._bbg_default_api = 'com-api'

    def set_bloomberg_open_api(self):
        """
        set_bloomberg_open_api - Sets Bloomberg API to OpenAPI (recommended)
        """

        self._bbg_default_api = 'open-api'

    def flush_cache(self):
        """
        flush_cache - Flushs internal cache of time series
        """

        self._time_series_cache = {}

    def set_intraday_code(self, code):
        self._intraday_code = code

    def get_loader(self, source):
        """
        get_loader - Loads appropriate data service class

        Parameters
        ----------
        source : str
            the data service to use "bloomberg", "quandl", "yahoo", "google", "fred" etc.

        Returns
        -------
        LoaderTemplate
        """

        loader = None

        if source == 'bloomberg':

            ### allow use of COM API (older) and Open APIs (newer) for Bloomberg
            if self._bbg_default_api == 'com-api':
                from pythalesians.market.loaders.lowlevel.bbg.loaderbbg import LoaderBBGCOM
                loader = LoaderBBGCOM()
            elif self._bbg_default_api == 'open-api':
                from pythalesians.market.loaders.lowlevel.bbg.loaderbbgopen import LoaderBBGOpen
                loader = LoaderBBGOpen()

        elif source == 'quandl':
            from pythalesians.market.loaders.lowlevel.quandl.loaderquandl import LoaderQuandl
            loader = LoaderQuandl()

        elif source == 'dukascopy':
            from pythalesians.market.loaders.lowlevel.brokers.loaderdukascopy import LoaderDukasCopy
            loader = LoaderDukasCopy()

        elif source in ['yahoo', 'google', 'fred']:
            from pythalesians.market.loaders.lowlevel.pandasweb.loaderpandasweb import LoaderPandasWeb
            loader = LoaderPandasWeb()

        # TODO add support for other data sources (like Reuters)

        return loader

    def harvest_time_series(self, time_series_request, kill_session = True):
        """
        havest_time_series - Loads time series from specified data provider

        Parameters
        ----------
        time_series_request : TimeSeriesRequest
            contains various properties describing time series to fetched, including ticker, start & finish date etc.

        Returns
        -------
        pandas.DataFrame
        """

        tickers = time_series_request.tickers
        loader = self.get_loader(time_series_request.data_source)

        # check if tickers have been specified (if not load all of them for a category)
        # also handle single tickers/list tickers
        create_tickers = False

        if tickers is None :
            create_tickers = True
        elif isinstance(tickers, str):
            if tickers == '': create_tickers = True
        elif isinstance(tickers, list):
            if tickers == []: create_tickers = True

        if create_tickers:
            time_series_request.tickers = self.config.get_tickers_list_for_category(
            time_series_request.category, time_series_request.source, time_series_request.freq, time_series_request.cut)

        # intraday or tick: only one ticker per cache file
        if (time_series_request.freq in ['intraday', 'tick', 'second', 'hour', 'minute']):
            data_frame_agg = self.download_intraday_tick(time_series_request, loader)

        # daily: multiple tickers per cache file - assume we make one API call to vendor library
        else: data_frame_agg = self.download_daily(time_series_request, loader)

        if('internet_load' in time_series_request.cache_algo):
            self.logger.debug("Internet loading.. ")

            # signal to loader template to exit session
            # if loader is not None and kill_session == True: loader.kill_session()

        if(time_series_request.cache_algo == 'cache_algo'):
            self.logger.debug("Only caching data in memory, do not return any time series."); return

        tsf = TimeSeriesFilter()

        # only return time series if specified in the algo
        if 'return' in time_series_request.cache_algo:
            # special case for events/events-dt which is not indexed like other tables
            if hasattr(time_series_request, 'category'):
                if 'events' in time_series_request.category:
                    return data_frame_agg

            try:
                return tsf.filter_time_series(time_series_request, data_frame_agg)
            except:
                import traceback

                self.logger.error(traceback.format_exc())

                return None

    def get_time_series_cached(self, time_series_request):
        """
        get_time_series_cached - Loads time series from cache (if it exists)

        Parameters
        ----------
        time_series_request : TimeSeriesRequest
            contains various properties describing time series to fetched, including ticker, start & finish date etc.

        Returns
        -------
        pandas.DataFrame
        """

        if (time_series_request.freq == "intraday"):
            ticker = time_series_request.tickers
        else:
            ticker = None

        fname = self.create_time_series_hash_key(time_series_request, ticker)

        if (fname in self._time_series_cache):
            data_frame = self._time_series_cache[fname]

            tsf = TimeSeriesFilter()

            return tsf.filter_time_series(time_series_request, data_frame)

        return None

    def create_time_series_hash_key(self, time_series_request, ticker = None):
        """
        create_time_series_hash_key - Creates a hash key for retrieving the time series

        Parameters
        ----------
        time_series_request : TimeSeriesRequest
            contains various properties describing time series to fetched, including ticker, start & finish date etc.

        Returns
        -------
        str
        """

        if(isinstance(ticker, list)):
            ticker = ticker[0]

        return self.create_cache_file_name(self.create_category_key(time_series_request, ticker))

    def download_intraday_tick(self, time_series_request, loader):
        """
        download_intraday_tick - Loads intraday time series from specified data provider

        Parameters
        ----------
        time_series_request : TimeSeriesRequest
            contains various properties describing time series to fetched, including ticker, start & finish date etc.

        Returns
        -------
        pandas.DataFrame
        """

        data_frame_agg = None

        ticker_cycle = 0

        # single threaded version
        # handle intraday ticker calls separately one by one
        if len(time_series_request.tickers) == 1 or Constants().time_series_factory_thread_no['other'] == 1:
            for ticker in time_series_request.tickers:
                time_series_request_single = copy.copy(time_series_request)
                time_series_request_single.tickers = ticker

                if hasattr(time_series_request, 'vendor_tickers'):
                    time_series_request_single.vendor_tickers = [time_series_request.vendor_tickers[ticker_cycle]]
                    ticker_cycle = ticker_cycle + 1

                # we downscale into float32, to avoid memory problems in Python (32 bit)
                # data is stored on disk as float32 anyway
                data_frame_single = loader.load_ticker(time_series_request_single)

                # if the vendor doesn't provide any data, don't attempt to append
                if data_frame_single is not None:
                    if data_frame_single.empty == False:
                        data_frame_single.index.name = 'Date'
                        data_frame_single = data_frame_single.astype('float32')

                        # if you call for returning multiple tickers, be careful with memory considerations!
                        if data_frame_agg is not None:
                            data_frame_agg = data_frame_agg.join(data_frame_single, how='outer')
                        else:
                            data_frame_agg = data_frame_single

                # key = self.create_category_key(time_series_request, ticker)
                # fname = self.create_cache_file_name(key)
                # self._time_series_cache[fname] = data_frame_agg  # cache in memory (disable for intraday)

            return data_frame_agg
        else:
            time_series_request_list = []

            # create a list of TimeSeriesRequests
            for ticker in time_series_request.tickers:
                time_series_request_single = copy.copy(time_series_request)
                time_series_request_single.tickers = ticker

                if hasattr(time_series_request, 'vendor_tickers'):
                    time_series_request_single.vendor_tickers = [time_series_request.vendor_tickers[ticker_cycle]]
                    ticker_cycle = ticker_cycle + 1

                time_series_request_list.append(time_series_request_single)

            return self.fetch_group_time_series(time_series_request_list)

    def fetch_single_time_series(self, time_series_request):
        data_frame_single = self.get_loader(time_series_request.data_source).load_ticker(time_series_request)

        if data_frame_single is not None:
            if data_frame_single.empty == False:
                data_frame_single.index.name = 'Date'

                # will fail for dataframes which includes dates
                try:
                    data_frame_single = data_frame_single.astype('float32')
                except: pass

                if time_series_request.freq == "second":
                    data_frame_single = data_frame_single.resample("1s")

        return data_frame_single

    def fetch_group_time_series(self, time_series_request_list):

        data_frame_agg = None

        # depends on the nature of operation as to whether we should use threading or multiprocessing library
        if Constants().time_series_factory_thread_technique is "thread":
            from multiprocessing.dummy import Pool
        else:
            # most of the time is spend waiting for Bloomberg to return, so can use threads rather than multiprocessing
            # must use the multiprocessing_on_dill library otherwise can't pickle objects correctly
            # note: currently not very stable
            from multiprocessing_on_dill import Pool

        thread_no = Constants().time_series_factory_thread_no['other']

        if time_series_request_list[0].data_source in Constants().time_series_factory_thread_no:
            thread_no = Constants().time_series_factory_thread_no[time_series_request_list[0].data_source]

        pool = Pool(thread_no)

        # open the market data downloads in their own threads and return the results
        result = pool.map_async(self.fetch_single_time_series, time_series_request_list)
        data_frame_group = result.get()

        pool.close()
        pool.join()

        # data_frame_group = results.get()
        # data_frame_group = results
        # data_frame_group = None

        #import multiprocessing as multiprocessing
        # close the pool and wait for the work to finish

        # processes = []

        # for x in range(0, len(time_series_request_list)):
        #    time_series_request = time_series_request_list[x]
        # processes =   [multiprocessing.Process(target = self.fetch_single_time_series,
        #                                           args = (x)) for x in time_series_request_list]

        # pool.apply_async(tsf.harvest_category, args = (category_desc, environment, freq,
        #             exclude_freq_cat, force_new_download_freq_cat, include_freq_cat))

        # Run processes
        # for p in processes: p.start()

        # Exit the completed processes
        # for p in processes: p.join()

        # collect together all the time series
        if data_frame_group is not None:
            for data_frame_single in data_frame_group:
                # if you call for returning multiple tickers, be careful with memory considerations!
                if data_frame_single is not None:
                    if data_frame_agg is not None:
                        data_frame_agg = data_frame_agg.join(data_frame_single, how='outer')
                    else:
                        data_frame_agg = data_frame_single

        return data_frame_agg

    def download_daily(self, time_series_request, loader):
        """
        download_daily - Loads daily time series from specified data provider

        Parameters
        ----------
        time_series_request : TimeSeriesRequest
            contains various properties describing time series to fetched, including ticker, start & finish date etc.

        Returns
        -------
        pandas.DataFrame
        """

        # daily data does not include ticker in the key, as multiple tickers in the same file

        if Constants().time_series_factory_thread_no['other'] == 1:
            data_frame_agg = loader.load_ticker(time_series_request)
        else:
            time_series_request_list = []

            group_size = int(len(time_series_request.tickers) / Constants().time_series_factory_thread_no['other'] - 1)

            if group_size == 0: group_size = 1

            # split up tickers into groups related to number of threads to call
            for i in range(0, len(time_series_request.tickers), group_size):
                time_series_request_single = copy.copy(time_series_request)
                time_series_request_single.tickers = time_series_request.tickers[i:i + group_size]

                if hasattr(time_series_request, 'vendor_tickers'):
                    time_series_request_single.vendor_tickers = \
                        time_series_request.vendor_tickers[i:i + group_size]

                time_series_request_list.append(time_series_request_single)

            data_frame_agg = self.fetch_group_time_series(time_series_request_list)

        key = self.create_category_key(time_series_request)
        fname = self.create_cache_file_name(key)
        self._time_series_cache[fname] = data_frame_agg  # cache in memory (ok for daily data)

        return data_frame_agg

    def create_category_key(self, time_series_request, ticker=None):
        """
        create_category_key - Returns a category key for the associated TimeSeriesRequest

        Parameters
        ----------
        time_series_request : TimeSeriesRequest
            contains various properties describing time series to fetched, including ticker, start & finish date etc.

        Returns
        -------
        str
        """

        category = 'default-cat'
        cut = 'default-cut'

        if hasattr(time_series_request, 'category'): category = time_series_request.category

        environment = time_series_request.environment
        source = time_series_request.data_source
        freq = time_series_request.freq

        if hasattr(time_series_request, 'cut'): cut = time_series_request.cut

        if (ticker is not None): key = environment + "." + category + '.' + source + '.' + freq + '.' + cut + '.' + ticker
        else: key = environment + "." + category + '.' + source + '.' + freq + '.' + cut

        return key

    def create_cache_file_name(self, filename):
        return Constants().folder_time_series_data + "/" + filename

if __name__ == '__main__':
    # see examples/lighttimeseriesfactory_examples for practical examples on how to use this class
    pass