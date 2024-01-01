__author__ = "saeedamen"

#
# Copyright 2020 Cuemacro
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
Shows how to calculate seasonality
"""

# Loading data
import datetime

import pandas

from chartpy import Chart, Style
from finmarketpy.economics import Seasonality
from findatapy.market import Market, MarketDataGenerator, MarketDataRequest

from chartpy.style import Style
from findatapy.timeseries import Calculations
from findatapy.util.loggermanager import LoggerManager

seasonality = Seasonality()
calc = Calculations()
logger = LoggerManager().getLogger(__name__)

chart = Chart(engine="matplotlib")

market = Market(market_data_generator=MarketDataGenerator())

# choose run_example = 0 for everything
# run_example = 1 - seasonality of gold
# run_example = 2 - seasonality of FX vol
# run_example = 3 - seasonality of gasoline
# run_example = 4 - seasonality in NFP
# run_example = 5 - seasonal adjustment in NFP

run_example = 0

###### Calculate seasonal moves in Gold (using Bloomberg data)
if run_example == 1 or run_example == 0:
    md_request = MarketDataRequest(
                start_date = "01 Jan 1996",                         # start date
                data_source = "bloomberg",                          # use Bloomberg as data source
                tickers = ["Gold"],
                fields = ["close"],                                 # which fields to download
                vendor_tickers = ["XAUUSD Curncy"],                 # ticker (Bloomberg)
                vendor_fields = ["PX_LAST"],                        # which Bloomberg fields to download
                cache_algo = "internet_load_return")                # how to return data

    df = market.fetch_market(md_request)

    df_ret = calc.calculate_returns(df)

    day_of_month_seasonality = seasonality.bus_day_of_month_seasonality(df_ret, partition_by_month = False)
    day_of_month_seasonality = calc.convert_month_day_to_date_time(day_of_month_seasonality)

    style = Style()
    style.date_formatter = "%b"
    style.title = "Gold seasonality"
    style.scale_factor = 3
    style.file_output = "gold-seasonality.png"

    chart.plot(day_of_month_seasonality, style=style)

###### Calculate seasonal moves in FX vol (using Bloomberg data)
if run_example == 2 or run_example == 0:
    tickers = ["EURUSDV1M", "USDJPYV1M", "GBPUSDV1M", "AUDUSDV1M"]

    md_request = MarketDataRequest(
                start_date = "01 Jan 1996",                         # start date
                data_source = "bloomberg",                          # use Bloomberg as data source
                tickers = tickers,
                fields = ["close"],                                 # which fields to download
                vendor_tickers = [x + " Curncy" for x in tickers],  # ticker (Bloomberg)
                vendor_fields = ["PX_LAST"],                        # which Bloomberg fields to download
                cache_algo = "internet_load_return")                # how to return data

    df = market.fetch_market(md_request)

    df_ret = calc.calculate_returns(df)

    day_of_month_seasonality = seasonality.bus_day_of_month_seasonality(df_ret, partition_by_month = False)
    day_of_month_seasonality = calc.convert_month_day_to_date_time(day_of_month_seasonality)

    style = Style()
    style.date_formatter = "%b"
    style.title = "FX vol seasonality"
    style.scale_factor = 3
    style.file_output = "fx-vol-seasonality.png"
    style.source = "finmarketpy/Bloomberg"

    chart.plot(day_of_month_seasonality, style=style)

###### Calculate seasonal moves in Gasoline (using Bloomberg data)
if run_example == 3 or run_example == 0:
    md_request = MarketDataRequest(
                start_date = "01 Jan 1996",                         # start date
                data_source = "bloomberg",                          # use Bloomberg as data source
                tickers = ["Gasoline"],
                fields = ["close"],                                 # which fields to download
                vendor_tickers = ["XB1 Comdty"],                    # ticker (Bloomberg)
                vendor_fields = ["PX_LAST"],                        # which Bloomberg fields to download
                cache_algo = "internet_load_return")                # how to return data

    df = market.fetch_market(md_request)

    df_ret = calc.calculate_returns(df)

    day_of_month_seasonality = seasonality.bus_day_of_month_seasonality(df_ret, partition_by_month = False)
    day_of_month_seasonality = calc.convert_month_day_to_date_time(day_of_month_seasonality)

    style = Style()
    style.date_formatter = "%b"
    style.title = "Gasoline seasonality"
    style.scale_factor = 3
    style.file_output = "gasoline-seasonality.png"

    chart.plot(day_of_month_seasonality, style=style)

###### Calculate seasonal moves in US non-farm payrolls (using Bloomberg data)
if run_example == 4 or run_example == 0:
    # get the NFP NSA from ALFRED/FRED
    md_request = MarketDataRequest(
        start_date="01 Jun 2000",       # start date (download data over past decade)
        data_source="alfred",           # use ALFRED/FRED as data source
        tickers=["US NFP"],             # ticker
        fields=["actual-release"],      # which fields to download
        vendor_tickers=["PAYNSA"],         # ticker (FRED)  PAYEMS (NSA)
        vendor_fields=["actual-release"])  # which FRED fields to download

    df = market.fetch_market(md_request)

    df_ret = calc.calculate_returns(df)

    month_seasonality = seasonality.monthly_seasonality_from_prices(df)

    style = Style()
    style.date_formatter = "%b"
    style.title = "NFP seasonality"
    style.scale_factor = 3
    style.file_output = "nfp-seasonality.png"

    chart.plot(month_seasonality, style=style)

###### Apply seasonal adjustment to NFP data and compare the seasonal adjustment by finmarketpy with that of BLS
if run_example == 5 or run_example == 0:
    # get the NFP NSA from ALFRED/FRED
    md_request = MarketDataRequest(
        start_date="01 Jun 1980",       # start date (download data over past decade)
        data_source="alfred",           # use ALFRED/FRED as data source
        tickers=["US NFP (NSA)", "US NFP (SA)"],             # ticker
        fields=["actual-release"],      # which fields to download
        vendor_tickers=["PAYNSA", "PAYEMS"],         # ticker (FRED) PAYEMS (SA) PAYNSA (NSA)
        vendor_fields=["actual-release"])  # which FRED fields to download

    df = market.fetch_market(md_request)

    # Calculate changes in NFP
    df = df - df.shift(1)

    df_seasonal_adjusted = seasonality.adjust_rolling_seasonality(pandas.DataFrame(df["US NFP (NSA).actual-release"]),
                                                                  window=12*20, likely_period=12)

    df_seasonal_adjusted.columns = [x + " SA finmarketpy" for x in df_seasonal_adjusted.columns]

    # Compare not seasonally adjusted vs seasonally adjusted
    df = df.join(df_seasonal_adjusted)
    df = df[df.index > "01 Jan 2000"]

    style = Style()

    style.title = "NFP (seasonally adjusted)"
    style.scale_factor = 3
    style.file_output = "nfp-seasonally-adjusted.png"

    chart.plot(df, style=style)