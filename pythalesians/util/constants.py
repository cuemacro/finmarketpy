__author__ = 'saeedamen' # Saeed Amen / saeed@pythalesians.com

#
# Copyright 2015 Thalesians Ltd. - http//www.pythalesians.com / @pythalesians
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

Has various constants required for the project. Before running the project, you will need to modify
root_pythalesians_folder, for logging and also chart stylesheets amongst other things.

"""

import os

class Constants:
    def __init__(self):

        ###### CHANGE THIS TO REFER TO YOUR OWN ROOT FOLDER
        self.root_pythalesians_folder = "D:/Remote/pythalesians/pythalesians/"
        self.temp_pythalesians_folder = self.root_pythalesians_folder + "temp"

        self.folder_time_series_data = self.root_pythalesians_folder + "timeseriesdata"

        ###### FOR FUTURE VERSIONS (which include caching)
        # folders for holding market data
        # self.folder_historic_CSV = "D:/tickdata/historicCSV"
        #
        # # config file for time series categories
        # self.time_series_categories_fields = \
        #     self.root_pythalesians_folder + "conf/time_series_categories_fields.csv"
        #
        # # we can have multiple tickers files (separated by ";")
        # self.time_series_tickers_list = self.root_pythalesians_folder + "conf/time_series_tickers_list.csv;" + \
        #                                 self.root_pythalesians_folder + "conf/g10_vol_tickers.csv"
        #
        # self.time_series_fields_list = self.root_pythalesians_folder + "conf/time_series_fields_list.csv"

        # for events filtering
        self.events_category = 'events'
        self.events_category_dt = 'events_dt'

        ###### FOR CURRENT VERSION

        # which timeseriesfactory type to use?
        # note: lighttimeseriesfactory currently implemented
        #       cachedtimeseriesfactory will be added in due course
        self.default_time_series_factory = "lighttimeseriesfactory"

        # log config file
        self.logging_conf = self.root_pythalesians_folder + "conf/logging.conf"

        # Bloomberg settings
        self.bbg_default_api = 'open-api'   # allowed values 'open-api' (newer & recommended) and 'com-api' (older style API)
        self.bbg_server = "localhost"       # needs changing if you use Bloomberg Server API
        self.bbg_server_port = 8194

        # Dukascopy settings
        self.dukascopy_base_url = "http://www.dukascopy.com/datafeed/"
        self.dukascopy_write_temp_tick_disk = False

        # for plots
        self.plotfactory_default_adapter = "pythalesians"
        self.plotfactory_source = "Thalesians/BBG (created with PyThalesians Python library)"
        self.plotfactory_brand_label = "@thalesians"
        self.plotfactory_display_source = True
        self.plotfactory_display_brand_label = True
        self.plotfactory_brand_colour = "#5B9BD5"

        self.plotfactory_default_stylesheet = "pythalesians"

        self.plotfactory_pythalesians_style_sheet = {"pythalesians" : self.root_pythalesians_folder + "conf/stylesheets/pythalesians.mplstyle",
                                                     "538-pythalesians" : self.root_pythalesians_folder + "conf/stylesheets/538-pythalesians.mplstyle",
                                                     "miletus-pythalesians" : self.root_pythalesians_folder +"conf/stylesheets/miletus-pythalesians.mplstyle",
                                                     "ggplot-pythalesians" : self.root_pythalesians_folder +"conf/stylesheets/ggplot-pythalesians.mplstyle"}

        self.plotfactory_scale_factor = 1
        self.plotfactory_dpi = 100
        self.plotfactory_width = 543
        self.plotfactory_height = 381

        # nicer than the default colors of matplotlib (fully editable!)
        self.plotfactory_color_overwrites = {'red' : '#E24A33',
                                             'blue': '#348ABD',
                                             'purple':   '#988ED5',
                                             'gray'  :   '#777777',
                                             'yellow':   '#FBC15E',
                                             'green' :   '#8EBA42',
                                             'pink'  :   '#FFB5B8'}

        # plot Bokeh settings
        self.plotfactory_bokeh_palette =    ['#E24A33',
                                             '#348ABD',
                                             '#988ED5',
                                             '#777777',
                                             '#FBC15E',
                                             '#8EBA42',
                                             '#FFB5B8']

        self.plotfactory_bokeh_font = 'calibri'

        ########## API KEYS

        # Plotly settings
        self.plotly_username = "pythalesians"
        self.plotly_api_key = "XXXX"

        # Quandl settings
        self.quandl_api_key = "XXXX"

        # Twitter settings (you need to set these up on Twitter)
        self.APP_KEY             = "XXXX"
        self.APP_SECRET          = "XXXX"
        self.OAUTH_TOKEN	     = "XXXX"
        self.OAUTH_TOKEN_SECRET	 = "XXXX"