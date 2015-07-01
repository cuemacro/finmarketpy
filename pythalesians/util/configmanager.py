__author__ = 'saeedamen'

import csv
from pythalesians.util.constants import Constants
from pythalesians.util.singleton import Singleton
from pythalesians.util.loggermanager import LoggerManager
from dateutil.parser import parse

class ConfigManager(object):
    __metaclass__ = Singleton

    _is_init = 0

    _dict_time_series_tickers_list_library_to_vendor = {}
    _dict_time_series_tickers_list_vendor_to_library = {}
    _dict_time_series_fields_list_vendor_to_library = {}
    _dict_time_series_fields_list_library_to_vendor = {}

    # store categories -> fields
    _dict_time_series_category_fields_library_to_library = {}
    _dict_time_series_category_startdate_library_to_library = {}
    _dict_time_series_category_tickers_library_to_library = {}

    # store categories ->
    _dict_time_series_tickers_list_library = {}

    def __init__(self, *args, **kwargs):
        if ConfigManager._is_init == 0:
            ConfigManager.populate_time_series_dictionaries()
            ConfigManager._is_init = 1
        #logger = LoggerManager().getLogger(__name__)
        pass

    ### time series ticker manipulators
    @staticmethod
    def populate_time_series_dictionaries():

        # there are several CSV files which contain data on the tickers

        # time_series_tickers_list - contains every ticker (Thalesians tickers => vendor tickers)
        # category,	source,	freq, ticker, cut, fields, sourceticker (from your data provider)
        # eg. fx / bloomberg / daily / EURUSD / TOK / close,open,high,low / EURUSD CMPT Curncy

        # time_series_fields_list - translate Thalesians field name to vendor field names
        # Thalesians fields => vendor fields
        # source, field, sourcefield

        # time_series_categories_fields - for each category specific generic properties
        # category,	freq, source, fields, startdate
        # eg. fx / daily / bloomberg / close,high,low,open / 01-Jan-70

        # eg. bloomberg / close / PX_LAST

        ## populate tickers list (allow for multiple files)
        time_series_tickers_list_file = Constants().time_series_tickers_list.split(';')

        for tickers_list_file in time_series_tickers_list_file:
            reader = csv.DictReader(open(tickers_list_file))

            for line in reader:
                category = line["category"]
                source = line["source"]
                freq = line["freq"]
                ticker = line["ticker"]
                cut = line["cut"]
                sourceticker = line["sourceticker"]

                # conversion from library ticker to vendor sourceticker
                ConfigManager._dict_time_series_tickers_list_library_to_vendor[category + '.' +
                                                                     source + '.' +
                                                                     freq + '.' +
                                                                     cut + '.' +
                                                                     ticker] = sourceticker

                # conversion from vendor sourceticker to library ticker
                ConfigManager._dict_time_series_tickers_list_vendor_to_library[source + '.' + sourceticker] = ticker

                # library of tickers by category
                key = category + '.' + source + '.' + freq + '.' + cut

                if key in ConfigManager._dict_time_series_category_tickers_library_to_library:
                    ConfigManager._dict_time_series_category_tickers_library_to_library[key].append(ticker)
                else:
                    ConfigManager._dict_time_series_category_tickers_library_to_library[key] = [ticker]

        ## populate fields conversions
        reader = csv.DictReader(open(Constants().time_series_fields_list))

        for line in reader:
            source = line["source"]
            field = line["field"]
            sourcefield = line["sourcefield"]

            # conversion from vendor sourcefield to library field
            ConfigManager._dict_time_series_fields_list_vendor_to_library[source + '.' + sourcefield] = field

            # conversion from library ticker to vendor sourcefield
            ConfigManager._dict_time_series_fields_list_library_to_vendor[source + '.' + field] = sourcefield

        ## populate categories field list
        reader = csv.DictReader(open(Constants().time_series_categories_fields))

        for line in reader:
            category = line["category"]
            source = line["source"]
            freq = line["freq"]
            cut = line["cut"]
            fields = line["fields"].split(',') # can have multiple fields
            startdate = line["startdate"]

            # conversion from library category to library fields list
            ConfigManager._dict_time_series_category_fields_library_to_library[
                category + '.' + source + '.' + freq + '.' + cut] = fields

            # conversion from library category to library startdate
            ConfigManager._dict_time_series_category_startdate_library_to_library[
                category + '.' + source + '.' + freq + '.' + cut] = parse(startdate).date()

        x = 5

    @staticmethod
    def get_categories_from_fields():
        return ConfigManager._dict_time_series_category_fields_library_to_library.keys()

    @staticmethod
    def get_categories_from_tickers():
        return ConfigManager._dict_time_series_category_tickers_library_to_library.keys()

    @staticmethod
    def get_categories_from_tickers_selective_filter(filter):
        initial_list = ConfigManager._dict_time_series_category_tickers_library_to_library.keys()
        filtered_list = []

        for category_desc in initial_list:
            split_cat = category_desc.split('.')

            category = split_cat[0]
            source = split_cat[1]
            freq = split_cat[2]
            cut = split_cat[3]

            if filter in category:
                filtered_list.append(category_desc)

        return filtered_list

    @staticmethod
    def get_potential_caches_from_tickers():
        all_categories = ConfigManager._dict_time_series_category_tickers_library_to_library.keys()

        expanded_category_list = []

        for sing in all_categories:
            split_sing = sing.split(".")
            category = split_sing[0]
            source = split_sing[1]
            freq = split_sing[2]
            cut = split_sing[3]

            if(freq == 'intraday'):
                intraday_tickers = ConfigManager().get_tickers_list_for_category(category, source, freq, cut)

                for intraday in intraday_tickers:
                    expanded_category_list.append(category + '.' + source + '.' + freq +
                                                  '.' + cut + '.' + intraday)
            else:
                expanded_category_list.append(category + '.' + source + '.' + freq +
                                                  '.' + cut)

        return expanded_category_list

    @staticmethod
    def get_fields_list_for_category(category, source, freq, cut):
        return ConfigManager._dict_time_series_category_fields_library_to_library[
                category + '.' + source + '.' + freq + '.' + cut]

    @staticmethod
    def get_startdate_for_category(category, source, freq, cut):
        return ConfigManager._dict_time_series_category_startdate_library_to_library[
                category + '.' + source + '.' + freq + '.' + cut]

    @staticmethod
    def get_tickers_list_for_category(category, source, freq, cut):
        return ConfigManager._dict_time_series_category_tickers_library_to_library[
                category + '.' + source + '.' + freq + '.' + cut]

    @staticmethod
    def convert_library_to_vendor_ticker(category, source, freq, cut, ticker):
        return ConfigManager._dict_time_series_tickers_list_library_to_vendor[
            category + '.' + source + '.'+ freq + '.' + cut + '.' + ticker]

    @staticmethod
    def convert_vendor_to_library_ticker(source, sourceticker):
        return ConfigManager._dict_time_series_tickers_list_vendor_to_library[
            source + '.' + sourceticker]

    @staticmethod
    def convert_vendor_to_library_field(source, sourcefield):
        return ConfigManager._dict_time_series_fields_list_vendor_to_library[
            source + '.' + sourcefield]

    @staticmethod
    def convert_library_to_vendor_field(source, field):
        return ConfigManager._dict_time_series_fields_list_library_to_vendor[
            source + '.' + field]


