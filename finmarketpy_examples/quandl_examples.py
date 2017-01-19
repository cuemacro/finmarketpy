__author__ = 'saeedamen'

# loading data
import datetime

from chartpy import Chart, Style
from findatapy.market import Market, MarketDataGenerator, MarketDataRequest

from findatapy.util.loggermanager import LoggerManager

logger = LoggerManager().getLogger(__name__)

chart = Chart(engine='matplotlib')

market = Market(market_data_generator=MarketDataGenerator())

# choose run_example = 0 for everything
# run_example = 1 - download BoE data from quandl

run_example = 0

###### fetch data from Quandl for BoE rate (using Bloomberg data)
if run_example == 1 or run_example == 0:
    # Monthly average of UK resident monetary financial institutions' (excl. Central Bank) sterling
    # Weighted average interest rate, other loans, new advances, on a fixed rate to private non-financial corporations (in percent)
    # not seasonally adjusted
    md_request = MarketDataRequest(
        start_date="01 Jan 2000",  # start date
        data_source='quandl',  # use Quandl as data source
        tickers=['Weighted interest rate'],
        fields=['close'],  # which fields to download
        vendor_tickers=['BOE/CFMBJ84'],  # ticker (Bloomberg)
        vendor_fields=['close'],  # which Bloomberg fields to download
        cache_algo='internet_load_return')  # how to return data

    df = market.fetch_market(md_request)

    style = Style()

    style.title = 'BoE weighted interest rate'
    style.scale_factor = 3
    style.file_output = "boe-rate.png"
    style.source = 'Quandl/BoE'

    chart.plot(df, style=style)
