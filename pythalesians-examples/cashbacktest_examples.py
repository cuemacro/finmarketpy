__author__ = 'saeedamen' # Saeed Amen / saeed@thalesians.com

#
# Copyright 2015 Thalesians Ltd. - http//www.thalesians.com / @thalesians
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
cashbacktest_examples

Gives several examples of backtesting simple trading strategies.

"""

###### backtest simple trend following strategy for FX spot basket
if True:
    # for backtest and loading data
    from pythalesians.market.requests.backtestrequest import BacktestRequest
    from pythalesians.backtest.cash.cashbacktest import CashBacktest
    from pythalesians.market.requests.timeseriesrequest import TimeSeriesRequest
    from pythalesians.market.loaders.lighttimeseriesfactory import LightTimeSeriesFactory
    from pythalesians.util.fxconv import FXConv

    # for logging
    from pythalesians.util.loggermanager import LoggerManager

    # for signal generation
    from pythalesians.timeseries.techind.techindicator import TechIndicator
    from pythalesians.timeseries.techind.techparams import TechParams

    # for plotting
    from pythalesians.graphics.graphs.graphproperties import GraphProperties
    from pythalesians.graphics.graphs.plotfactory import PlotFactory

    logger = LoggerManager().getLogger(__name__)

    import datetime

    cash_backtest = CashBacktest()
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

    tech_params = TechParams(); tech_params.sma_period = 200; indicator = 'SMA'

    # pick USD crosses in G10 FX
    # note: we are calculating returns from spot (it is much better to use to total return
    # indices for FX, which include carry)
    logger.info("Loading asset data...")

    tickers = ['EURUSD', 'USDJPY', 'GBPUSD', 'AUDUSD', 'USDCAD',
               'NZDUSD', 'USDCHF', 'USDNOK', 'USDSEK']

    vendor_tickers = ['FRED/DEXUSEU', 'FRED/DEXJPUS', 'FRED/DEXUSUK', 'FRED/DEXUSAL', 'FRED/DEXCAUS',
                      'FRED/DEXUSNZ', 'FRED/DEXSZUS', 'FRED/DEXNOUS', 'FRED/DEXSDUS']

    time_series_request = TimeSeriesRequest(
                start_date = "01 Jan 1989",                     # start date
                finish_date = datetime.date.today(),            # finish date
                freq = 'daily',                                 # daily data
                data_source = 'quandl',                         # use Quandl as data source
                tickers = tickers,                              # ticker (Thalesians)
                fields = ['close'],                                 # which fields to download
                vendor_tickers = vendor_tickers,                    # ticker (Quandl)
                vendor_fields = ['close'],                          # which Bloomberg fields to download
                cache_algo = 'internet_load_return')                # how to return data

    ltsf = LightTimeSeriesFactory()

    asset_df = ltsf.harvest_time_series(time_series_request)
    spot_df = asset_df

    logger.info("Running backtest...")

    # use technical indicator to create signals
    # (we could obviously create whatever function we wanted for generating the signal dataframe)
    tech_ind = TechIndicator()
    tech_ind.create_tech_ind(spot_df, indicator, tech_params); signal_df = tech_ind.get_signal()

    # use the same data for generating signals
    cash_backtest.calculate_trading_PnL(br, asset_df, signal_df)
    port = cash_backtest.get_cumportfolio()
    port.columns = [indicator + ' = ' + str(tech_params.sma_period) + ' ' + str(cash_backtest.get_portfolio_pnl_desc()[0])]
    signals = cash_backtest.get_porfolio_signal()

    # print the last positions (we could also save as CSV etc.)
    print(signals.tail(1))

    pf = PlotFactory()
    gp = GraphProperties()
    gp.title = "Thalesians FX trend strategy"
    gp.source = 'Thalesians/BBG (calc with PyThalesians Python library)'
    gp.scale_factor = 3
    gp.file_output = 'output_data/FX-trend-example.png'

    pf.plot_line_graph(port, adapter = 'pythalesians', gp = gp)