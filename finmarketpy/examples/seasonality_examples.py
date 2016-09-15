__author__ = 'saeedamen'


# loading data
import datetime

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

# choose run_example = 0 for everything
# run_example = 1 - seasonality of gold
# run_example = 2 - seasonality of FX vol

run_example = 0

###### calculate seasonal moves in Gold (using Bloomberg data)
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

    df_ret = calc.calculate_returns(df)

    day_of_month_seasonality = seasonality.bus_day_of_month_seasonality(df_ret, partition_by_month = False)
    day_of_month_seasonality = calc.convert_month_day_to_date_time(day_of_month_seasonality)

    style = Style()
    style.date_formatter = '%b'
    style.title = 'Gold seasonality'
    style.scale_factor = 3
    style.file_output = "gold-seasonality.png"

    chart.plot(day_of_month_seasonality, style=style)

###### calculate seasonal moves in FX vol (using Bloomberg data)
if run_example == 2 or run_example == 0:
    tickers = ['EURUSDV1M', 'USDJPYV1M', 'GBPUSDV1M', 'AUDUSDV1M']

    md_request = MarketDataRequest(
                start_date = "01 Jan 1996",                         # start date
                data_source = 'bloomberg',                          # use Bloomberg as data source
                tickers = tickers,
                fields = ['close'],                                 # which fields to download
                vendor_tickers = [x + ' Curncy' for x in tickers],  # ticker (Bloomberg)
                vendor_fields = ['PX_LAST'],                        # which Bloomberg fields to download
                cache_algo = 'internet_load_return')                # how to return data

    df = market.fetch_market(md_request)

    df_ret = calc.calculate_returns(df)

    day_of_month_seasonality = seasonality.bus_day_of_month_seasonality(df_ret, partition_by_month = False)
    day_of_month_seasonality = calc.convert_month_day_to_date_time(day_of_month_seasonality)

    style = Style()
    style.date_formatter = '%b'
    style.title = 'FX vol seasonality'
    style.scale_factor = 3
    style.file_output = "fx-vol-seasonality.png"
    style.source = 'finmarketpy/Bloomberg'

    chart.plot(day_of_month_seasonality, style=style)