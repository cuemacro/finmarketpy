__author__ = 'saeedamen'

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
StrategyFXCTA_Example

Shows how to create a simple FX CTA style strategy, using the StrategyTemplate abstract class (cashbacktest_examples.py
is a lower level way of doing this).

"""

import datetime

from pythalesians.util.loggermanager import LoggerManager

from pythalesians.backtest.popular.strategytemplate import StrategyTemplate

from pythalesians.market.requests.backtestrequest import BacktestRequest
from pythalesians.market.loaders.lighttimeseriesfactory import LightTimeSeriesFactory
from pythalesians.market.requests.timeseriesrequest import TimeSeriesRequest

from pythalesians.timeseries.techind.techindicator import TechIndicator

class StrategyFXCTA_Example(StrategyTemplate):

    def __init__(self):
        super(StrategyTemplate, self).__init__()
        self.logger = LoggerManager().getLogger(__name__)

        ##### FILL IN WITH YOUR OWN PARAMETERS FOR display, dumping, TSF etc.
        self.tsfactory = LightTimeSeriesFactory()
        self.DUMP_CSV = 'output_data/'
        self.DUMP_PATH = 'output_data/' + datetime.date.today().strftime("%Y%m%d") + ' '
        self.FINAL_STRATEGY = 'Thalesians FX CTA'
        self.SCALE_FACTOR = 3
        self.DEFAULT_PLOT_ENGINE = 'pythalesians'

        return

    ###### Parameters and signal generations (need to be customised for every model)
    def fill_backtest_request(self):

        ##### FILL IN WITH YOUR OWN BACKTESTING PARAMETERS
        br = BacktestRequest()

        # get all asset data
        br.start_date = "04 Jan 1989"
        br.finish_date = datetime.datetime.utcnow()
        br.spot_tc_bp = 0.5
        br.ann_factor = 252

        br.plot_start = "01 Apr 2015"
        br.calc_stats = True
        br.write_csv = False
        br.plot_interim = True
        br.include_benchmark = True

        # have vol target for each signal
        br.signal_vol_adjust = True
        br.signal_vol_target = 0.1
        br.signal_vol_max_leverage = 5
        br.signal_vol_periods = 20
        br.signal_vol_obs_in_year = 252
        br.signal_vol_rebalance_freq = 'BM'
        br.signal_vol_resample_freq = None

        # have vol target for portfolio
        br.portfolio_vol_adjust = True
        br.portfolio_vol_target = 0.1
        br.portfolio_vol_max_leverage = 5
        br.portfolio_vol_periods = 20
        br.portfolio_vol_obs_in_year = 252
        br.portfolio_vol_rebalance_freq = 'BM'
        br.portfolio_vol_resample_freq = None

        # tech params
        br.tech_params.sma_period = 200

        return br

    def fill_assets(self):
        ##### FILL IN WITH YOUR ASSET DATA

        # for FX basket
        full_bkt    = ['EURUSD', 'USDJPY', 'GBPUSD', 'AUDUSD', 'USDCAD',
                       'NZDUSD', 'USDCHF', 'USDNOK', 'USDSEK']

        basket_dict = {}

        for i in range(0, len(full_bkt)):
            basket_dict[full_bkt[i]] = [full_bkt[i]]

        basket_dict['Thalesians FX CTA'] = full_bkt

        br = self.fill_backtest_request()

        self.logger.info("Loading asset data...")

        vendor_tickers = ['FRED/DEXUSEU', 'FRED/DEXJPUS', 'FRED/DEXUSUK', 'FRED/DEXUSAL', 'FRED/DEXCAUS',
                          'FRED/DEXUSNZ', 'FRED/DEXSZUS', 'FRED/DEXNOUS', 'FRED/DEXSDUS']

        time_series_request = TimeSeriesRequest(
                    start_date = br.start_date,                     # start date
                    finish_date = br.finish_date,                   # finish date
                    freq = 'daily',                                 # daily data
                    data_source = 'quandl',                         # use Quandl as data source
                    tickers = full_bkt,                             # ticker (Thalesians)
                    fields = ['close'],                                 # which fields to download
                    vendor_tickers = vendor_tickers,                    # ticker (Quandl)
                    vendor_fields = ['close'],                          # which Bloomberg fields to download
                    cache_algo = 'internet_load_return')                # how to return data

        asset_df = self.tsfactory.harvest_time_series(time_series_request)

        # if web connection fails read from CSV
        if asset_df is None:
            import pandas

            asset_df = pandas.read_csv("d:/fxcta.csv", index_col=0, parse_dates=['Date'],
                                       date_parser = lambda x: pandas.datetime.strptime(x, '%Y-%m-%d'))

        # signalling variables
        spot_df = asset_df
        spot_df2 = None

        # asset_df

        return asset_df, spot_df, spot_df2, basket_dict

    def construct_signal(self, spot_df, spot_df2, tech_params, br):

        ##### FILL IN WITH YOUR OWN SIGNALS

        # use technical indicator to create signals
        # (we could obviously create whatever function we wanted for generating the signal dataframe)
        tech_ind = TechIndicator()
        tech_ind.create_tech_ind(spot_df, 'SMA', tech_params); signal_df = tech_ind.get_signal()

        return signal_df

    def construct_strategy_benchmark(self):

        ###### FILL IN WITH YOUR OWN BENCHMARK

        tsr_indices = TimeSeriesRequest(
            start_date = '01 Jan 1980',                     # start date
            finish_date = datetime.datetime.utcnow(),       # finish date
            freq = 'daily',                                 # intraday data
            data_source = 'quandl',                         # use Bloomberg as data source
            tickers = ["EURUSD"],                           # tickers to download
            vendor_tickers=['FRED/DEXUSEU'],
            fields = ['close'],                             # which fields to download
            vendor_fields = ['close'],
            cache_algo = 'cache_algo_return')               # how to return data)

        df = self.tsfactory.harvest_time_series(tsr_indices)

        df.columns = [x.split(".")[0] for x in df.columns]

        return df

if __name__ == '__main__':

# just change "False" to "True" to run any of the below examples

    # create a FX CTA strategy then chart the returns, leverage over time
    if True:
        strategy = StrategyFXCTA_Example()

        strategy.construct_strategy()

        strategy.plot_strategy_pnl()                        # plot the final strategy
        strategy.plot_strategy_leverage()                   # plot the leverage of the portfolio
        strategy.plot_strategy_group_pnl_trades()           # plot the individual trade P&Ls
        strategy.plot_strategy_group_benchmark_pnl()        # plot all the cumulative P&Ls of each component
        strategy.plot_strategy_group_leverage()             # plot all the individual leverages
        strategy.plot_strategy_group_benchmark_annualised_pnl()

    # create a FX CTA strategy, then examine how P&L changes with different vol targeting
    # and later transaction costs
    if True:
        strategy = StrategyFXCTA_Example()

        from pythalesians.backtest.stratanalysis.tradeanalysis import TradeAnalysis

        ta = TradeAnalysis()

        # which backtesting parameters to change
        # names of the portfolio
        # broad type of parameter name
        parameter_list = [
            {'portfolio_vol_adjust': True, 'signal_vol_adjust' : True},
            {'portfolio_vol_adjust': False, 'signal_vol_adjust' : False}]

        pretty_portfolio_names = \
            ['Vol target',
             'No vol target']

        parameter_type = 'vol target'

        ta.run_arbitrary_sensitivity(strategy,
                                     parameter_list=parameter_list,
                                     pretty_portfolio_names=pretty_portfolio_names,
                                     parameter_type=parameter_type)

        # now examine sensitivity to different transaction costs
        tc = [0, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2.0]
        ta.run_tc_shock(strategy, tc = tc)

        # how does P&L change on day of month
        ta.run_day_of_month_analysis(strategy)

    # create a FX CTA strategy then use TradeAnalysis (via pyfolio) to analyse returns
    if True:
        from pythalesians.backtest.stratanalysis.tradeanalysis import TradeAnalysis
        strategy = StrategyFXCTA_Example()
        strategy.construct_strategy()

        tradeanalysis = TradeAnalysis()
        tradeanalysis.run_strategy_returns_stats(strategy)
