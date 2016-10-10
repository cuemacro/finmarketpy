__author__ = 'saeedamen'


# loading data
import datetime

from chartpy import Chart, Style
from finmarketpy.backtest import TradeAnalysis
from findatapy.market import Market, MarketDataGenerator, MarketDataRequest

from chartpy.style import Style
from findatapy.timeseries import Calculations
from findatapy.util.loggermanager import LoggerManager

ta = TradeAnalysis()
calc = Calculations()
logger = LoggerManager().getLogger(__name__)

chart = Chart(engine='matplotlib')

market = Market(market_data_generator=MarketDataGenerator())

# choose run_example = 0 for everything
# run_example = 1 - use PyFolio to analyse gold's return properties

run_example = 0

###### use PyFolio to analyse gold's return properties
if run_example == 1 or run_example == 0:
    md_request = MarketDataRequest(
                start_date = "01 Jan 1996",                         # start date
                data_source = 'bloomberg',                          # use Bloomberg as data source
                tickers = ['Gold'],
                fields = ['close'],                                 # which fields to download
                vendor_tickers = ['XAUUSD Curncy'],                 # ticker (Bloomberg)
                vendor_fields = ['PX_LAST'],                        # which Bloomberg fields to download
                cache_algo = 'internet_load_return')                # how to return data

    df = market.fetch_market(md_request)

    ta.run_strategy_returns_stats(None, index=df, engine='pyfolio')