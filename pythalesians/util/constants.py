__author__ = 'saeedamen' # Saeed Amen / saeed@thalesians.com

#
# Copyright 2015 Thalesians Ltd. - http//www.thalesians.com / @pythalesians
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
Constants

Has various constants required for the project.

"""

import os

class Constants:

    ###### CHANGE THIS TO REFER TO YOUR OWN ROOT FOLDER (if autodetect has problems)
    root_pythalesians_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/') + "/"
    temp_pythalesians_folder = root_pythalesians_folder + "temp"

    ###### FOR FUTURE VERSIONS (which include caching and aliasing of tickers) - DO NOT REMOVE!
    # folders for holding market data
    folder_time_series_data = "E:/timeseriesdata"
    folder_historic_CSV = "E:/tickdata/historicCSV"

    # config file for time series categories
    time_series_categories_fields = \
        root_pythalesians_folder + "conf/time_series_categories_fields.csv"

    # we can have multiple tickers files (separated by ";")
    time_series_tickers_list = root_pythalesians_folder + "conf/time_series_tickers_list.csv;" + \
                               root_pythalesians_folder + "conf/g10_vol_tickers.csv"

    time_series_fields_list = root_pythalesians_folder + "conf/time_series_fields_list.csv"

    # config file for long term econ data
    all_econ_tickers = root_pythalesians_folder + "conf/all_econ_tickers.csv"
    econ_country_codes = root_pythalesians_folder + "conf/econ_country_codes.csv"
    econ_country_groups = root_pythalesians_folder + "conf/econ_country_groups.csv"

    # for events filtering
    events_category = 'events'
    events_category_dt = 'events_dt'

    ###### FOR CURRENT VERSION

    # which timeseriesfactory type to use?
    # note: lighttimeseriesfactory currently implemented
    #       cachedtimeseriesfactory will be added in due course
    default_time_series_factory = "lighttimeseriesfactory"

    # in Python threading does not offer true parallisation, but can be useful when downloading data, because
    # a lot of the time is spend waiting on data, multiprocessing library addresses this problem by spawning new Python
    # instances, but this has greater overhead (maybe more advisable when downloading very long time series)

    # "thread" or "multiprocessing" (experimental!) library to use when downloading data
    time_series_factory_thread_technique = "thread"

    # how many threads to use for loading external data (don't do too many on slow machines!)
    # also some data sources will complain if you start too many parallel threads to call data!
    # for some data providers might get better performance from 1 thread only!
    time_series_factory_thread_no = {'quandl'      : 4,
                                     'bloomberg'   : 8,
                                     'yahoo'       : 8,
                                     'other'       : 4}

    # log config file
    logging_conf = root_pythalesians_folder + "conf/logging.conf"

    # Bloomberg settings
    bbg_default_api = 'open-api'   # allowed values 'open-api' (newer & recommended) and 'com-api' (older style API)
    bbg_server = "localhost"       # needs changing if you use Bloomberg Server API
    bbg_server_port = 8194

    # Dukascopy settings
    dukascopy_base_url = "http://www.dukascopy.com/datafeed/"
    dukascopy_write_temp_tick_disk = False

    # Quandl settings
    quandl_api_key = "x"

    # Twitter settings (you need to set these up on Twitter)
    APP_KEY             = "x"
    APP_SECRET          = "x"
    OAUTH_TOKEN	     = "x"
    OAUTH_TOKEN_SECRET	 = "x"