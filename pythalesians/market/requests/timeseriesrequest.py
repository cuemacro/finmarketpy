__author__ = 'saeedamen'

from pythalesians.util.loggermanager import LoggerManager
from datetime import datetime

class TimeSeriesRequest:

    # properties
    #
    # data_source eg. bbg, yahoo, quandl
    # start_date
    # finish_date
    # tickers (can be list) eg. EURUSD
    # category (eg. fx, equities, fixed_income, cal_event, fundamental)
    # freq_mult (eg. 1)
    # freq
    # gran_freq (minute, daily, hourly, daily, weekly, monthly, yearly)
    # fields (can be list)
    # vendor_tickers (optional)
    # vendor_fields (optional)
    # cache_algo (eg. internet, disk, memory) - internet will forcibly download from the internet
    # environment (eg. prod, backtest) - old data is saved with prod, backtest will overwrite the last data point
    def __init__(self, data_source = None,
                 start_date = None, finish_date = None, tickers = None, category = None, freq_mult = None, freq = None,
                 gran_freq = None, cut = None,
                 fields = None, cache_algo = None,
                 vendor_tickers = None, vendor_fields = None,
                 environment = "backtest", trade_side = 'trade'
                 ):

        self.logger = LoggerManager().getLogger(__name__)

        self.freq_mult = 1

        if data_source is not None: self.data_source = data_source
        if start_date is not None: self.start_date = start_date
        if finish_date is not None: self.finish_date = finish_date
        if tickers is not None: self.tickers = tickers
        if category is not None: self.category = category
        if gran_freq is not None: self.gran_freq = gran_freq
        if freq_mult is not None: self.freq_mult = freq_mult
        if freq is not None: self.freq = freq
        if cut is not None: self.cut = cut
        if fields is not None: self.fields = fields
        if cache_algo is not None: self.cache_algo = cache_algo
        if vendor_tickers is not None: self.vendor_tickers = vendor_tickers
        if vendor_fields is not None: self.vendor_fields = vendor_fields
        if environment is not None: self.environment = environment
        if trade_side is not None: self.trade_side = trade_side

    @property
    def data_source(self):
        return self.__data_source

    @data_source.setter
    def data_source(self, data_source):
        valid_data_source = ['ats', 'bloomberg', 'dukascopy', 'fred', 'gain', 'google', 'quandl', 'yahoo']

        if not data_source in valid_data_source:
            self.logger.warning(data_source & " is not a defined data source.")

        self.__data_source = data_source

    @property
    def category(self):
        return self.__category

    @category.setter
    def category(self, category):
        self.__category = category

    @property
    def tickers(self):
        return self.__tickers

    @tickers.setter
    def tickers(self, tickers):
        if not isinstance(tickers, list):
            tickers = [tickers]

        self.__tickers = tickers

    @property
    def fields(self):
        return self.__fields

    @fields.setter
    def fields(self, fields):
        valid_fields = ['open', 'high', 'low', 'close', 'volume', 'numEvents']

        if not isinstance(fields, list):
            fields = [fields]

        for field_entry in fields:
            if not field_entry in valid_fields:
                i = 0
                # self.logger.warning(field_entry + " is not a valid field.")

        # add error checking

        self.__fields = fields

    @property
    def vendor_tickers(self):
        return self.__vendor_tickers

    @vendor_tickers.setter
    def vendor_tickers(self, vendor_tickers):
        if not isinstance(vendor_tickers, list):
            vednor_tickers = [vendor_tickers]

        self.__vendor_tickers = vendor_tickers

    @property
    def vendor_fields(self):
        return self.__vendor_fields

    @vendor_fields.setter
    def vendor_fields(self, vendor_fields):
        if not isinstance(vendor_fields, list):
            vendor_fields = [vendor_fields]

        self.__vendor_fields = vendor_fields

    @property
    def freq(self):
        return self.__freq

    @freq.setter
    def freq(self, freq):
        freq = freq.lower()

        valid_freq = ['tick', 'second', 'minute', 'intraday', 'hourly', 'daily']

        if not freq in valid_freq:
            self.logger.warning(freq & " is not a defined frequency")

        self.__freq = freq

    @property
    def gran_freq(self):
        return self.__gran_freq

    @gran_freq.setter
    def gran_freq(self, gran_freq):
        gran_freq = gran_freq.lower()

        valid_gran_freq = ['tick', 'second', 'minute', 'hourly', 'pseudodaily', 'daily', 'weekly', 'monthly', 'quarterly', 'yearly']

        if not gran_freq in valid_gran_freq:
            self.logger.warning(gran_freq & " is not a defined frequency")

        if gran_freq in ['minute', 'hourly']:
            self.__freq = 'intraday'
        elif gran_freq in ['tick', 'second']:
            self.__freq = 'tick'
        else:
            self.__freq = 'daily'

        self.__gran_freq = gran_freq

    @property
    def freq_mult(self):
        return self.__freq_mult

    @freq_mult.setter
    def freq_mult(self, freq_mult):
        self.__freq_mult = freq_mult

    @property
    def start_date(self):
        return self.__start_date

    @start_date.setter
    def start_date(self, start_date):
        self.__start_date = self.date_parser(start_date)

    @property
    def finish_date(self):
        return self.__finish_date

    @finish_date.setter
    def finish_date(self, finish_date):
        self.__finish_date = self.date_parser(finish_date)

    @property
    def cut(self):
        return self.__cut

    @cut.setter
    def cut(self, cut):
        self.__cut = cut

    def date_parser(self, date):
        if isinstance(date, str):
            # format expected 'Jun 1 2005 01:33', '%b %d %Y %H:%M'
            try:
                date = datetime.strptime(date, '%b %d %Y %H:%M')
            except:
                # self.logger.warning("Attempted to parse date")
                i = 0

            # format expected '1 Jun 2005 01:33', '%d %b %Y %H:%M'
            try:
                date = datetime.strptime(date, '%d %b %Y %H:%M')
            except:
                # self.logger.warning("Attempted to parse date")
                i = 0

            try:
                date = datetime.strptime(date, '%b %d %Y')
            except:
                # self.logger.warning("Attempted to parse date")
                i = 0

            try:
                date = datetime.strptime(date, '%d %b %Y')
            except:
                # self.logger.warning("Attempted to parse date")
                i = 0

        return date

    @property
    def cache_algo(self):
        return self.__cache_algo

    @cache_algo.setter
    def cache_algo(self, cache_algo):
        cache_algo = cache_algo.lower()

        valid_cache_algo = ['internet_load', 'internet_load_return', 'cache_algo', 'cache_algo_return']


        if not cache_algo in valid_cache_algo:
            self.logger.warning(cache_algo + " is not a defined caching scheme")

        self.__cache_algo = cache_algo

    @property
    def environment(self):
        return self.__environment

    @environment.setter
    def environment(self, environment):
        environment = environment.lower()

        valid_environment= ['prod', 'backtest']

        if not environment in valid_environment:
            self.logger.warning(environment + " is not a defined environment.")

        self.__environment = environment

    @property
    def trade_side(self):
        return self.__trade_side

    @trade_side.setter
    def trade_side(self, trade_side):
        trade_side = trade_side.lower()

        valid_trade_side = ['trade', 'bid', 'ask']

        if not trade_side in valid_trade_side:
            self.logger.warning(trade_side + " is not a defined trade side.")

        self.__trade_side = trade_side