## test function
if __name__ == '__main__':
    logger = LoggerManager().getLogger(__name__)

    categories = ConfigManager().get_categories_from_fields()

    logger.info("Categories from fields list")
    print(categories)

    categories = ConfigManager().get_categories_from_tickers()

    logger.info("Categories from tickers list")
    print(categories)

    filter = 'events'

    categories_filtered = ConfigManager().get_categories_from_tickers_selective_filter(filter)
    logger.info("Categories from tickers list, filtered by events")
    print(categories_filtered)

    logger.info("For each category, print all tickers and fields")

    for sing in categories:
        split_sing = sing.split(".")
        category = split_sing[0]
        source = split_sing[1]
        freq = split_sing[2]
        cut = split_sing[3]

        logger.info("tickers for " + sing)
        tickers = ConfigManager().get_tickers_list_for_category(category, source, freq, cut)

        print(tickers)

        logger.info("fields for " + sing)
        fields = ConfigManager().get_fields_list_for_category(category, source, freq, cut)

        print(fields)

    # test the various converter mechanisms
    output = ConfigManager().convert_library_to_vendor_ticker(
        category='fx',source='bloomberg', freq='daily', cut='TOK', ticker='USDJPY')

    print(output)

    output = ConfigManager().convert_vendor_to_library_ticker(
        source='bloomberg', sourceticker='EURUSD CMPT Curncy')

    print(output)

    output = ConfigManager().convert_vendor_to_library_field(
        source='bloomberg', sourcefield='PX_LAST')

    print(output)

    output = ConfigManager().convert_library_to_vendor_field(
        source='bloomberg', field='close')

    print(output)

    x = 5



