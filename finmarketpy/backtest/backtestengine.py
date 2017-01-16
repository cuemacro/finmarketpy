__author__ = 'saeedamen'

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

import numpy

from findatapy.util import LoggerManager

class Backtest(object):
    """Conducts backtest for strategies trading assets. Assumes we have an input of total returns. Reports historical return statistics
    and returns time series.

    """

    def __init__(self):
        self.logger = LoggerManager().getLogger(__name__)
        self._pnl = None
        self._portfolio = None
        return

    def calculate_diagnostic_trading_PnL(self, asset_a_df, signal_df, further_df = [], further_df_labels = []):
        """Calculates P&L table which can be used for debugging purposes,

        The table is populated with asset, signal and further dataframes provided by the user, can be used to check signalling methodology.
        It does not apply parameters such as transaction costs, vol adjusment and so on.

        Parameters
        ----------
        asset_a_df : DataFrame
            Asset prices

        signal_df : DataFrame
            Trade signals (typically +1, -1, 0 etc)

        further_df : DataFrame
            Further dataframes user wishes to output in the diagnostic output (typically inputs for the signals)

        further_df_labels
            Labels to append to the further dataframes

        Returns
        -------
        DataFrame with asset, trading signals and returns of the trading strategy for diagnostic purposes

        """
        calculations = Calculations()
        asset_rets_df = calculations.calculate_returns(asset_a_df)
        strategy_rets = calculations.calculate_signal_returns(signal_df, asset_rets_df)

        reset_points = ((signal_df - signal_df.shift(1)).abs())

        asset_a_df_entry = asset_a_df.copy(deep=True)
        asset_a_df_entry[reset_points == 0] = numpy.nan
        asset_a_df_entry = asset_a_df_entry.ffill()

        asset_a_df_entry.columns = [x + '_entry' for x in asset_a_df_entry.columns]
        asset_rets_df.columns = [x + '_asset_rets' for x in asset_rets_df.columns]
        strategy_rets.columns = [x + '_strat_rets' for x in strategy_rets.columns]
        signal_df.columns = [x + '_final_signal' for x in signal_df.columns]

        for i in range(0, len(further_df)):
            further_df[i].columns = [x + '_' + further_df_labels[i] for x in further_df[i].columns]

        flatten_df =[asset_a_df, asset_a_df_entry, asset_rets_df, strategy_rets, signal_df]

        for f in further_df:
            flatten_df.append(f)

        return calculations.pandas_outer_join(flatten_df)


    def calculate_trading_PnL(self, br, asset_a_df, signal_df, contract_value_df = None):
        """Calculates P&L of a trading strategy and statistics to be retrieved later

        Calculates the P&L for each asset/signal combination and also for the finally strategy applying appropriate
        weighting in the portfolio, depending on predefined parameters, for example:
            static weighting for each asset
            static weighting for each asset + vol weighting for each asset
            static weighting for each asset + vol weighting for each asset + vol weighting for the portfolio

        Parameters
        ----------
        br : BacktestRequest
            Parameters for the backtest specifying start date, finish data, transaction costs etc.

        asset_a_df : pandas.DataFrame
            Asset prices to be traded

        signal_df : pandas.DataFrame
            Signals for the trading strategy

        contract_value_df : pandas.DataFrame
            Daily size of contracts
        """

        calculations = Calculations()

        # make sure the dates of both traded asset and signal are aligned properly
        asset_df, signal_df = asset_a_df.align(signal_df, join='left', axis = 'index')

        if (contract_value_df is not None):
            asset_df, contract_value_df = asset_df.align(contract_value_df, join='left', axis='index')
            contract_value_df = contract_value_df.fillna(method='ffill')  # fill down asset holidays (we won't trade on these days)

        # non-trading days
        non_trading_days = numpy.isnan(asset_df.values)

        # only allow signals to change on the days when we can trade assets
        signal_df = signal_df.mask(non_trading_days)                # fill asset holidays with NaN signals
        signal_df = signal_df.fillna(method='ffill')                # fill these down

        tc = br.spot_tc_bp

        signal_cols = signal_df.columns.values
        asset_df_cols = asset_df.columns.values

        pnl_cols = []

        for i in range(0, len(asset_df_cols)):
            pnl_cols.append(asset_df_cols[i] + " / " + signal_cols[i])

        asset_df_copy = asset_df.copy()
        asset_df = asset_df.fillna(method='ffill')        # fill down asset holidays (we won't trade on these days)
        returns_df = calculations.calculate_returns(asset_df)

        # apply a stop loss/take profit to every trade if this has been specified
        # do this before we start to do vol weighting etc.
        if hasattr(br, 'take_profit') and hasattr(br, 'stop_loss'):
            returns_df = calculations.calculate_returns(asset_df)

            temp_strategy_rets_df = calculations.calculate_signal_returns(signal_df, returns_df)
            trade_rets_df = calculations.calculate_cum_rets_trades(signal_df, temp_strategy_rets_df)

            # pre_signal_df = signal_df.copy()

            signal_df = calculations.calculate_risk_stop_signals(signal_df, trade_rets_df, br.stop_loss, br.take_profit)

            # make sure we can't trade where asset price is undefined and carry over signal
            signal_df = signal_df.mask(non_trading_days)  # fill asset holidays with NaN signals
            signal_df = signal_df.fillna(method='ffill')  # fill these down (when asset is not trading

            # signal_df.columns = [x + '_final_signal' for x in signal_df.columns]

            # for debugging purposes
            # if False:
            #     signal_df_copy = signal_df.copy()
            #     trade_rets_df_copy = trade_rets_df.copy()
            #
            #     asset_df_copy.columns = [x + '_asset' for x in temp_strategy_rets_df.columns]
            #     temp_strategy_rets_df.columns = [x + '_strategy_rets' for x in temp_strategy_rets_df.columns]
            #     signal_df_copy.columns = [x + '_final_signal' for x in signal_df_copy.columns]
            #     trade_rets_df_copy.columns = [x + '_cum_trade' for x in trade_rets_df_copy.columns]
            #
            #     to_plot = calculations.pandas_outer_join([asset_df_copy, pre_signal_df, signal_df_copy, trade_rets_df_copy, temp_strategy_rets_df])
            #     to_plot.to_csv('test.csv')

        # do we have a vol target for individual signals?
        if hasattr(br, 'signal_vol_adjust'):
            if br.signal_vol_adjust is True:
                risk_engine = RiskEngine()

                if not(hasattr(br, 'signal_vol_resample_type')):
                    br.signal_vol_resample_type = 'mean'

                if not(hasattr(br, 'signal_vol_resample_freq')):
                    br.signal_vol_resample_freq = None

                if not(hasattr(br, 'signal_vol_period_shift')):
                    br.signal_vol_period_shift = 0

                leverage_df = risk_engine.calculate_leverage_factor(returns_df, br.signal_vol_target, br.signal_vol_max_leverage,
                                               br.signal_vol_periods, br.signal_vol_obs_in_year,
                                               br.signal_vol_rebalance_freq, br.signal_vol_resample_freq,
                                               br.signal_vol_resample_type, period_shift=br.signal_vol_period_shift)

                signal_df = pandas.DataFrame(
                    signal_df.values * leverage_df.values, index = signal_df.index, columns = signal_df.columns)

                self._individual_leverage = leverage_df     # contains leverage of individual signal (before portfolio vol target)

        _pnl = calculations.calculate_signal_returns_with_tc_matrix(signal_df, returns_df, tc = tc)
        _pnl.columns = pnl_cols

        adjusted_weights_matrix = None

        # portfolio is average of the underlying signals: should we sum them or average them?
        if hasattr(br, 'portfolio_combination'):
            if br.portfolio_combination == 'sum':
                portfolio = pandas.DataFrame(data = _pnl.sum(axis = 1), index = _pnl.index, columns = ['Portfolio'])
            elif br.portfolio_combination == 'mean':
                portfolio = pandas.DataFrame(data = _pnl.mean(axis = 1), index = _pnl.index, columns = ['Portfolio'])

                adjusted_weights_matrix = self.create_portfolio_weights(br, _pnl, method='mean')
            elif isinstance(br.portfolio_combination, dict):
                # get the weights for each asset
                adjusted_weights_matrix = self.create_portfolio_weights(br, _pnl, method='weighted')

                portfolio = pandas.DataFrame(data=(_pnl.values * adjusted_weights_matrix), index=_pnl.index)
                is_all_na = pandas.isnull(portfolio).all(axis=1)
                portfolio = pandas.DataFrame(portfolio.sum(axis = 1), columns = ['Portfolio'])

                # overwrite days when every asset PnL was null is NaN with nan
                portfolio[is_all_na] = numpy.nan
        else:
            portfolio = pandas.DataFrame(data = _pnl.mean(axis = 1), index = _pnl.index, columns = ['Portfolio'])

            adjusted_weights_matrix = self.create_portfolio_weights(br, _pnl, method='mean')

        portfolio_leverage_df = pandas.DataFrame(data = numpy.ones(len(_pnl.index)), index = _pnl.index, columns = ['Portfolio'])

        # should we apply vol target on a portfolio level basis?
        if hasattr(br, 'portfolio_vol_adjust'):
            if br.portfolio_vol_adjust is True:
                risk_engine = RiskEngine()

                portfolio, portfolio_leverage_df = risk_engine.calculate_vol_adjusted_returns(portfolio, br = br)

        self._portfolio = portfolio
        self._signal = signal_df                            # individual signals (before portfolio leverage)
        self._portfolio_leverage = portfolio_leverage_df    # leverage on portfolio

        # multiply portfolio leverage * individual signals to get final position signals
        length_cols = len(signal_df.columns)
        leverage_matrix = numpy.repeat(portfolio_leverage_df.values.flatten()[numpy.newaxis,:], length_cols, 0)

        # final portfolio signals (including signal & portfolio leverage)
        self._portfolio_signal = pandas.DataFrame(
            data = numpy.multiply(numpy.transpose(leverage_matrix), signal_df.values),
            index = signal_df.index, columns = signal_df.columns)

        if hasattr(br, 'portfolio_combination'):
            if br.portfolio_combination == 'sum':
                pass
            elif br.portfolio_combination == 'mean' or isinstance(br.portfolio_combination, dict):
                self._portfolio_signal = pandas.DataFrame(data=(self._portfolio_signal.values * adjusted_weights_matrix),
                                             index=self._portfolio_signal.index,
                                             columns=self._portfolio_signal.columns)
        else:
            self._portfolio_signal = pandas.DataFrame(data=(self._portfolio_signal.values * adjusted_weights_matrix),
                                                      index=self._portfolio_signal.index,
                                                      columns=self._portfolio_signal.columns)

        # calculate each period of trades
        self._portfolio_trade = self._portfolio_signal - self._portfolio_signal.shift(1)

        self._portfolio_signal_notional = None
        self._portfolio_signal_trade_notional = None

        self._portfolio_signal_contracts = None
        self._portfolio_signal_trade_contracts = None

        # also create other measures of portfolio
        # portfolio & trades in terms of a predefined notional (in USD)
        # portfolio & trades in terms of contract sizes (particularly useful for futures)
        if hasattr(br, 'portfolio_notional_size'):
            # express positions in terms of the notional size specified
            self._portfolio_signal_notional = self._portfolio_signal * br.portfolio_notional_size
            self._portfolio_signal_trade_notional = self._portfolio_signal_notional - self._portfolio_signal_notional.shift(1)

            # get the positions in terms of the contract sizes
            notional_copy = self._portfolio_signal_notional.copy(deep=True)
            notional_copy_cols = [x.split('.')[0] for x in notional_copy.columns]
            notional_copy_cols = [x + '.contract-value' for x in notional_copy_cols]

            notional_copy.columns = notional_copy_cols

            contract_value_df = contract_value_df[notional_copy_cols]
            notional_df, contract_value_df = notional_copy.align(contract_value_df, join='left', axis='index')

            # careful make sure orders of magnitude are same for the notional and the contract value
            self._portfolio_signal_contracts = notional_df / contract_value_df
            self._portfolio_signal_contracts.columns = self._portfolio_signal_notional.columns
            self._portfolio_signal_trade_contracts = self._portfolio_signal_contracts - self._portfolio_signal_contracts.shift(1)

        self._pnl = _pnl                                                                    # individual signals P&L

        # TODO FIX very slow - hence only calculate on demand
        _pnl_trades = None
        # _pnl_trades = calculations.calculate_individual_trade_gains(signal_df, _pnl)
        self._pnl_trades = _pnl_trades

        self._ret_stats_pnl = RetStats()
        self._ret_stats_pnl.calculate_ret_stats(self._pnl, br.ann_factor)

        self._portfolio.columns = ['Port']
        self._ret_stats_portfolio = RetStats()
        self._ret_stats_portfolio.calculate_ret_stats(self._portfolio, br.ann_factor)

        self._cumpnl = calculations.create_mult_index(self._pnl)                             # individual signals cumulative P&L
        self._cumpnl.columns = pnl_cols

        self._cumportfolio = calculations.create_mult_index(self._portfolio)                 # portfolio cumulative P&L
        self._cumportfolio.columns = ['Port']

    def create_portfolio_weights(self, br, _pnl, method='mean'):
        """Calculates P&L of a trading strategy and statistics to be retrieved later

        Parameters
        ----------
        br : BacktestRequest
            Parameters for the backtest specifying start date, finish data, transaction costs etc.

        _pnl : pandas.DataFrame
            Contains the daily P&L for the portfolio

        method : String
            'mean' - assumes equal weighting for each signal
            'weighted' - can use predefined user weights (eg. if we assign weighting of 1, 1, 0.5, for three signals
            the third signal will have a weighting of half versus the others)

        Returns
        -------
        pandas.DataFrame
            Contains the portfolio weights
        """
        if method == 'mean':
            weights_vector = numpy.ones(len(_pnl.columns))
        elif method == 'weighted':
            # get the weights for each asset
            weights_vector = numpy.array([float(br.portfolio_combination[col]) for col in _pnl.columns])

        # repeat this down for every day
        weights_matrix = numpy.repeat(weights_vector[numpy.newaxis, :], len(_pnl.index), 0)

        # where we don't have old price data, make the weights 0 there
        ind = numpy.isnan(_pnl.values)
        weights_matrix[ind] = 0

        # the total weights will vary, as historically might not have all the assets trading
        total_weights = numpy.sum(weights_matrix, axis=1)

        # replicate across columns
        total_weights = numpy.transpose(numpy.repeat(total_weights[numpy.newaxis, :], len(_pnl.columns), 0))

        # to avoid divide by zero
        total_weights[total_weights == 0.0] = 1.0

        adjusted_weights_matrix = weights_matrix / total_weights
        adjusted_weights_matrix[ind] = numpy.nan

        return adjusted_weights_matrix

    def get_backtest_output(self):
        return

    def get_pnl(self):
        """Gets P&L returns

        Returns
        -------
        pandas.Dataframe
        """
        return self._pnl

    def get_pnl_trades(self):
        """Gets P&L of each individual trade per signal

        Returns
        -------
        pandas.Dataframe
        """

        if self._pnl_trades is None:
            calculations = Calculations()
            self._pnl_trades = calculations.calculate_individual_trade_gains(self._signal, self._pnl)

        return self._pnl_trades

    def get_pnl_desc(self):
        """Gets P&L return statistics in a string format

        Returns
        -------
        str
        """
        return self._ret_stats_signals.summary()

    def get_pnl_ret_stats(self):
        """Gets P&L return statistics of individual strategies as class to be queried

        Returns
        -------
        TimeSeriesDesc
        """

        return self._ret_stats_pnl

    def get_cumpnl(self):
        """Gets P&L as a cumulative time series of individual assets

        Returns
        -------
        pandas.DataFrame
        """

        return self._cumpnl

    def get_cumportfolio(self):
        """Gets P&L as a cumulative time series of portfolio

        Returns
        -------
        pandas.DataFrame
        """

        return self._cumportfolio

    def get_portfolio_pnl(self):
        """Gets portfolio returns in raw form (ie. not indexed into cumulative form)

        Returns
        -------
        pandas.DataFrame
        """

        return self._portfolio

    def get_portfolio_pnl_desc(self):
        """Gets P&L return statistics of portfolio as string

        Returns
        -------
        pandas.DataFrame
        """

        return self._ret_stats_portfolio.summary()

    def get_portfolio_pnl_ret_stats(self):
        """Gets P&L return statistics of portfolio as class to be queried

        Returns
        -------
        RetStats
        """

        return self._ret_stats_portfolio

    def get_individual_leverage(self):
        """Gets leverage for each asset historically

        Returns
        -------
        pandas.DataFrame
        """

        return self._individual_leverage

    def get_portfolio_leverage(self):
        """Gets the leverage for the portfolio

        Returns
        -------
        pandas.DataFrame
        """

        return self._portfolio_leverage

    def get_portfolio_signal(self):
        """Gets the signals (with individual leverage & portfolio leverage) for each asset, which
        equates to what we would trade in practice

        Returns
        -------
        DataFrame
        """

        return self._portfolio_signal

    def get_portfolio_trade(self):
        """Gets the trades (with individual leverage & portfolio leverage) for each asset, which
        we'd need to execute

        Returns
        -------
        DataFrame
        """

        return self._portfolio_trade

    def get_portfolio_signal_notional(self):
        """Gets the signals (with individual leverage & portfolio leverage) for each asset, which
        equates to what we would have a positions in practice, scaled by a notional amount we have already specified

        Returns
        -------
        DataFrame
        """

        return self._portfolio_signal_notional

    def get_portfolio_trade_notional(self):
        """Gets the trades (with individual leverage & portfolio leverage) for each asset, which
        we'd need to execute, scaled by a notional amount we have already specified

        Returns
        -------
        DataFrame
        """

        return self._portfolio_signal_trade_notional

    def get_portfolio_signal_contracts(self):
        """Gets the signals (with individual leverage & portfolio leverage) for each asset, which
        equates to what we would have a positions in practice, scaled by a notional amount and into contract sizes (eg. for futures)
        which we need to specify in another dataframe

        Returns
        -------
        DataFrame
        """

        return self._portfolio_signal_contracts

    def get_portfolio_trade_contracts(self):
        """Gets the trades (with individual leverage & portfolio leverage) for each asset, which
        we'd need to execute, scaled by a notional amount we have already specified and into contract sizes (eg. for futures)
        which we need to specify in another dataframe

        Returns
        -------
        DataFrame
        """

        return self._portfolio_signal_trade_contracts

    def get_signal(self):
        """(with individual leverage, but excluding portfolio leverage) for each asset

        Returns
        -------
        pandas.DataFrame
        """

        return self._signal


