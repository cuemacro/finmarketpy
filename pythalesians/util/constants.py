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

    ###### CHANGE THIS TO REFER TO YOUR OWN ROOT FOLDER
    root_pythalesians_folder = "E:/Remote/pythalesians/pythalesians/"
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

    # for plots
    plotfactory_silent_display = False
    plotfactory_default_adapter = "pythalesians"
    plotfactory_source = "Thalesians/BBG (created with PyThalesians Python library)"
    plotfactory_brand_label = "@thalesians"
    plotfactory_display_source_label = True
    plotfactory_display_brand_label = True
    plotfactory_brand_colour = "#5B9BD5"

    plotfactory_default_stylesheet = "pythalesians"

    plotfactory_pythalesians_style_sheet = {"pythalesians" : root_pythalesians_folder + "conf/stylesheets/pythalesians.mplstyle",
                                            "538-pythalesians" : root_pythalesians_folder + "conf/stylesheets/538-pythalesians.mplstyle",
                                            "miletus-pythalesians" : root_pythalesians_folder + "conf/stylesheets/miletus-pythalesians.mplstyle",
                                            "ggplot-pythalesians" : root_pythalesians_folder + "conf/stylesheets/ggplot-pythalesians.mplstyle",
                                            "ggplot-traditional" : root_pythalesians_folder + "conf/stylesheets/ggplot-traditional.mplstyle"}

    plotfactory_scale_factor = 1
    plotfactory_dpi = 100
    plotfactory_width = 543
    plotfactory_height = 381

    ########## BOKEH SETTINGS
    bokeh_font       = 'calibri'
    bokeh_font_style = "normal"
    bokeh_palette = [  '#E24A33',
                       '#348ABD',
                       '#988ED5',
                       '#777777',
                       '#FBC15E',
                       '#8EBA42',
                       '#FFB5B8']

    ########## PLOTLY SETTINGS
    plotly_world_readable = False

    ########## API KEYS

    # Plotly default username
    plotly_default_username = 'thalesians'

    # Plotly settings (username : api_key)
    plotly_creds = {"x" : "x",
                    "x1" : "x1"
                    }

    plotly_streaming_key = "x2"

    # Quandl settings
    quandl_api_key = "x"

    # Twitter settings (you need to set these up on Twitter)
    APP_KEY             = "x"
    APP_SECRET          = "x"
    OAUTH_TOKEN	     = "x"
    OAUTH_TOKEN_SECRET	 = "x"

    ##### Colors for plotting
    # 'red'   :   '#E24A33',
    # 'blue'  :   '#348ABD',
    # 'purple':   '#988ED5',
    # 'gray'  :   '#777777',
    # 'yellow':   '#FBC15E',
    # 'green' :   '#8EBA42',
    # 'pink'  :   '#FFB5B8'

    # nicer than the default colors of matplotlib (fully editable!)
    # list of colors from http://www.github.com/santosjorge/cufflinks project
    # where I've overwritten some of the primary colours (with the above)
    plotfactory_color_overwrites = {
        'aliceblue':         '#F0F8FF',
        'antiquewhite':	     '#FAEBD7',
        'aqua':			     '#00FFFF',
        'aquamarine':		 '#7FFFD4',
        'azure':			 '#F0FFFF',
        'beige':			 '#F5F5DC',
        'bisque':			 '#FFE4C4',
        'black':			 '#000000',
        'blanchedalmond':	 '#FFEBCD',
        'blue':			     '#348ABD', # '#3780bf',
        'bluegray':		     '#565656',
        'bluepurple':		 '#6432AB',
        'blueviolet':		 '#8A2BE2',
        'brick':			 '#E24A33',
        'brightblue':		 '#0000FF',
        'brightred':		 '#FF0000',
        'brown':			 '#A52A2A',
        'burlywood':		 '#DEB887',
        'cadetblue':		 '#5F9EA0',
        'charcoal':		     '#151516',
        'chartreuse':		 '#7FFF00',
        'chocolate':		 '#D2691E',
        'coral':			 '#FF7F50',
        'cornflowerblue':	 '#6495ED',
        'cornsilk':		     '#FFF8DC',
        'crimson':			 '#DC143C',
        'cyan':			     '#00FFFF',
        'darkblue':		     '#00008B',
        'darkcyan':		     '#008B8B',
        'darkgoldenrod':	 '#B8860B',
        'darkgray':		     '#A9A9A9',
        'darkgreen':		 '#006400',
        'darkgrey':		     '#A9A9A9',
        'darkkhaki':		 '#BDB76B',
        'darkmagenta':		 '#8B008B',
        'darkolivegreen':	 '#556B2F',
        'darkorange':		 '#FF8C00',
        'darkorchid':		 '#9932CC',
        'darkred':			 '#8B0000',
        'darksalmon':		 '#E9967A',
        'darkseagreen':	     '#8FBC8F',
        'darkslateblue':	 '#483D8B',
        'darkslategray':	 '#2F4F4F',
        'darkslategrey':	 '#2F4F4F',
        'darkturquoise':	 '#00CED1',
        'darkviolet':		 '#9400D3',
        'deeppink':		     '#FF1493',
        'deepskyblue':		 '#00BFFF',
        'dimgray':			 '#696969',
        'dimgrey':			 '#696969',
        'dodgerblue':		 '#1E90FF',
        'firebrick':		 '#B22222',
        'floralwhite':		 '#FFFAF0',
        'forestgreen':		 '#228B22',
        'fuchsia':			 '#FF00FF',
        'gainsboro':		 '#DCDCDC',
        'ghostwhite':		 '#F8F8FF',
        'gold':			     '#FFD700',
        'goldenrod':		 '#DAA520',
        'grassgreen':		 '#32ab60',
        'gray':			     '#777777', # '#808080',
        'green':			 '#8EBA42', # '#008000',
        'greenyellow':		 '#ADFF2F',
        'grey':			     '#808080',
        'grey01':			 '#0A0A0A',
        'grey02':			 '#151516',
        'grey03':			 '#1A1A1C',
        'grey04':			 '#1E1E21',
        'grey05':			 '#252529',
        'grey06':			 '#36363C',
        'grey07':			 '#3C3C42',
        'grey08':			 '#434343',
        'grey09':			 '#666570',
        'grey10':			 '#666666',
        'grey11':			 '#8C8C8C',
        'grey12':			 '#C2C2C2',
        'grey13':			 '#E2E2E2',
        'honeydew':		     '#F0FFF0',
        'hotpink':			 '#FF69B4',
        'indianred':		 '#CD5C5C',
        'indigo':			 '#4B0082',
        'ivory':			 '#FFFFF0',
        'khaki':			 '#F0E68C',
        'lavender':		     '#E6E6FA',
        'lavenderblush':	 '#FFF0F5',
        'lawngreen':		 '#7CFC00',
        'lemonchiffon':	     '#FFFACD',
        'lightpink2':		 '#fccde5',
        'lightpurple':		 '#bc80bd',
        'lightblue':		 '#ADD8E6',
        'lightcoral':		 '#F08080',
        'lightcyan':		 '#E0FFFF',
        'lightgoldenrodyellow':	 '#FAFAD2',
        'lightgray':		 '#D3D3D3',
        'lightgreen':		 '#90EE90',
        'lightgrey':		 '#D3D3D3',
        'lightpink':		 '#FFB6C1',
        'lightsalmon':		 '#FFA07A',
        'lightseagreen':	 '#20B2AA',
        'lightskyblue':	     '#87CEFA',
        'lightslategray':	 '#778899',
        'lightslategrey':	 '#778899',
        'lightsteelblue':	 '#B0C4DE',
        'lightteal':		 '#8dd3c7',
        'lightyellow':		 '#FFFFE0',
        'lightblue2':		 '#80b1d3',
        'lightviolet':		 '#8476CA',
        'lime':			     '#00FF00',
        'lime2':			 '#8EBA42',
        'limegreen':		 '#32CD32',
        'linen':			 '#FAF0E6',
        'magenta':			 '#FF00FF',
        'maroon':			 '#800000',
        'mediumaquamarine':  '#66CDAA',
        'mediumblue':		 '#0000CD',
        'mediumgray' : 	     '#656565',
        'mediumorchid':	     '#BA55D3',
        'mediumpurple':	     '#9370DB',
        'mediumseagreen':	 '#3CB371',
        'mediumslateblue':	 '#7B68EE',
        'mediumspringgreen': '#00FA9A',
        'mediumturquoise':	 '#48D1CC',
        'mediumvioletred':	 '#C71585',
        'midnightblue':	     '#191970',
        'mintcream':		 '#F5FFFA',
        'mistyrose':		 '#FFE4E1',
        'moccasin':		     '#FFE4B5',
        'mustard':			 '#FBC15E',
        'navajowhite':		 '#FFDEAD',
        'navy':			     '#000080',
        'oldlace':			 '#FDF5E6',
        'olive':			 '#808000',
        'olivedrab':		 '#6B8E23',
        'orange':			 '#FF9900', # '#ff9933',
        'orangered':		 '#FF4500',
        'orchid':			 '#DA70D6',
        'palegoldenrod':	 '#EEE8AA',
        'palegreen':		 '#98FB98',
        'paleolive':		 '#b3de69',
        'paleturquoise':	 '#AFEEEE',
        'palevioletred':	 '#DB7093',
        'papayawhip':		 '#FFEFD5',
        'peachpuff':		 '#FFDAB9',
        'pearl':			 '#D9D9D9',
        'pearl02':			 '#F5F6F9',
        'pearl03':			 '#E1E5ED',
        'pearl04':			 '#9499A3',
        'pearl05':			 '#6F7B8B',
        'pearl06':			 '#4D5663',
        'peru':			     '#CD853F',
        'pink':			     '#FFB5B8', #'#ff0088',
        'pinksalmon':		 '#FFB5B8',
        'plum':			     '#DDA0DD',
        'powderblue':		 '#B0E0E6',
        'purple':			 '#988ED5', #'#800080',
        'red':				 '#E24A33', #'#db4052',
        'rose':			     '#FFC0CB',
        'rosybrown':		 '#BC8F8F',
        'royalblue':		 '#4169E1',
        'saddlebrown':		 '#8B4513',
        'salmon':			 '#fb8072',
        'sandybrown':		 '#FAA460',
        'seaborn':			 '#EAE7E4',
        'seagreen':		     '#2E8B57',
        'seashell':		     '#FFF5EE',
        'sienna':			 '#A0522D',
        'silver':			 '#C0C0C0',
        'skyblue':			 '#87CEEB',
        'slateblue':		 '#6A5ACD',
        'slategray':		 '#708090',
        'slategrey':		 '#708090',
        'smurf':			 '#3E6FB0',
        'snow':			     '#FFFAFA',
        'springgreen':		 '#00FF7F',
        'steelblue':		 '#4682B4',
        'tan':				 '#D2B48C',
        'teal':			     '#008080',
        'thistle':			 '#D8BFD8',
        'tomato':			 '#FF6347',
        'turquoise':		 '#40E0D0',
        'violet':			 '#EE82EE',
        'wheat':			 '#F5DEB3',
        'white':			 '#FFFFFF',
        'whitesmoke':		 '#F5F5F5',
        'yellow':			 '#FBC15E', #'#ffff33',
        'yellowgreen':		 '#9ACD32'
    }

    # plot Bokeh settings
    plotfactory_bokeh_palette =    ['#E24A33',
                                    '#348ABD',
                                    '#988ED5',
                                    '#777777',
                                    '#FBC15E',
                                    '#8EBA42',
                                    '#FFB5B8']