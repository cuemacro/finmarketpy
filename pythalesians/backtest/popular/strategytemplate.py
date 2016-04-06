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
StrategyTemplate

Abstract class which wraps around BacktestFactory, providing conveninent functions for analaysis. Implement your own
subclasses of this for your own strategy. See strategyfxcta_example.py for a simple implementation of a FX trend following
strategy.

"""

import abc

import pandas
import numpy

from pythalesians.util.loggermanager import LoggerManager

from pythalesians.backtest.cash.cashbacktest import CashBacktest

from pythalesians.timeseries.calcs.timeseriesfilter import TimeSeriesFilter
from pythalesians.timeseries.calcs.timeseriescalcs import TimeSeriesCalcs
from pythalesians.timeseries.calcs.timeseriesdesc import TimeSeriesDesc

from pythalesians.timeseries.techind.techparams import TechParams

from pythalesians.graphics.graphs.plotfactory import PlotFactory
from pythalesians.graphics.graphs.graphproperties import GraphProperties

from collections import OrderedDict

from pythalesians.util.constants import Constants

class StrategyTemplate:

    # to be implemented by every trading strategy
    @abc.abstractmethod
    def fill_backtest_request(self):
        """
        fill_backtest_request - Fills parameters for the backtest, such as start-end dates, transaction costs etc. To
        be implemented by subclass.
        """
        return

    @abc.abstractmethod
    def fill_assets(self):
        """
        fill_assets - Loads time series for the assets to be traded and also for data for generating signals.
        """
        return

    @abc.abstractmethod
    def construct_signal(self, spot_df, spot_df2, tech_params):
        """
        construct_signal - Constructs signal from pre-loaded time series

        Parameters
        ----------
        spot_df : pandas.DataFrame
            Market time series for generating signals

        spot_df2 : pandas.DataFrame
            Market time series for generated signals (can be of different frequency)

        tech_params : TechParams
            Parameters for generating signals
        """
        return

    ####### Generic functions for every backtest
    def construct_strategy(self, br = None):
        """
        construct_strategy - Constructs the returns for all the strategies which have been specified.

        - gets parameters form fill_backtest_request
        - market data from fill_assets

        """

        time_series_calcs = TimeSeriesCalcs()

        # get the parameters for backtesting
        if hasattr(self, 'br'):
            br = self.br
        elif br is None:
            br = self.fill_backtest_request()

        # get market data for backtest
        asset_df, spot_df, spot_df2, basket_dict = self.fill_assets()

        if hasattr(br, 'tech_params'):
            tech_params = br.tech_params
        else:
            tech_params = TechParams()

        cumresults = pandas.DataFrame(index = asset_df.index)
        portleverage = pandas.DataFrame(index = asset_df.index)

        from collections import OrderedDict
        tsdresults = OrderedDict()

        # each portfolio key calculate returns - can put parts of the portfolio in the key
        for key in basket_dict.keys():
            asset_cut_df = asset_df[[x +'.close' for x in basket_dict[key]]]
            spot_cut_df = spot_df[[x +'.close' for x in basket_dict[key]]]

            self.logger.info("Calculating " + key)

            results, cash_backtest = self.construct_individual_strategy(br, spot_cut_df, spot_df2, asset_cut_df, tech_params, key)

            cumresults[results.columns[0]] = results
            portleverage[results.columns[0]] = cash_backtest.get_porfolio_leverage()
            tsdresults[key] = cash_backtest.get_portfolio_pnl_tsd()

            # for a key, designated as the final strategy save that as the "strategy"
            if key == self.FINAL_STRATEGY:
                self._strategy_pnl = results
                self._strategy_pnl_tsd = cash_backtest.get_portfolio_pnl_tsd()
                self._strategy_leverage = cash_backtest.get_porfolio_leverage()
                self._strategy_signal = cash_backtest.get_porfolio_signal()
                self._strategy_pnl_trades = cash_backtest.get_pnl_trades()

        # get benchmark for comparison
        benchmark = self.construct_strategy_benchmark()

        cumresults_benchmark = self.compare_strategy_vs_benchmark(br, cumresults, benchmark)

        self._strategy_group_benchmark_tsd = tsdresults

        if hasattr(self, '_benchmark_tsd'):
            tsdlist = tsdresults
            tsdlist['Benchmark'] = (self._benchmark_tsd)
            self._strategy_group_benchmark_tsd = tsdlist

        # calculate annualised returns
        years = time_series_calcs.average_by_annualised_year(time_series_calcs.calculate_returns(cumresults_benchmark))

        self._strategy_group_pnl = cumresults
        self._strategy_group_pnl_tsd = tsdresults
        self._strategy_group_benchmark_pnl = cumresults_benchmark
        self._strategy_group_leverage = portleverage
        self._strategy_group_benchmark_annualised_pnl = years

    def construct_individual_strategy(self, br, spot_df, spot_df2, asset_df, tech_params, key):
        """
        construct_individual_strategy - Combines the signal with asset returns to find the returns of an individual
        strategy

        Parameters
        ----------
        br : BacktestRequest
            Parameters for backtest such as start and finish dates

        spot_df : pandas.DataFrame
            Market time series for generating signals

        spot_df2 : pandas.DataFrame
            Market time series for generated signals (can be of different frequency)

        tech_params : TechParams
            Parameters for generating signals

        Returns
        -------
        cumportfolio : pandas.DataFrame
        cash_backtest : CashBacktest
        """
        cash_backtest = CashBacktest()

        signal_df = self.construct_signal(spot_df, spot_df2, tech_params, br)   # get trading signal
        cash_backtest.calculate_trading_PnL(br, asset_df, signal_df)            # calculate P&L

        cumpnl = cash_backtest.get_cumpnl()

        if br.write_csv: cumpnl.to_csv(self.DUMP_CSV + key + ".csv")

        cumportfolio = cash_backtest.get_cumportfolio()

        if br.calc_stats:
            cumportfolio.columns = [key + ' ' + str(cash_backtest.get_portfolio_pnl_desc()[0])]
        else:
            cumportfolio.columns = [key]

        return cumportfolio, cash_backtest

    def compare_strategy_vs_benchmark(self, br, strategy_df, benchmark_df):
        """
        compare_strategy_vs_benchmark - Compares the trading strategy we are backtesting against a benchmark

        Parameters
        ----------
        br : BacktestRequest
            Parameters for backtest such as start and finish dates

        strategy_df : pandas.DataFrame
            Strategy time series

        benchmark_df : pandas.DataFrame
            Benchmark time series
        """

        include_benchmark = False
        calc_stats = False

        if hasattr(br, 'include_benchmark'): include_benchmark = br.include_benchmark
        if hasattr(br, 'calc_stats'): calc_stats = br.calc_stats

        if include_benchmark:
            tsd = TimeSeriesDesc()
            cash_backtest = CashBacktest()
            ts_filter = TimeSeriesFilter()
            ts_calcs = TimeSeriesCalcs()

            # align strategy time series with that of benchmark
            strategy_df, benchmark_df = strategy_df.align(benchmark_df, join='left', axis = 0)

            # if necessary apply vol target to benchmark (to make it comparable with strategy)
            if hasattr(br, 'portfolio_vol_adjust'):
                if br.portfolio_vol_adjust is True:
                    benchmark_df = cash_backtest.calculate_vol_adjusted_index_from_prices(benchmark_df, br = br)

            # only calculate return statistics if this has been specified
            if calc_stats:
                tsd.calculate_ret_stats_from_prices(benchmark_df, br.ann_factor)
                benchmark_df.columns = tsd.summary()

            # realign strategy & benchmark
            strategy_benchmark_df = strategy_df.join(benchmark_df, how='inner')
            strategy_benchmark_df = strategy_benchmark_df.fillna(method='ffill')

            strategy_benchmark_df = ts_filter.filter_time_series_by_date(br.plot_start, br.finish_date, strategy_benchmark_df)
            strategy_benchmark_df = ts_calcs.create_mult_index_from_prices(strategy_benchmark_df)

            self._benchmark_pnl = benchmark_df
            self._benchmark_tsd = tsd

            return strategy_benchmark_df

        return strategy_df

    def get_strategy_name(self):
        return self.FINAL_STRATEGY

    def get_individual_leverage(self):
        return self._individual_leverage

    def get_strategy_group_pnl_trades(self):
        return self._strategy_pnl_trades

    def get_strategy_pnl(self):
        return self._strategy_pnl

    def get_strategy_pnl_tsd(self):
        return self._strategy_pnl_tsd

    def get_strategy_leverage(self):
        return self._strategy_leverage

    def get_strategy_group_benchmark_pnl(self):
        return self._strategy_group_benchmark_pnl

    def get_strategy_group_benchmark_tsd(self):
        return self._strategy_group_benchmark_tsd

    def get_strategy_leverage(self):
        return self._strategy_group_leverage

    def get_strategy_signal(self):
        return self._strategy_signal

    def get_benchmark(self):
        return self._benchmark_pnl

    def get_benchmark_tsd(self):
        return self._benchmark_tsd

    def get_strategy_group_benchmark_annualised_pnl(self):
        return self._strategy_group_benchmark_annualised_pnl

    #### Plotting

    def reduce_plot(self, data_frame):
        """
        reduce_plot - Reduces the frequency of a time series to every business day so it can be plotted more easily

        Parameters
        ----------
        data_frame: pandas.DataFrame
            Strategy time series

        Returns
        -------
        pandas.DataFrame
        """
        try:
            # make plots on every business day (will downsample intraday data)
            data_frame = data_frame.resample('B')
            data_frame = data_frame.fillna(method='pad')

            return data_frame
        except:
            return data_frame

    ##### Quick helper functions to plot aspects of the strategy such as P&L, leverage etc.
    def plot_individual_leverage(self):
        pf = PlotFactory()
        gp = GraphProperties()

        gp.title = self.FINAL_STRATEGY + ' Leverage'
        gp.display_legend = True
        gp.scale_factor = self.SCALE_FACTOR

        gp.file_output = self.DUMP_PATH + self.FINAL_STRATEGY + ' (Individual Leverage).png'

        try:
            pf.plot_line_graph(self.reduce_plot(self._individual_leverage), adapter = 'pythalesians', gp = gp)
        except: pass

    def plot_strategy_group_pnl_trades(self):
        pf = PlotFactory()
        gp = GraphProperties()

        gp.title = self.FINAL_STRATEGY + " (bp)"
        gp.display_legend = True
        gp.scale_factor = self.SCALE_FACTOR

        gp.file_output = self.DUMP_PATH + self.FINAL_STRATEGY + ' (Individual Trade PnL).png'

        # zero when there isn't a trade exit
        # strategy_pnl_trades = self._strategy_pnl_trades * 100 * 100
        # strategy_pnl_trades = strategy_pnl_trades.dropna()

        # note only works with single large basket trade
        try:
            strategy_pnl_trades = self._strategy_pnl_trades.fillna(0) * 100 * 100
            pf.plot_line_graph(self.reduce_plot(strategy_pnl_trades), adapter = 'pythalesians', gp = gp)
        except: pass

    def plot_strategy_pnl(self):
        pf = PlotFactory()
        gp = GraphProperties()

        gp.title = self.FINAL_STRATEGY
        gp.display_legend = True
        gp.scale_factor = self.SCALE_FACTOR

        gp.file_output = self.DUMP_PATH + self.FINAL_STRATEGY + ' (Strategy PnL).png'

        try:
            pf.plot_line_graph(self.reduce_plot(self._strategy_pnl), adapter = 'pythalesians', gp = gp)
        except: pass

    def plot_strategy_signal_proportion(self, strip = None):

        signal = self._strategy_signal

        long = signal[signal > 0].count()
        short = signal[signal < 0].count()
        flat = signal[signal == 0].count()

        keys = long.index

        trades = abs(signal - signal.shift(-1))
        trades = trades[trades > 0].count()

        df_trades = pandas.DataFrame(index = keys, columns = ['Trades'], data = trades)

        df = pandas.DataFrame(index = keys, columns = ['Long', 'Short', 'Flat'])

        df['Long'] = long
        df['Short']  = short
        df['Flat'] = flat

        if strip is not None: keys = [k.replace(strip, '') for k in keys]

        df.index = keys
        df_trades.index = keys
        # df = df.sort_index()

        pf = PlotFactory()
        gp = GraphProperties()

        gp.title = self.FINAL_STRATEGY
        gp.display_legend = True
        gp.scale_factor = self.SCALE_FACTOR

        try:
            gp.file_output = self.DUMP_PATH + self.FINAL_STRATEGY + ' (Strategy signal proportion).png'
            pf.plot_bar_graph(self.reduce_plot(df), adapter = 'pythalesians', gp = gp)

            gp.file_output = self.DUMP_PATH + self.FINAL_STRATEGY + ' (Strategy trade no).png'
            pf.plot_bar_graph(self.reduce_plot(df_trades), adapter = 'pythalesians', gp = gp)
        except: pass

    def plot_strategy_leverage(self):
        pf = PlotFactory()
        gp = GraphProperties()

        gp.title = self.FINAL_STRATEGY + ' Leverage'
        gp.display_legend = True
        gp.scale_factor = self.SCALE_FACTOR

        gp.file_output = self.DUMP_PATH + self.FINAL_STRATEGY + ' (Strategy Leverage).png'

        try:
            pf.plot_line_graph(self.reduce_plot(self._strategy_leverage), adapter = 'pythalesians', gp = gp)
        except: pass

    def plot_strategy_group_benchmark_pnl(self, strip = None):
        pf = PlotFactory()
        gp = GraphProperties()

        gp.title = self.FINAL_STRATEGY
        gp.display_legend = True
        gp.scale_factor = self.SCALE_FACTOR
        #gp.color = 'RdYlGn'

        gp.file_output = self.DUMP_PATH + self.FINAL_STRATEGY + ' (Group Benchmark PnL - cumulative).png'

        strat_list = self._strategy_group_benchmark_pnl.columns #.sort_values()

        for line in strat_list:
            self.logger.info(line)

        # plot cumulative line of returns
        pf.plot_line_graph(self.reduce_plot(self._strategy_group_benchmark_pnl), adapter = 'pythalesians', gp = gp)

        # needs write stats flag turned on
        try:
            keys = self._strategy_group_benchmark_tsd.keys()
            ir = []

            for key in keys: ir.append(self._strategy_group_benchmark_tsd[key].inforatio()[0])

            if strip is not None: keys = [k.replace(strip, '') for k in keys]

            ret_stats = pandas.DataFrame(index = keys, data = ir, columns = ['IR'])
            # ret_stats = ret_stats.sort_index()
            gp.file_output = self.DUMP_PATH + self.FINAL_STRATEGY + ' (Group Benchmark PnL - IR).png'

            gp.display_brand_label = False

            # plot ret stats
            pf.plot_bar_graph(ret_stats, adapter = 'pythalesians', gp = gp)

        except: pass

    def plot_strategy_group_benchmark_annualised_pnl(self, cols = None):
        # TODO - unfinished, needs checking!

        if cols is None: cols = self._strategy_group_benchmark_annualised_pnl.columns

        pf = PlotFactory()
        gp = GraphProperties()

        gp.title = self.FINAL_STRATEGY
        gp.display_legend = True
        gp.scale_factor = self.SCALE_FACTOR
        gp.color = ['red', 'blue', 'purple', 'gray', 'yellow', 'green', 'pink']

        gp.file_output = self.DUMP_PATH + self.FINAL_STRATEGY + ' (Group Benchmark Annualised PnL).png'

        pf.plot_line_graph(self.reduce_plot(self._strategy_group_benchmark_annualised_pnl[cols]), adapter = 'pythalesians', gp = gp)

    def plot_strategy_group_leverage(self):
        pf = PlotFactory()
        gp = GraphProperties()

        gp.title = self.FINAL_STRATEGY + ' Leverage'
        gp.display_legend = True
        gp.scale_factor = self.SCALE_FACTOR

        gp.file_output = self.DUMP_PATH + self.FINAL_STRATEGY + ' (Group Leverage).png'

        pf.plot_line_graph(self.reduce_plot(self._strategy_group_leverage), adapter = 'pythalesians', gp = gp)
