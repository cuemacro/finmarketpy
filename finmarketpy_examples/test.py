from chartpy import Chart, Style
from finmarketpy.economics import Seasonality
from findatapy.market import Market, MarketDataGenerator, MarketDataRequest

from chartpy.style import Style
from findatapy.timeseries import Calculations
from findatapy.util.loggermanager import LoggerManager

seasonality = Seasonality()
calc = Calculations()
logger = LoggerManager().getLogger(__name__)

chart = Chart(engine='matplotlib')

market = Market(market_data_generator=MarketDataGenerator())

md_request = MarketDataRequest(
    start_date="20 Nov 2016",  # start date
    freq='daily',
    data_source='bloomberg',  # use Bloomberg as data source
    tickers=['Gold'],
    fields=['close'],  # which fields to download
    vendor_tickers=['XAUUSD Curncy'],  # ticker (Bloomberg)
    vendor_fields=['PX_LAST'],  # which Bloomberg fields to download
    cache_algo='internet_load_return')  # how to return data

df = market.fetch_market(md_request)

print(df)