########################################################################################################################

import abc
import pandas
import datetime

from chartpy import Chart, Style, ChartConstants

from finmarketpy.economics import TechParams
from findatapy.timeseries import Calculations, RetStats, Filter

class TradingModel(object):
    """Abstract class which wraps around Backtest, providing convenient functions for analaysis. Implement your own
    subclasses of this for your own strategy. See tradingmodelfxtrend_example.py for a simple implementation of a
    FX trend following strategy.

    """

    #### Default parameters for outputting of results from trading model
    SAVE_FIGURES = True
    DEFAULT_PLOT_ENGINE = ChartConstants().chartfactory_default_engine
    SCALE_FACTOR = ChartConstants().chartfactory_scale_factor
    CHART_SOURCE = ChartConstants().chartfactory_source

    DUMP_CSV = ''
    DUMP_PATH = datetime.date.today().strftime("%Y%m%d") + ' '

    logger = LoggerManager().getLogger(__name__)

    def __init__(self):
        pass

    # to be implemented by every trading strategy
    @abc.abstractmethod
    def load_parameters(self):
        """Fills parameters for the backtest, such as start-end dates, transaction costs etc. To
        be implemented by subclass.
        """
        return

    @abc.abstractmethod
    def load_assets(self):
        """Loads time series for the assets to be traded and also for data for generating signals.
        """
        return

    @abc.abstractmethod
    def construct_signal(self, spot_df, spot_df2, tech_params):
        """Constructs signal from pre-loaded time series

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
        """Constructs the returns for all the strategies which have been specified.

        It gets backtesting parameters from fill_backtest_request (although these can be overwritten
        and then market data from fill_assets

        Parameters
        ----------
        br : BacktestRequest
            Parameters which define the backtest (for example start date, end date, transaction costs etc.

        """

        calculations = Calculations()

        # get the parameters for backtesting
        if hasattr(self, 'br'):
            br = self.br
        elif br is None:
            br = self.load_parameters()

        # get market data for backtest
        market_data = self.load_assets()

        asset_df = market_data[0]
        spot_df = market_data[1]
        spot_df2 = market_data[2]
        basket_dict = market_data[3]

        # optional database output
        contract_value_df = None

        if len(market_data) == 5:
            contract_value_df = market_data[4]

        if hasattr(br, 'tech_params'):
            tech_params = br.tech_params
        else:
            tech_params = TechParams()

        cumresults = pandas.DataFrame(index = asset_df.index)
        portleverage = pandas.DataFrame(index = asset_df.index)

        from collections import OrderedDict
        ret_statsresults = OrderedDict()

        # each portfolio key calculate returns - can put parts of the portfolio in the key
        for key in basket_dict.keys():
            asset_cut_df = asset_df[[x +'.close' for x in basket_dict[key]]]
            spot_cut_df = spot_df[[x +'.close' for x in basket_dict[key]]]

            self.logger.info("Calculating " + key)

            results, backtest = self.construct_individual_strategy(br, spot_cut_df, spot_df2, asset_cut_df, tech_params, key,
                                                                   contract_value_df = contract_value_df)

            cumresults[results.columns[0]] = results
            portleverage[results.columns[0]] = backtest.get_portfolio_leverage()
            ret_statsresults[key] = backtest.get_portfolio_pnl_ret_stats()

            # for a key, designated as the final strategy save that as the "strategy"
            if key == self.FINAL_STRATEGY:
                self._strategy_pnl = results
                self._strategy_pnl_ret_stats = backtest.get_portfolio_pnl_ret_stats()
                self._strategy_leverage = backtest.get_portfolio_leverage()

                # collect the position sizes and trade sizes (in several different formats)
                self._strategy_signal = backtest.get_portfolio_signal()
                self._strategy_trade = backtest.get_portfolio_trade()

                # scaled by notional
                self._strategy_signal_notional = backtest.get_portfolio_signal_notional()
                self._strategy_trade_notional = backtest.get_portfolio_trade_notional()

                # scaled by notional and adjusted into contract sizes
                self._strategy_signal_contracts = backtest.get_portfolio_signal_contracts()
                self._strategy_trade_contracts = backtest.get_portfolio_trade_contracts()

                self._strategy_pnl_trades = backtest.get_pnl_trades()

        # get benchmark for comparison
        benchmark = self.construct_strategy_benchmark()

        cumresults_benchmark = self.compare_strategy_vs_benchmark(br, cumresults, benchmark)

        self._strategy_group_benchmark_ret_stats = ret_statsresults

        if hasattr(self, '_benchmark_ret_stats'):
            ret_statslist = ret_statsresults
            ret_statslist['Benchmark'] = (self._benchmark_ret_stats)
            self._strategy_group_benchmark_ret_stats = ret_statslist

        # calculate annualised returns
        years = calculations.average_by_annualised_year(calculations.calculate_returns(cumresults_benchmark))

        self._strategy_group_pnl = cumresults
        self._strategy_group_pnl_ret_stats = ret_statsresults
        self._strategy_group_benchmark_pnl = cumresults_benchmark
        self._strategy_group_leverage = portleverage
        self._strategy_group_benchmark_annualised_pnl = years

    def construct_individual_strategy(self, br, spot_df, spot_df2, asset_df, tech_params, key, contract_value_df = None):
        """Combines the signal with asset returns to find the returns of an individual strategy

        Parameters
        ----------
        br : BacktestRequest
            Parameters for backtest such as start and finish dates

        spot_df : pandas.DataFrame
            Market time series for generating signals

        spot_df2 : pandas.DataFrame
            Secondary Market time series for generated signals (can be of different frequency)

        tech_params : TechParams
            Parameters for generating signals

        contract_value_df : pandas.DataFrame
            Dataframe with the contract sizes for each asset

        Returns
        -------
        cumportfolio : pandas.DataFrame
        backtest : Backtest
        """
        backtest = Backtest()

        signal_df = self.construct_signal(spot_df, spot_df2, tech_params, br)       # get trading signal (raw)
        backtest.calculate_trading_PnL(br, asset_df, signal_df, contract_value_df)   # calculate P&L (and adjust signals for vol etc)

        cumpnl = backtest.get_cumpnl()

        if br.write_csv: cumpnl.to_csv(self.DUMP_CSV + key + ".csv")

        cumportfolio = backtest.get_cumportfolio()

        if br.calc_stats:
            cumportfolio.columns = [key + ' ' + str(backtest.get_portfolio_pnl_desc()[0])]
        else:
            cumportfolio.columns = [key]

        return cumportfolio, backtest

    def compare_strategy_vs_benchmark(self, br, strategy_df, benchmark_df):
        """Compares the trading strategy we are backtesting against a benchmark

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
            ret_stats = RetStats()
            risk_engine = RiskEngine()
            filter = Filter()
            calculations = Calculations()

            # align strategy time series with that of benchmark
            strategy_df, benchmark_df = strategy_df.align(benchmark_df, join='left', axis = 0)

            # if necessary apply vol target to benchmark (to make it comparable with strategy)
            if hasattr(br, 'portfolio_vol_adjust'):
                if br.portfolio_vol_adjust is True:
                    benchmark_df = risk_engine.calculate_vol_adjusted_index_from_prices(benchmark_df, br = br)

            # only calculate return statistics if this has been specified (note when different frequencies of data
            # might underrepresent vol
            # if calc_stats:
            benchmark_df = benchmark_df.fillna(method='ffill')
            ret_stats.calculate_ret_stats_from_prices(benchmark_df, br.ann_factor)

            if calc_stats:
                benchmark_df.columns = ret_stats.summary()

            # realign strategy & benchmark
            strategy_benchmark_df = strategy_df.join(benchmark_df, how='inner')
            strategy_benchmark_df = strategy_benchmark_df.fillna(method='ffill')

            strategy_benchmark_df = filter.filter_time_series_by_date(br.plot_start, br.finish_date, strategy_benchmark_df)
            strategy_benchmark_df = calculations.create_mult_index_from_prices(strategy_benchmark_df)

            self._benchmark_pnl = benchmark_df
            self._benchmark_ret_stats = ret_stats

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

    def get_strategy_pnl_ret_stats(self):
        return self._strategy_pnl_ret_stats

    def get_strategy_leverage(self):
        return self._strategy_leverage

    def get_strategy_group_benchmark_pnl(self):
        return self._strategy_group_benchmark_pnl

    def get_strategy_group_benchmark_ret_stats(self):
        return self._strategy_group_benchmark_ret_stats

    def get_strategy_leverage(self):
        return self._strategy_group_leverage

    def get_strategy_signal(self):
        return self._strategy_signal

    def get_strategy_trade(self):
        return self._strategy_trade

    def get_strategy_signal_notional(self):
        return self._strategy_signal_notional

    def get_strategy_trade_notional(self):
        return self._strategy_trade_notional

    def get_strategy_signal_contracts(self):
        return self._strategy_signal_contracts

    def get_strategy_trade_contracts(self):
        return self._strategy_trade_contracts

    def get_benchmark(self):
        return self._benchmark_pnl

    def get_benchmark_ret_stats(self):
        return self._benchmark_ret_stats

    def get_strategy_group_benchmark_annualised_pnl(self):
        return self._strategy_group_benchmark_annualised_pnl

    #### Plotting

    def reduce_plot(self, data_frame):
        """Reduces the frequency of a time series to every business day so it can be plotted more easily

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
    def plot_individual_leverage(self, silent_plot=False):

        style = self.create_style("Leverage", "Individual Leverage")

        try:
            chart = Chart(self.reduce_plot(self._individual_leverage), engine=self.DEFAULT_PLOT_ENGINE, chart_type='line', style=style)
            if not(silent_plot): chart.plot()
            return chart
        except: pass

    def plot_strategy_group_pnl_trades(self, silent_plot = False):

        style = self.create_style("(bp)", "Individual Trade PnL")

        # zero when there isn't a trade exit
        # strategy_pnl_trades = self._strategy_pnl_trades * 100 * 100
        # strategy_pnl_trades = strategy_pnl_trades.dropna()

        # note only works with single large basket trade
        try:
            strategy_pnl_trades = self._strategy_pnl_trades.fillna(0) * 100 * 100
            chart = Chart(self.reduce_plot(strategy_pnl_trades), engine=self.DEFAULT_PLOT_ENGINE, chart_type='line', style=style)
            if not(silent_plot): chart.plot()
            return chart
        except: pass

    def plot_strategy_pnl(self, silent_plot = False):

        style = self.create_style("", "Strategy PnL")

        try:
            chart = Chart(self.reduce_plot(self._strategy_pnl), engine=self.DEFAULT_PLOT_ENGINE, chart_type='line', style=style)
            if not(silent_plot): chart.plot()
            return chart
        except: pass

    def plot_strategy_trade_no(self, strip = None, silent_plot = False):
        signal = self._strategy_signal

        ####### how many trades have there been (ignore size of the trades)
        trades = abs(signal - signal.shift(-1))
        trades = trades[trades > 0].count()

        df_trades = pandas.DataFrame(index=trades.index, columns=['Trades'], data=trades)

        if strip is not None: df_trades.index = [k.replace(strip, '') for k in df_trades.index]

        style = self.create_style("", "")

        try:
            style.file_output = self.DUMP_PATH + self.FINAL_STRATEGY + ' (Strategy trade no).png'
            style.html_file_output = self.DUMP_PATH + self.FINAL_STRATEGY + ' (Strategy trade no).html'

            chart = Chart(self.reduce_plot(df_trades), engine=self.DEFAULT_PLOT_ENGINE, chart_type='bar', style=style)
            if not(silent_plot): chart.plot()
            return chart
        except:
            pass

    def plot_strategy_signal_proportion(self, strip = None, silent_plot = False):

        signal = self._strategy_signal

        ####### count number of long, short and flat periods in our sample
        long = signal[signal > 0].count()
        short = signal[signal < 0].count()
        flat = signal[signal == 0].count()

        df = pandas.DataFrame(index = long.index, columns = ['Long', 'Short', 'Flat'])

        df['Long'] = long
        df['Short']  = short
        df['Flat'] = flat

        if strip is not None: df.index = [k.replace(strip, '') for k in df.index]

        style = self.create_style("", "")

        try:
            style.file_output = self.DUMP_PATH + self.FINAL_STRATEGY + ' (Strategy signal proportion).png'
            style.html_file_output = self.DUMP_PATH + self.FINAL_STRATEGY + ' (Strategy signal proportion).html'

            chart = Chart(self.reduce_plot(df), engine=self.DEFAULT_PLOT_ENGINE, chart_type='bar', style=style)
            if not(silent_plot): chart.plot()
            return chart
        except: pass

    def plot_strategy_leverage(self, silent_plot = False):
        style = self.create_style("Leverage", "Strategy Leverage")

        try:
            chart = Chart(self.reduce_plot(self._strategy_leverage), engine=self.DEFAULT_PLOT_ENGINE, chart_type='line', style=style)
            if not(silent_plot): chart.plot()
            return chart
        except: pass

    def plot_strategy_group_benchmark_pnl(self, silent_plot = False):

        style = self.create_style("", "Group Benchmark PnL - cumulative")

        strat_list = self._strategy_group_benchmark_pnl.columns #.sort_values()

        for line in strat_list:
            self.logger.info(line)

        # plot cumulative line of returns
        chart = Chart(self.reduce_plot(self._strategy_group_benchmark_pnl), engine=self.DEFAULT_PLOT_ENGINE, chart_type='line',
                      style=style)
        if not (silent_plot): chart.plot()
        return chart

    def plot_strategy_group_benchmark_pnl_ir(self, strip = None, silent_plot = False):

        style = self.create_style("", "Group Benchmark PnL IR - cumulative")
        keys = self._strategy_group_benchmark_ret_stats.keys()
        ir = []

        for key in keys:
            ir.append(self._strategy_group_benchmark_ret_stats[key].inforatio()[0])

        if strip is not None: keys = [k.replace(strip, '') for k in keys]

        ret_stats = pandas.DataFrame(index=keys, data=ir, columns=['IR'])
        # ret_stats = ret_stats.sort_index()
        style.file_output = self.DUMP_PATH + self.FINAL_STRATEGY + ' (Group Benchmark PnL - IR) ' + str(style.scale_factor) + '.png'
        style.html_file_output = self.DUMP_PATH + self.FINAL_STRATEGY + ' (Group Benchmark PnL - IR) ' + str(style.scale_factor) + '.html'
        style.display_brand_label = False

        chart = Chart(ret_stats, engine=self.DEFAULT_PLOT_ENGINE, chart_type='bar', style=style)
        if not (silent_plot): chart.plot()
        return chart

    def plot_strategy_group_benchmark_pnl_yoy(self, strip = None, silent_plot = False):

        style = self.create_style("", "Group Benchmark PnL YoY - cumulative")
        keys = self._strategy_group_benchmark_ret_stats.keys()
        yoy = []

        for key in keys:
            col = self._strategy_group_benchmark_ret_stats[key].yoy_rets()
            col.columns = [key]
            yoy.append(col)

        calculations = Calculations()
        ret_stats = calculations.pandas_outer_join(yoy)
        ret_stats.index = ret_stats.index.year

        if strip is not None: ret_stats.columns = [k.replace(strip, '') for k in ret_stats.columns]

        # ret_stats = ret_stats.sort_index()
        style.file_output = self.DUMP_PATH + self.FINAL_STRATEGY + ' (Group Benchmark PnL - YoY) ' + str(style.scale_factor) + '.png'
        style.html_file_output = self.DUMP_PATH + self.FINAL_STRATEGY + ' (Group Benchmark PnL - YoY) ' + str(style.scale_factor) + '.html'
        style.display_brand_label = False
        style.date_formatter = "%Y"

        chart = Chart(ret_stats * 100, engine=self.DEFAULT_PLOT_ENGINE, chart_type='bar', style=style)
        if not (silent_plot): chart.plot()
        return chart

    def plot_strategy_group_benchmark_annualised_pnl(self, cols = None, silent_plot = False):
        # TODO - unfinished, needs checking!

        if cols is None: cols = self._strategy_group_benchmark_annualised_pnl.columns

        style = self.create_style("", "Group Benchmark Annualised PnL")
        style.color = ['red', 'blue', 'purple', 'gray', 'yellow', 'green', 'pink']

        chart = Chart(self.reduce_plot(self._strategy_group_benchmark_annualised_pnl[cols]), engine=self.DEFAULT_PLOT_ENGINE, chart_type='line', style=style)
        if not (silent_plot): chart.plot()
        return chart

    def plot_strategy_group_leverage(self, silent_plot = False):

        style = self.create_style("Leverage", "Group Leverage")

        chart = Chart(self.reduce_plot(self._strategy_group_leverage), engine=self.DEFAULT_PLOT_ENGINE, chart_type='line', style=style)
        if not (silent_plot): chart.plot()
        return chart

    def plot_strategy_signals(self, date = None, strip = None, silent_plot = False):
        self._plot_signal(self._strategy_signal, label = "positions (% portfolio notional)", caption = "Positions",
                          date = date, strip = strip, silent_plot=silent_plot)

    def plot_strategy_trades(self, date = None, strip = None, silent_plot = False):
        self._plot_signal(self._strategy_trade, label = "trades (% portfolio notional)", caption = "Trades",
                          date = date, strip = strip, silent_plot=silent_plot)

    def plot_strategy_signals_notional(self, date = None, strip = None, silent_plot = False):
        self._plot_signal(self._strategy_signal_notional, label = "positions (scaled by notional)", caption = "Positions",
                          date = date, strip = strip, silent_plot=silent_plot)

    def plot_strategy_trades_notional(self, date = None, strip = None, silent_plot = False):
        self._plot_signal(self._strategy_trade_notional, label = "trades (scaled by notional)", caption = "Trades",
                          date = date, strip = strip, silent_plot=silent_plot)

    def plot_strategy_signals_contracts(self, date = None, strip = None, silent_plot = False):
        self._plot_signal(self._strategy_signal_notional, label = "positions (contracts)", caption = "Positions",
                          date = date, strip = strip, silent_plot=silent_plot)

    def plot_strategy_trades_notional(self, date = None, strip = None, silent_plot = False):
        self._plot_signal(self._strategy_trade_notional, label = "trades (contracts)", caption = "Contracts",
                          date = date, strip = strip, silent_plot=silent_plot)

    def grab_signals(self, strategy_signal, date = None, strip = None):
        if date is None:
            last_day = strategy_signal.ix[-1].transpose().to_frame()
        else:
            if not(isinstance(date, list)):
                date = [date]

            last_day = []

            for d in date:
                last_day.append(strategy_signal.ix[d].transpose().to_frame())

            last_day = pandas.concat(last_day, axis=1)
            last_day = last_day.sort_index(axis=1)

        if strip is not None:
            last_day.index = [x.replace(strip, '') for x in last_day.index]

        return last_day

    def _plot_signal(self, sig, label = ' ', caption = '', date = None, strip = None, silent_plot = False):

        ######## plot signals
        strategy_signal = 100 * (sig)
        last_day = self.grab_signals(strategy_signal, date=date, strip=strip)

        style = self.create_style(label, caption)

        chart = Chart(last_day, engine=self.DEFAULT_PLOT_ENGINE, chart_type='bar', style=style)
        if not (silent_plot): chart.plot()
        return chart

    def create_style(self, title, file_add):
        style = Style()

        style.title = self.FINAL_STRATEGY + " " + title
        style.display_legend = True
        style.scale_factor = self.SCALE_FACTOR
        style.source = self.CHART_SOURCE

        if self.DEFAULT_PLOT_ENGINE not in ['plotly', 'cufflinks'] and self.SAVE_FIGURES:
            style.file_output = self.DUMP_PATH + self.FINAL_STRATEGY + ' (' + file_add + ') ' + str(style.scale_factor) + '.png'

        style.html_file_output = self.DUMP_PATH + self.FINAL_STRATEGY + ' (' + file_add + ') ' + str(style.scale_factor) + '.html'

        try:
            style.silent_display = self.SILENT_DISPLAY
        except: pass

        return style

#######################################################################################################################

"""
RiskEngine

Adjusts signal weighting according to risk constraints (volatility targeting)

"""

class RiskEngine(object):
    def calculate_vol_adjusted_index_from_prices(self, prices_df, br):
        """Adjusts an index of prices for a vol target

        Parameters
        ----------
        br : BacktestRequest
            Parameters for the backtest specifying start date, finish data, transaction costs etc.

        asset_a_df : pandas.DataFrame
            Asset prices to be traded

        Returns
        -------
        pandas.Dataframe containing vol adjusted index
        """

        calculations = Calculations()

        returns_df, leverage_df = self.calculate_vol_adjusted_returns(prices_df, br, returns=False)

        return calculations.create_mult_index(returns_df)

    def calculate_vol_adjusted_returns(self, returns_df, br, returns=True):
        """Adjusts returns for a vol target

        Parameters
        ----------
        br : BacktestRequest
            Parameters for the backtest specifying start date, finish data, transaction costs etc.

        returns_a_df : pandas.DataFrame
            Asset returns to be traded

        Returns
        -------
        pandas.DataFrame
        """

        calculations = Calculations()

        if not returns: returns_df = calculations.calculate_returns(returns_df)

        if not (hasattr(br, 'portfolio_vol_resample_type')):
            br.portfolio_vol_resample_type = 'mean'

        if not (hasattr(br, 'portfolio_vol_resample_freq')):
            br.portfolio_vol_resample_freq = None

        if not (hasattr(br, 'portfolio_vol_period_shift')):
            br.portfolio_vol_period_shift = 0

        leverage_df = self.calculate_leverage_factor(returns_df,
                                                     br.portfolio_vol_target, br.portfolio_vol_max_leverage,
                                                     br.portfolio_vol_periods, br.portfolio_vol_obs_in_year,
                                                     br.portfolio_vol_rebalance_freq, br.portfolio_vol_resample_freq,
                                                     br.portfolio_vol_resample_type,
                                                     period_shift=br.portfolio_vol_period_shift)

        vol_returns_df = calculations.calculate_signal_returns_with_tc_matrix(leverage_df, returns_df, tc=br.spot_tc_bp)
        vol_returns_df.columns = returns_df.columns

        return vol_returns_df, leverage_df

    def calculate_leverage_factor(self, returns_df, vol_target, vol_max_leverage, vol_periods=60, vol_obs_in_year=252,
                                  vol_rebalance_freq='BM', data_resample_freq=None, data_resample_type='mean',
                                  returns=True, period_shift=0):
        """Calculates the time series of leverage for a specified vol target

        Parameters
        ----------
        returns_df : DataFrame
            Asset returns

        vol_target : float
            vol target for assets

        vol_max_leverage : float
            maximum leverage allowed

        vol_periods : int
            number of periods to calculate volatility

        vol_obs_in_year : int
            number of observations in the year

        vol_rebalance_freq : str
            how often to rebalance

        vol_resample_type : str
            do we need to resample the underlying data first? (eg. have we got intraday data?)

        returns : boolean
            is this returns time series or prices?

        period_shift : int
            should we delay the signal by a number of periods?

        Returns
        -------
        pandas.Dataframe
        """

        calculations = Calculations()
        filter = Filter()

        if data_resample_freq is not None:
            return
            # TODO not implemented yet

        if not returns: returns_df = calculations.calculate_returns(returns_df)

        roll_vol_df = calculations.rolling_volatility(returns_df,
                                                      periods=vol_periods, obs_in_year=vol_obs_in_year).shift(
            period_shift)

        # calculate the leverage as function of vol target (with max lev constraint)
        lev_df = vol_target / roll_vol_df
        lev_df[lev_df > vol_max_leverage] = vol_max_leverage

        lev_df = filter.resample_time_series_frequency(lev_df, vol_rebalance_freq, data_resample_type)

        returns_df, lev_df = returns_df.align(lev_df, join='left', axis=0)

        lev_df = lev_df.fillna(method='ffill')
        lev_df.ix[0:vol_periods] = numpy.nan  # ignore the first elements before the vol window kicks in

        return lev_df