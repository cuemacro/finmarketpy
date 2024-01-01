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
Shows how to calculate returns of an asset
"""

# Loading data
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

chart = Chart(engine="matplotlib")

market = Market(market_data_generator=MarketDataGenerator())

# Choose run_example = 0 for everything
# run_example = 1 - use PyFolio to analyse gold"s return properties

run_example = 0

###### Use PyFolio to analyse gold"s return properties
if run_example == 1 or run_example == 0:
    md_request = MarketDataRequest(
                start_date="01 Jan 1996",                         # start date
                data_source="bloomberg",                          # use Bloomberg as data source
                tickers=["Gold"],
                field =["close"],                                 # which fields to download
                vendor_tickers=["XAUUSD Curncy"],                 # ticker (Bloomberg)
                vendor_fields=["PX_LAST"],                        # which Bloomberg fields to download
                cache_algo="internet_load_return")                # how to return data

    df = market.fetch_market(md_request)

    ta.run_strategy_returns_stats(None, index=df, engine="pyfolio")