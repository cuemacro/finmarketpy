__author__ = 'saeedamen' # Saeed Amen

#
# Copyright 2016 Cuemacro
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
backtest

Gives several examples of backtesting simple trading strategies, using Backtest (a lower level class)

"""

# choose run_example = 0 for everything
# run_example = 1 - do a backtest of a FX basket with trend following
# run_example = 2 - do a backtest of EURUSD traded with trend following
run_example = 0

###### backtest simple trend following strategy for FX spot basket
if run_example == 1 or run_example == 0:
    # for backtest and loading data
    from finmarketpy.backtest import BacktestRequest, Backtest
    from findatapy.market import Market, MarketDataRequest, MarketDataGenerator
    from findatapy.util.fxconv import FXConv

    # for logging
    from findatapy.util.loggermanager import LoggerManager

    # for signal generation
    from finmarketpy.economics import TechIndicator, TechParams

    # for plotting
    from chartpy import Chart, Style

    logger = LoggerManager().getLogger(__name__)

    import datetime

    backtest = Backtest()
    br = BacktestRequest()
    fxconv = FXConv()

    # get all asset data
    br.start_date = "02 Jan 1990"
    br.finish_date = datetime.datetime.utcnow()
    br.spot_tc_bp = 2.5                             # 2.5 bps bid/ask spread
    br.ann_factor = 252

    # have vol target for each signal
    br.signal_vol_adjust = True
    br.signal_vol_target = 0.05
    br.signal_vol_max_leverage = 3
    br.signal_vol_periods = 60
    br.signal_vol_obs_in_year = 252
    br.signal_vol_rebalance_freq = 'BM'
    br.signal_vol_resample_freq = None

    tech_params = TechParams(); tech_params.sma_period = 200; indicator = 'SMA'

    # pick USD crosses in G10 FX
    # note: we are calculating returns from spot (it is much better to use to total return
    # indices for FX, which include carry)
    logger.info("Loading asset data...")

    tickers = ['EURUSD', 'USDJPY', 'GBPUSD', 'AUDUSD', 'USDCAD',
               'NZDUSD', 'USDCHF', 'USDNOK', 'USDSEK']

    vendor_tickers = ['FRED/DEXUSEU', 'FRED/DEXJPUS', 'FRED/DEXUSUK', 'FRED/DEXUSAL', 'FRED/DEXCAUS',
                      'FRED/DEXUSNZ', 'FRED/DEXSZUS', 'FRED/DEXNOUS', 'FRED/DEXSDUS']

    md_request = MarketDataRequest(
                start_date = "01 Jan 1989",                     # start date
                finish_date = datetime.date.today(),            # finish date
                freq = 'daily',                                 # daily data
                data_source = 'quandl',                         # use Quandl as data source
                tickers = tickers,                              # ticker (findatapy)
                fields = ['close'],                                 # which fields to download
                vendor_tickers = vendor_tickers,                    # ticker (Quandl)
                vendor_fields = ['close'],                          # which Bloomberg fields to download
                cache_algo = 'internet_load_return')                # how to return data

    market = Market(market_data_generator=MarketDataGenerator())

    asset_df = market.fetch_market(md_request)
    spot_df = asset_df

    logger.info("Running backtest...")

    # use technical indicator to create signals
    # (we could obviously create whatever function we wanted for generating the signal dataframe)
    tech_ind = TechIndicator()
    tech_ind.create_tech_ind(spot_df, indicator, tech_params); signal_df = tech_ind.get_signal()

    # use the same data for generating signals
    backtest.calculate_trading_PnL(br, asset_df, signal_df)
    port = backtest.get_cumportfolio()
    port.columns = [indicator + ' = ' + str(tech_params.sma_period) + ' ' + str(backtest.get_portfolio_pnl_desc()[0])]
    signals = backtest.get_portfolio_signal()

    # print the last positions (we could also save as CSV etc.)
    print(signals.tail(1))

    style = Style()
    style.title = "FX trend strategy"
    style.source = 'Quandl'
    style.scale_factor = 1
    style.file_output = 'fx-trend-example.png'

    Chart().plot(port, style = style)

###### backtest simple trend following strategy for FX spot basket
if run_example == 2 or run_example == 0:
    # for backtest and loading data
    from finmarketpy.backtest import Backtest, BacktestRequest
    from findatapy.market import Market, MarketDataRequest, MarketDataGenerator
    from findatapy.util.fxconv import FXConv
    from findatapy.timeseries import Calculations

    # for logging
    from findatapy.util import LoggerManager

    # for signal generation
    from finmarketpy.economics import TechIndicator, TechParams

    # for plotting
    from chartpy import Chart, Style

    logger = LoggerManager().getLogger(__name__)

    import datetime

    backtest = Backtest()
    br = BacktestRequest()
    fxconv = FXConv()

    # get all asset data
    br.start_date = "02 Jan 1990"
    br.finish_date = datetime.datetime.utcnow()
    br.spot_tc_bp = 2.5                             # 2.5 bps bid/ask spread
    br.ann_factor = 252

    tech_params = TechParams(); tech_params.sma_period = 200; indicator = 'SMA'
    tech_params.only_allow_longs = True
    # tech_params.only_allow_shorts = True

    # pick EUR/USD
    # note: we are calculating returns from spot (it is much better to use to total return
    # indices for FX, which include carry)
    logger.info("Loading asset data...")

    md_request = MarketDataRequest(
                start_date = "01 Jan 1989",                     # start date
                finish_date = datetime.date.today(),            # finish date
                freq = 'daily',                                 # daily data
                data_source = 'quandl',                         # use Quandl as data source
                tickers = ['EURUSD'],                               # ticker (findatapy)
                fields = ['close'],                                 # which fields to download
                vendor_tickers = ['FRED/DEXUSEU'],                  # ticker (Quandl)
                vendor_fields = ['close'],                          # which Bloomberg fields to download
                cache_algo = 'internet_load_return')                # how to return data

    market = Market(market_data_generator=MarketDataGenerator())

    asset_df = market.fetch_market(md_request)
    spot_df = asset_df

    logger.info("Running backtest...")

    # use technical indicator to create signals
    # (we could obviously create whatever function we wanted for generating the signal dataframe)
    tech_ind = TechIndicator()
    tech_ind.create_tech_ind(spot_df, indicator, tech_params); signal_df = tech_ind.get_signal()

    # use the same data for generating signals
    backtest.calculate_trading_PnL(br, asset_df, signal_df)
    port = backtest.get_cumportfolio()
    port.columns = [indicator + ' = ' + str(tech_params.sma_period) + ' ' + str(backtest.get_portfolio_pnl_desc()[0])]
    signals = backtest.get_porfolio_signal()   # get final signals for each series
    returns = backtest.get_pnl()               # get P&L for each series

    calculations = Calculations()
    trade_returns = calculations.calculate_individual_trade_gains(signals, returns)

    print(trade_returns)

    # print the last positions (we could also save as CSV etc.)
    print(signals.tail(1))

    style = Style()
    style.title = "EUR/USD trend model"
    style.source = 'Quandl'
    style.scale_factor = 1
    style.file_output = 'eurusd-trend-example.png'

    Chart(port, style = style).plot()