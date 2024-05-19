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

import numpy as np
import pandas as pd

from finmarketpy.util.marketconstants import MarketConstants

from findatapy.util import SwimPool
from findatapy.util import LoggerManager

import pickle
# import zlib
# import lz4framed    # conda install -c conda-forge py-lz4framed

from typing import List, Dict

# Make blosc optional (only when trying to run backtests in parallel)
try:
    import blosc
except:
    pass

import pickle

from finmarketpy.backtest.backtestrequest import BacktestRequest

market_constants = MarketConstants()


class Backtest(object):
    """Conducts backtest for strategies trading assets. Assumes we have an
    input of total returns. Reports historical return statistics
    and returns time series.

    """

    def __init__(self):
        self._pnl = None
        self._portfolio = None
        return

    def calculate_diagnostic_trading_PnL(
            self,
            asset_a_df: pd.DataFrame,
            signal_df: pd.DataFrame,
            further_df: pd.DataFrame = [],
            further_df_labels: List[str] = []) -> pd.DataFrame:
        """Calculates P&L table which can be used for debugging purposes.

        The table is populated with asset, signal and further dataframes
        provided by the user, can be used to check signalling methodology.
        It does not apply parameters such as transaction costs, vol adjusment
        and so on.

        Parameters
        ----------
        asset_a_df : DataFrame
            Asset prices

        signal_df : DataFrame
            Trade signals (typically +1, -1, 0 etc)

        further_df : DataFrame
            Further dataframes user wishes to output in the diagnostic output
            (typically inputs for the signals)

        further_df_labels
            Labels to append to the further dataframes

        Returns
        -------
        DataFrame with asset, trading signals and returns of the trading
        strategy for diagnostic purposes

        """
        calculations = Calculations()
        asset_rets_df = calculations.calculate_returns(asset_a_df)
        strategy_rets = calculations.calculate_signal_returns(signal_df,
                                                              asset_rets_df)

        reset_points = ((signal_df - signal_df.shift(1)).abs())

        asset_a_df_entry = asset_a_df.copy(deep=True)
        asset_a_df_entry[reset_points == 0] = np.nan
        asset_a_df_entry = asset_a_df_entry.ffill()

        asset_a_df_entry.columns = [x + '_entry' for x in
                                    asset_a_df_entry.columns]
        asset_rets_df.columns = [x + '_asset_rets' for x in
                                 asset_rets_df.columns]
        strategy_rets.columns = [x + '_strat_rets' for x in
                                 strategy_rets.columns]
        signal_df.columns = [x + '_final_signal' for x in signal_df.columns]

        for i in range(0, len(further_df)):
            further_df[i].columns = [x + '_' + further_df_labels[i] for x in
                                     further_df[i].columns]

        flatten_df = [asset_a_df, asset_a_df_entry, asset_rets_df,
                      strategy_rets, signal_df]

        for f in further_df:
            flatten_df.append(f)

        return calculations.join(flatten_df, how='outer')

    def calculate_trading_PnL(
            self,
            br: BacktestRequest,
            asset_a_df: pd.DataFrame,
            signal_df: pd.DataFrame,
            contract_value_df: pd.DataFrame,
            run_in_parallel: bool = False):
        """Calculates P&L of a trading strategy and statistics to be retrieved
        later

        Calculates the P&L for each asset/signal combination and also for the
        finally strategy applying appropriate weighting in the portfolio,
        depending on predefined parameters, for example:
            static weighting for each asset
            static weighting for each asset + vol weighting for each asset
            static weighting for each asset + vol weighting for each asset + vol weighting for the portfolio

        Parameters
        ----------
        br : BacktestRequest
            Parameters for the backtest specifying start date, finish data, transaction costs etc.

        asset_a_df : pd.DataFrame
            Asset prices to be traded

        signal_df : pd.DataFrame
            Signals for the trading strategy

        contract_value_df : pd.DataFrame
            Daily size of contracts
        """

        calculations = Calculations()
        risk_engine = RiskEngine()

        # # Do an outer join first, so can fill out signal and fill it down
        # # this captures the case where the signal changes on an asset holiday
        # # it will just get delayed till the next tradable day when we do this
        # asset_df_2, signal_df_2 = asset_a_df.align(signal_df, join='outer', axis='index')
        # signal_df = signal_df_2.fillna(method='ffill')
        #
        # # Now make sure the dates of both traded asset and signal are aligned properly
        # # and use as reference only those days where we have asset information
        # asset_df, signal_df = asset_a_df.align(signal_df, join='left', axis = 'index')

        logger = LoggerManager().getLogger(__name__)

        logger.info("Calculating trading P&L...")

        signal_df = signal_df.shift(br.signal_delay)
        asset_df, signal_df = calculations.join_left_fill_right(asset_a_df,
                                                                signal_df)

        if (contract_value_df is not None):
            asset_df, contract_value_df = asset_df.align(contract_value_df,
                                                         join='left',
                                                         axis='index')
            contract_value_df = contract_value_df.fillna(
                method='ffill')  # fill down asset holidays (we won't trade
            # on these days)

        # Non-trading days of the assets (this may of course vary between the
        # assets we are trading
        # if they are from different asset classes)
        non_trading_days = np.isnan(asset_df.values)

        # Only allow signals to change on the days when we can trade assets
        signal_df = signal_df.mask(
            non_trading_days)  # fill asset holidays with NaN signals
        signal_df = signal_df.fillna(method='ffill')  # fill these down

        # Transaction costs and roll costs
        tc = br.spot_tc_bp
        rc = br.spot_rc_bp

        signal_cols = signal_df.columns.values
        asset_df_cols = asset_df.columns.values

        pnl_cols = []

        for i in range(0, len(asset_df_cols)):
            pnl_cols.append(asset_df_cols[i] + " / " + signal_cols[i])

        # Fill down asset holidays (we won't trade on these days)
        asset_df = asset_df.fillna(
            method='ffill')
        returns_df = calculations.calculate_returns(asset_df)

        # Apply a stop loss/take profit to every trade if this has been specified
        # do this before we start to do vol weighting etc.
        if br.take_profit is not None and br.stop_loss is not None:
            returns_df = calculations.calculate_returns(asset_df)

            # Makes assumption that signal column order matches that of returns
            temp_strategy_rets_df = calculations.calculate_signal_returns_as_matrix(
                signal_df, returns_df)

            trade_rets_df = calculations.calculate_cum_rets_trades(signal_df,
                                                                   temp_strategy_rets_df)

            # pre_signal_df = signal_df.copy()

            signal_df = calculations.calculate_risk_stop_signals(signal_df,
                                                                 trade_rets_df,
                                                                 br.stop_loss,
                                                                 br.take_profit)

            # Make sure we can't trade where asset price is undefined and
            # carry over signal
            signal_df = signal_df.mask(
                non_trading_days)  # fill asset holidays with NaN signals
            signal_df = signal_df.fillna(
                method='ffill')  # fill these down (when asset is not trading

            # for debugging purposes
            # if True:
            #     signal_df_copy = signal_df.copy()
            #     trade_rets_df_copy = trade_rets_df.copy()
            #
            #     asset_df_copy.columns = [x + '_asset' for x in temp_strategy_rets_df.columns]
            #     temp_strategy_rets_df.columns = [x + '_strategy_rets' for x in temp_strategy_rets_df.columns]
            #     signal_df_copy.columns = [x + '_final_signal' for x in signal_df_copy.columns]
            #     trade_rets_df_copy.columns = [x + '_cum_trade' for x in trade_rets_df_copy.columns]
            #
            #     to_plot = _calculations.pandas_outer_join([asset_df_copy, pre_signal_df, signal_df_copy, trade_rets_df_copy, temp_strategy_rets_df])
            #     to_plot.to_csv('test.csv')

        if br.portfolio_weight_construction is None:
            pwc = PortfolioWeightConstruction(br=br)
        else:
            pwc = br.portfolio_weight_construction

        # Adjust signal weights and portfolio weights (eg. using various rules, like vol targeting)
        # and also aggregate final portfolio weights
        portfolio_signal_before_weighting, portfolio_signal, portfolio_leverage_df, portfolio, individual_leverage_df, pnl = \
            pwc.optimize_portfolio_weights(returns_df, signal_df, pnl_cols)

        portfolio_total_longs, portfolio_total_shorts, portfolio_net_exposure, portfolio_total_exposure \
            = self.calculate_exposures(portfolio_signal)

        # Apply position limits?
        position_clip_adjustment = risk_engine.calculate_position_clip_adjustment \
            (portfolio_net_exposure, portfolio_total_exposure, br)

        # If we have any position clip adjustment, for example related to max position sizes
        if position_clip_adjustment is not None:
            length_cols = len(signal_df.columns)

            position_clip_adjustment_matrix = np.transpose(
                np.repeat(
                    position_clip_adjustment.values.flatten()[np.newaxis, :],
                    length_cols, 0))

            # Recalculate portfolio signals after adjustment (for individual components - without
            # weighting each signal separately)
            portfolio_signal_before_weighting = pd.DataFrame(
                data=(
                            portfolio_signal_before_weighting.values * position_clip_adjustment_matrix),
                index=portfolio_signal_before_weighting.index,
                columns=portfolio_signal_before_weighting.columns)

            # Recalculate portfolio signal after adjustment (for portfolio
            # level positions)
            portfolio_signal = pd.DataFrame(
                data=(
                            portfolio_signal.values * position_clip_adjustment_matrix),
                index=portfolio_signal.index,
                columns=portfolio_signal.columns)

            # Recalculate portfolio leverage with position constraint
            # (multiply vectors elementwise)
            portfolio_leverage_df = pd.DataFrame(
                data=(
                            portfolio_leverage_df.values * position_clip_adjustment.values),
                index=portfolio_leverage_df.index,
                columns=portfolio_leverage_df.columns)

            # Recalculate total long, short, net and absolute exposures of the
            # whole portfolio after the position
            # clip adjustment
            portfolio_total_longs, portfolio_total_shorts, portfolio_net_exposure, portfolio_total_exposure \
                = self.calculate_exposures(portfolio_signal)

        # Calculate final portfolio returns with the amended portfolio leverage (by default just 1s)
        portfolio = calculations.calculate_signal_returns_with_tc_matrix(
            portfolio_leverage_df, portfolio, tc=tc, rc=rc)

        # Assign all the property variables
        # Trim them if we have asked for a different plot start/finish
        self._signal = self._filter_by_plot_start_finish_date(signal_df,
                                                              br)  # individual signals (before portfolio leverage)
        self._portfolio_signal = self._filter_by_plot_start_finish_date(
            portfolio_signal,
            br)  # individual signals (AFTER portfolio leverage/constraints)
        self._portfolio_leverage = self._filter_by_plot_start_finish_date(
            portfolio_leverage_df, br)  # leverage on portfolio

        self._portfolio = self._filter_by_plot_start_finish_date(portfolio, br)

        # Calculate each period of trades
        self._portfolio_trade = self._portfolio_signal - self._portfolio_signal.shift(
            1)

        # Expressing trades/positions in terms of notionals
        self._portfolio_signal_notional = None
        self._portfolio_signal_trade_notional = None

        # Expressing trades/positions in terms of contracts (useful for futures)
        self._portfolio_signal_contracts = None
        self._portfolio_signal_trade_contracts = None

        self._portfolio_total_longs = self._filter_by_plot_start_finish_date(
            portfolio_total_longs, br)
        self._portfolio_total_shorts = self._filter_by_plot_start_finish_date(
            portfolio_total_shorts, br)
        self._portfolio_net_exposure = self._filter_by_plot_start_finish_date(
            portfolio_net_exposure, br)
        self._portfolio_total_exposure = self._filter_by_plot_start_finish_date(
            portfolio_total_exposure, br)

        self._portfolio_total_longs_notional = None
        self._portfolio_total_shorts_notional = None
        self._portfolio_net_exposure_notional = None
        self._portfolio_total_exposure_notional = None
        self._portfolio_signal_trade_notional_sizes = None

        # Individual signals P&L (before portfolio volatility targeting,
        # position limits etc)
        self._pnl = pnl

        self._individual_leverage = self._filter_by_plot_start_finish_date(
            individual_leverage_df, br)

        # P&L components of individual assets after all the portfolio level
        # risk signals and position limits have been applied
        self._components_pnl = self._filter_by_plot_start_finish_date(
            calculations.calculate_signal_returns_with_tc_matrix(
                portfolio_signal_before_weighting,
                returns_df, tc=tc, rc=rc), br)
        self._components_pnl.columns = pnl_cols

        # TODO FIX very slow - hence only calculate on demand
        # _pnl_trades = _calculations.calculate_individual_trade_gains(signal_df, _pnl)
        self._pnl_trades = None
        self._components_pnl_trades = None

        self._trade_no = None
        self._portfolio_trade_no = None

        self._portfolio.columns = ['Port']

        self._pnl_ret_stats = RetStats(self._pnl, br.ann_factor,
                                       br.resample_ann_factor)
        self._components_pnl_ret_stats = RetStats(self._components_pnl,
                                                  br.ann_factor,
                                                  br.resample_ann_factor)
        self._portfolio_ret_stats = RetStats(self._portfolio, br.ann_factor,
                                             br.resample_ann_factor)

        # Also create other measures of portfolio
        # * portfolio & trades in terms of a predefined notional (in USD)
        # * portfolio & trades in terms of contract sizes (particularly useful for futures)
        if br.portfolio_notional_size is not None:

            # Express positions in terms of the notional size specified
            self._portfolio_signal_notional = self._portfolio_signal * br.portfolio_notional_size
            self._portfolio_signal_trade_notional = self._portfolio_signal_notional \
                                                    - self._portfolio_signal_notional.shift(
                1)

            df_trades_sizes = pd.DataFrame()

            rounded_portfolio_signal_trade_notional = self._portfolio_signal_trade_notional.round(
                2)

            for k in rounded_portfolio_signal_trade_notional.columns:
                df_trades_sizes[k] = pd.value_counts(
                    rounded_portfolio_signal_trade_notional[k], sort=True)

            df_trades_sizes = df_trades_sizes[df_trades_sizes.index != 0]

            self._portfolio_signal_trade_notional_sizes = df_trades_sizes

            self._portfolio_total_longs_notional = portfolio_total_longs * br.portfolio_notional_size
            self._portfolio_total_shorts_notional = portfolio_total_shorts * br.portfolio_notional_size
            self._portfolio_net_exposure_notional = portfolio_net_exposure * br.portfolio_notional_size
            self._portfolio_total_exposure_notional = portfolio_total_exposure * br.portfolio_notional_size

            # Get the positions in terms of the contract sizes
            notional_copy = self._portfolio_signal_notional.copy(deep=True)
            notional_copy_cols = [x.split('.')[0] for x in
                                  notional_copy.columns]
            notional_copy_cols = [x + '.contract-value' for x in
                                  notional_copy_cols]

            notional_copy.columns = notional_copy_cols

            # Can only give contract sizes if these are defined
            if contract_value_df is not None:
                contract_value_df = contract_value_df[notional_copy_cols]
                notional_df, contract_value_df = notional_copy.align(
                    contract_value_df, join='left', axis='index')

                # Careful make sure orders of magnitude are same for the notional and the contract value
                self._portfolio_signal_contracts = notional_df / contract_value_df
                self._portfolio_signal_contracts.columns = self._portfolio_signal_notional.columns
                self._portfolio_signal_trade_contracts = self._portfolio_signal_contracts \
                                                         - self._portfolio_signal_contracts.shift(
                    1)

        # TODO parallel version still work in progress!
        logger.info("Cumulative index calculations")

        if False:  # market_constants.backtest_thread_no[market_constants.generic_plat] > 1 and run_in_parallel:
            swim_pool = SwimPool(
                multiprocessing_library=market_constants.multiprocessing_library)

            pool = swim_pool.create_pool(
                thread_technique=market_constants.backtest_thread_technique,
                thread_no=market_constants.backtest_thread_no[
                    market_constants.generic_plat])

            r1 = pool.apply_async(self._pnl_ret_stats.calculate_ret_stats)
            r2 = pool.apply_async(
                self._components_pnl_ret_stats.calculate_ret_stats)
            r3 = pool.apply_async(
                self._portfolio_ret_stats.calculate_ret_stats)

            resultsA = pool.apply_async(calculations.create_mult_index,
                                        args=(self._pnl,))
            resultsB = pool.apply_async(calculations.create_mult_index,
                                        args=(self._components_pnl,))
            resultsC = pool.apply_async(calculations.create_mult_index,
                                        args=(self._portfolio,))

            swim_pool.close_pool(pool)

            self._pnl_ret_stats = r1.get()
            self._components_pnl_ret_stats = r2.get()
            self._portfolio_ret_stats = r3.get()

            self._pnl_cum = resultsA.get()
            self._components_pnl_cum = resultsB.get()
            self._portfolio_cum = resultsC.get()

        else:
            # Calculate return statistics of the each asset/signal after signal
            # leverage (but before portfolio level constraints)
            # self._ret_stats_pnl.calculate_ret_stats()

            # Calculate return statistics of the each asset/signal after signal
            # leverage AND after portfolio level constraints
            # self._ret_stats_pnl_components.calculate_ret_stats()

            # Calculate return statistics of the final portfolio
            # self._ret_stats_portfolio.calculate_ret_stats()

            # Calculate final portfolio cumulative P&L
            if br.cum_index == 'mult':
                # Calculate individual signals cumulative P&L after signal
                # leverage but before portfolio level constraints
                self._pnl_cum = calculations.create_mult_index(self._pnl)

                # Calculate individual signals cumulative P&L after signal
                # leverage AND after portfolio level constraints
                self._components_pnl_cum = calculations.create_mult_index(
                    self._components_pnl)

                self._portfolio_cum = calculations.create_mult_index(
                    self._portfolio)  # portfolio cumulative P&L

            elif br.cum_index == 'add':
                # Calculate individual signals cumulative P&L after signal leverage but before portfolio level constraints
                self._pnl_cum = calculations.create_add_index(self._pnl)

                # Calculate individual signals cumulative P&L after signal leverage AND after portfolio level constraints
                self._components_pnl_cum = calculations.create_add_index(
                    self._components_pnl)

                self._portfolio_cum = calculations.create_add_index(
                    self._portfolio)  # portfolio cumulative P&L

        logger.info("Completed cumulative index calculations")

        self._pnl_cum.columns = pnl_cols
        self._components_pnl_cum.columns = pnl_cols
        self._portfolio_cum.columns = ['Port']

    def _filter_by_plot_start_finish_date(
            self,
            df: pd.DataFrame,
            br: BacktestRequest) -> pd.DataFrame:

        if br.plot_start is None and br.plot_finish is None:
            return df
        elif df is None:
            return None
        else:
            filter = Filter()
            plot_start = br.start_date;
            plot_finish = br.finish_date

            if br.plot_start is not None:
                plot_start = br.plot_start

            if br.plot_finish is not None:
                plot_finish = br.plot_finish

            return filter.filter_time_series_by_date(plot_start, plot_finish,
                                                     df)

    def calculate_exposures(self,
                            portfolio_signal: pd.DataFrame) -> List[
        pd.DataFrame]:
        """Calculates time series for the total longs, short, net and absolute
        exposure on an aggregated portfolio basis.

        Parameters
        ----------
        portfolio_signal : DataFrame
            Signals for each asset in the portfolio after all weighting,
            portfolio & signal level volatility adjustments

        Returns
        -------
        DataFrame (list)

        """

        # Calculate total portfolio longs/total portfolio shorts/total portfolio exposure
        portfolio_total_longs = pd.DataFrame(
            portfolio_signal[portfolio_signal > 0].sum(axis=1))
        portfolio_total_shorts = pd.DataFrame(
            portfolio_signal[portfolio_signal < 0].sum(axis=1))

        portfolio_total_longs.columns = ['Total Longs']
        portfolio_total_shorts.columns = ['Total Shorts']

        # NOTE: careful usage of signs (portfolio_total_shorts are NEGATIVE)
        portfolio_net_exposure = pd.DataFrame(
            index=portfolio_signal.index, columns=['Net Exposure'],
            data=portfolio_total_longs.values + portfolio_total_shorts.values)

        portfolio_total_exposure = pd.DataFrame(
            index=portfolio_signal.index, columns=['Total Exposure'],
            data=portfolio_total_longs.values - portfolio_total_shorts.values)

        return portfolio_total_longs, portfolio_total_shorts, portfolio_net_exposure, portfolio_total_exposure

    def backtest_output(self):
        return

    ### Get PnL of individual assets before portfolio constraints
    def pnl(self) -> pd.DataFrame:
        """Gets P&L returns of all the individual sub_components of the model (before any portfolio level leverage is applied)

        Returns
        -------
        pd.Dataframe
        """
        return self._pnl

    def trade_no(self) -> pd.DataFrame:
        """Gets number of trades for each signal in the backtest (before

        Returns
        -------
        pd.Dataframe
        """

        if self._trade_no is None:
            calculations = Calculations()
            self._trade_no = calculations.calculate_trade_no(self._signal)

        return self._trade_no

    def pnl_trades(self) -> pd.DataFrame:
        """Gets P&L of each individual trade per signal

        Returns
        -------
        pd.Dataframe
        """

        if self._pnl_trades is None:
            calculations = Calculations()
            self._pnl_trades = calculations.calculate_individual_trade_gains(
                self._signal, self._pnl)

        return self._pnl_trades

    def pnl_desc(self) -> pd.DataFrame:
        """Gets P&L return statistics in a string format

        Returns
        -------
        str
        """
        return self._ret_stats_signals.summary()

    def pnl_ret_stats(self) -> pd.DataFrame:
        """Gets P&L return statistics of individual strategies as class to be queried

        Returns
        -------
        TimeSeriesDesc
        """

        return self._pnl_ret_stats

    def pnl_cum(self) -> pd.DataFrame:
        """Gets P&L as a cumulative time series of individual assets

        Returns
        -------
        pd.DataFrame
        """

        return self._pnl_cum

    ### Get PnL of individual assets AFTER portfolio constraints
    def components_pnl(self) -> pd.DataFrame:
        """Gets P&L returns of all the individual subcomponents of the model (after portfolio level leverage is applied)

        Returns
        -------
        pd.Dataframe
        """
        return self._components_pnl

    def components_pnl_trades(self) -> pd.DataFrame:
        """Gets P&L of each individual trade per signal

        Returns
        -------
        pd.Dataframe
        """

        if self._components_pnl_trades is None:
            calculations = Calculations()
            self._components_pnl_trades = calculations.calculate_individual_trade_gains(
                self._signal,
                self._components_pnl)

        return self._components_pnl_trades

    def components_pnl_desc(self) -> pd.DataFrame:
        """Gets P&L of individual components as return statistics in a string format

        Returns
        -------
        str
        """
        # return self._ret_stats_signals.summary()

    def components_pnl_ret_stats(self) -> pd.DataFrame:
        """Gets P&L return statistics of individual strategies as class to be queried

        Returns
        -------
        TimeSeriesDesc
        """

        return self._components_pnl_ret_stats

    def components_pnl_cum(self) -> pd.DataFrame:
        """Gets P&L as a cumulative time series of individual assets (after portfolio level leverage adjustments)

        Returns
        -------
        pd.DataFrame
        """

        return self._components_pnl_cum

    ### Get PnL of the final portfolio

    def portfolio_cum(self) -> pd.DataFrame:
        """Gets P&L as a cumulative time series of portfolio

        Returns
        -------
        pd.DataFrame
        """

        return self._portfolio_cum

    def portfolio_pnl(self) -> pd.DataFrame:
        """Gets portfolio returns in raw form (ie. not indexed into cumulative form)

        Returns
        -------
        pd.DataFrame
        """

        return self._portfolio

    def portfolio_pnl_desc(self) -> pd.DataFrame:
        """Gets P&L return statistics of portfolio as string

        Returns
        -------
        pd.DataFrame
        """

        return self._portfolio_ret_stats.summary()

    def portfolio_pnl_ret_stats(self) -> pd.DataFrame:
        """Gets P&L return statistics of portfolio as class to be queried

        Returns
        -------
        RetStats
        """

        return self._portfolio_ret_stats

    def individual_leverage(self) -> pd.DataFrame:
        """Gets leverage for each asset historically

        Returns
        -------
        pd.DataFrame
        """

        return self._individual_leverage

    def portfolio_leverage(self) -> pd.DataFrame:
        """Gets the leverage for the portfolio

        Returns
        -------
        pd.DataFrame
        """

        return self._portfolio_leverage

    def portfolio_trade_no(self) -> pd.DataFrame:
        """Gets number of trades for each signal in the backtest (after both signal and portfolio level vol adjustment)

        Returns
        -------
        pd.Dataframe
        """

        if self._portfolio_trade_no is None:
            calculations = Calculations()
            self._portfolio_trade_no = calculations.calculate_trade_no(
                self._portfolio_signal)

        return self._portfolio_trade_no

    def portfolio_signal(self) -> pd.DataFrame:
        """Gets the signals (with individual leverage & portfolio leverage) for each asset, which
        equates to what we would trade in practice

        Returns
        -------
        DataFrame
        """

        return self._portfolio_signal

    def portfolio_total_longs(self) -> pd.DataFrame:
        """Gets the total long exposure in the portfolio

        Returns
        -------
        DataFrame
        """

        return self._portfolio_total_longs

    def portfolio_total_shorts(self) -> pd.DataFrame:
        """Gets the total short exposure in the portfolio

        Returns
        -------
        DataFrame
        """

        return self._portfolio_total_shorts

    def portfolio_net_exposure(self) -> pd.DataFrame:
        """Gets the total net exposure of the portfolio

        Returns
        -------
        DataFrame
        """

        return self._portfolio_net_exposure

    def portfolio_total_exposure(self) -> pd.DataFrame:
        """Gets the total absolute exposure of the portfolio

        Returns
        -------
        DataFrame
        """

        return self._portfolio_total_exposure

    def portfolio_total_longs_notional(self) -> pd.DataFrame:
        """Gets the total long exposure in the portfolio scaled by notional

        Returns
        -------
        DataFrame
        """

        return self._portfolio_total_longs_notional

    def portfolio_total_shorts_notional(self) -> pd.DataFrame:
        """Gets the total short exposure in the portfolio scaled by notional

        Returns
        -------
        DataFrame
        """

        return self._portfolio_total_shorts_notional

    def portfolio_net_exposure_notional(self) -> pd.DataFrame:
        """Gets the total net exposure of the portfolio scaled by notional

        Returns
        -------
        DataFrame
        """

        return self._portfolio_net_exposure_notional

    def portfolio_total_exposure_notional(self) -> pd.DataFrame:
        """Gets the total absolute exposure of the portfolio scaled by notional

        Returns
        -------
        DataFrame
        """

        return self._portfolio_total_exposure_notional

    def portfolio_trade(self) -> pd.DataFrame:
        """Gets the trades (with individual leverage & portfolio leverage) for each asset, which
        we'd need to execute

        Returns
        -------
        DataFrame
        """

        return self._portfolio_trade

    def portfolio_signal_notional(self) -> pd.DataFrame:
        """Gets the signals (with individual leverage & portfolio leverage) for each asset, which
        equates to what we would have a positions in practice, scaled by a notional amount we have already specified

        Returns
        -------
        DataFrame
        """

        return self._portfolio_signal_notional

    def portfolio_trade_notional(self) -> pd.DataFrame:
        """Gets the trades (with individual leverage & portfolio leverage) for each asset, which
        we'd need to execute, scaled by a notional amount we have already specified

        Returns
        -------
        DataFrame
        """

        return self._portfolio_signal_trade_notional

    def portfolio_trade_notional_sizes(self) -> pd.DataFrame:
        """Gets the number of trades (with individual leverage & portfolio leverage) for each asset, which
        we'd need to execute, scaled by a notional amount we have already specified

        Returns
        -------
        DataFrame
        """

        return self._portfolio_signal_trade_notional_sizes

    def portfolio_signal_contracts(self) -> pd.DataFrame:
        """Gets the signals (with individual leverage & portfolio leverage) for each asset, which
        equates to what we would have a positions in practice, scaled by a notional amount and into contract sizes (eg. for futures)
        which we need to specify in another dataframe

        Returns
        -------
        DataFrame
        """

        return self._portfolio_signal_contracts

    def portfolio_trade_contracts(self) -> pd.DataFrame:
        """Gets the trades (with individual leverage & portfolio leverage) for each asset, which
        we'd need to execute, scaled by a notional amount we have already specified and into contract sizes (eg. for futures)
        which we need to specify in another dataframe

        Returns
        -------
        DataFrame
        """

        return self._portfolio_signal_trade_contracts

    def signal(self) -> pd.DataFrame:
        """Gets signal for each asset (with individual leverage, but excluding portfolio leverage constraints) for each asset

        Returns
        -------
        pd.DataFrame
        """

        return self._signal


########################################################################################################################

import abc
import datetime
import copy

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
    SHOW_CHARTS = True
    SHOW_TITLES = True

    DEFAULT_PLOT_ENGINE = ChartConstants().chartfactory_default_engine
    SCALE_FACTOR = ChartConstants().chartfactory_scale_factor
    WIDTH = ChartConstants().chartfactory_width
    HEIGHT = ChartConstants().chartfactory_height
    CHART_SOURCE = ChartConstants().chartfactory_source
    CHART_STYLE = Style()

    DUMP_CSV = ''
    DUMP_PATH = datetime.date.today().strftime("%Y%m%d") + ' '

    # logger = LoggerManager().getLogger(__name__)

    def __init__(self):
        self.br = self.load_parameters()

    # To be implemented by every trading strategy
    @abc.abstractmethod
    def load_parameters(self, br: BacktestRequest = None):
        """Fills parameters for the backtest, such as start-end dates, transaction costs etc. To
        be implemented by subclass. Can overwrite it with our own BacktestRequest.
        """
        return

    @abc.abstractmethod
    def load_assets(self, br=None):
        """Loads time series for the assets to be traded and also for data for generating signals. Can overwrite it
        with our own BacktestRequest.
        """
        return

    @abc.abstractmethod
    def construct_signal(self,
                         spot_df: pd.DataFrame = None,
                         spot_df2: pd.DataFrame = None,
                         tech_params: TechParams = None,
                         br: BacktestRequest = None,
                         run_in_parallel: bool = False) -> pd.DataFrame:
        """Constructs signal from pre-loaded time series

        Parameters
        ----------
        spot_df : pd.DataFrame
            Market time series for generating signals

        spot_df2 : pd.DataFrame
            Market time series for generated signals (can be of different frequency)

        tech_params : TechParams
            Parameters for generating signals

        run_in_parallel : bool
            Allow signal calculation in parallel
        """
        return

    def save_model(self, path):
        """
        Save the model instance as as pickle.

        :param path: path to pickle.
        :return:
        """
        pickle.dump(self, path)

    @staticmethod
    def load_model(path):
        """
        Load the pickle of the saved model.
        :param path: path to pickle.
        :return: TradingModel instance.
        """
        pkl = pickle.load(path)
        return pkl

    ####### Generic functions for every backtest
    def construct_strategy(self, br: BacktestRequest = None, run_in_parallel: bool = False) -> pd.DataFrame:
        """Constructs the returns for all the strategies which have been specified.

        It gets backtesting parameters from fill_backtest_request (although
        these can be overwritten and then market data from fill_assets

        Parameters
        ----------
        br : BacktestRequest
            Parameters which define the backtest (for example start date,
            end date, transaction costs etc.
        """

        logger = LoggerManager().getLogger(__name__)

        # Get the parameters for backtesting
        if br is not None:
            pass
        elif hasattr(self, 'br'):
            br = self.br
        elif br is None:
            br = self.load_parameters()

        # Get market data for backtest (not every load_assets model will take br)
        try:
            market_data = self.load_assets(br=br)
        except:
            market_data = self.load_assets()

        asset_df = None
        spot_df = None
        spot_df2 = None
        basket_dict = {}
        contract_value_df = None

        if isinstance(market_data, tuple) or isinstance(market_data, list):
            asset_df = market_data[0]
            spot_df = market_data[1]
            spot_df2 = market_data[2]
            basket_dict = market_data[3]

            # optional database output

            if len(market_data) == 5:
                contract_value_df = market_data[4]

        elif isinstance(market_data, dict):
            if "asset_df" in market_data:
                asset_df = market_data["asset_df"]

            if "spot_df" in market_data:
                spot_df = market_data["spot_df"]
            else:
                spot_df = market_data["asset_df"]

            if "spot_df2" in market_data:
                spot_df2 = market_data["spot_df2"]

            if "basket_dict" in market_data:
                basket_dict = market_data["basket_dict"]
            else:
                try:
                    final_strategy = self.FINAL_STRATEGY
                except:
                    final_strategy = "Basket"

                tickers = []

                for tick in asset_df.columns:
                    if "." in tick:
                        tick = tick.split(".")[0]

                    basket_dict[tick] = [tick]
                    tickers.append(tick)

                basket_dict[final_strategy] = tickers

            if "contract_value_df" in market_data:
                contract_value_df = market_data["contract_value_df"]

        if hasattr(br, 'tech_params'):
            tech_params = br.tech_params
        else:
            tech_params = TechParams()

        cum_results = pd.DataFrame(index=asset_df.index)
        port_leverage = pd.DataFrame(index=asset_df.index)

        from collections import OrderedDict
        ret_stats_results = OrderedDict()

        bask_results = {}

        bask_keys = basket_dict.keys()

        # Each portfolio key calculate returns - can put parts of the portfolio in the key
        if market_constants.backtest_thread_no[
            market_constants.generic_plat] > 1 and run_in_parallel:
            swim_pool = SwimPool(
                multiprocessing_library=market_constants.multiprocessing_library)

            pool = swim_pool.create_pool(
                thread_technique=market_constants.backtest_thread_technique,
                thread_no=market_constants.backtest_thread_no[
                    market_constants.generic_plat])

            mult_results = []

            # start = asset_df.index[0]
            # finish = asset_df.index[-1]

            # calculate sub substrategies in sub-processes
            # TODO cut up in time chunks
            for key in bask_keys:

                if key != self.FINAL_STRATEGY:
                    logger.info("Calculating (parallel) " + key)

                    asset_cut_df = asset_df[
                        [x + "." + br.trading_field for x in basket_dict[key]]]
                    spot_cut_df = spot_df[
                        [x + "." + br.trading_field for x in basket_dict[key]]]

                    mult_results.append(
                        pool.apply_async(self.construct_individual_strategy,
                                         args=(br, spot_cut_df, spot_df2,
                                               asset_cut_df,
                                               tech_params, key,
                                               contract_value_df,
                                               False, True,))
                    )

                    # Calculate final strategy separately in my main process (so don't have issues with pickling back large output)

            logger.info("Calculating final strategy " + self.FINAL_STRATEGY)

            # Calculate the final strategy separately (can often be a lot larger)
            asset_cut_df = asset_df[[x + "." + br.trading_field for x in
                                     basket_dict[self.FINAL_STRATEGY]]]
            spot_cut_df = spot_df[[x + "." + br.trading_field for x in
                                   basket_dict[self.FINAL_STRATEGY]]]

            desc, results, leverage, stats, key, backtest = \
                self.construct_individual_strategy(br, spot_cut_df, spot_df2,
                                                   asset_cut_df,
                                                   tech_params,
                                                   self.FINAL_STRATEGY,
                                                   contract_value_df, True,
                                                   False)

            results.columns = desc

            cum_results[results.columns[0]] = results
            port_leverage[results.columns[0]] = leverage
            ret_stats_results[key] = stats

            self._assign_final_strategy_results(results, backtest)

            for p in mult_results:

                desc, results, leverage, stats, key, backtest = p.get()

                results.columns = desc

                cum_results[results.columns[0]] = results
                port_leverage[results.columns[0]] = leverage
                ret_stats_results[key] = stats

                if key == self.FINAL_STRATEGY:
                    self._assign_final_strategy_results(results, backtest)

            try:
                swim_pool.close_pool(pool)
            except:
                pass

        else:
            for key in bask_keys:
                logger.info("Calculating (single thread) " + key)

                asset_cut_df = asset_df[
                    [x + "." + br.trading_field for x in basket_dict[key]]]
                spot_cut_df = spot_df[
                    [x + "." + br.trading_field for x in basket_dict[key]]]

                desc, results, leverage, ret_stats, key, backtest = \
                    self.construct_individual_strategy(br, spot_cut_df,
                                                       spot_df2, asset_cut_df,
                                                       tech_params, key,
                                                       contract_value_df,
                                                       False, False)

                # results = backtest.portfolio_cum()
                results.columns = desc

                cum_results[results.columns[0]] = results
                port_leverage[results.columns[0]] = leverage
                ret_stats_results[key] = ret_stats

                if key == self.FINAL_STRATEGY:
                    self._assign_final_strategy_results(results, backtest)

        # Get benchmark for comparison
        benchmark = self.construct_strategy_benchmark()

        cum_results_benchmark = self.compare_strategy_vs_benchmark(br,
                                                                   cum_results,
                                                                   benchmark)

        self._strategy_group_benchmark_pnl_ret_stats = ret_stats_results

        try:
            ret_stats_list = ret_stats_results
            ret_stats_list["Benchmark"] = (
                self._strategy_benchmark_pnl_ret_stats)
            self._strategy_group_benchmark_pnl_ret_stats = ret_stats_list
        except:
            pass

        # Individual parts (all after individually applying portfolio level vol adjustment)
        self._strategy_group_pnl = cum_results
        self._strategy_group_pnl_ret_stats = ret_stats_results

        self._strategy_group_leverage = port_leverage
        self._strategy_group_benchmark_pnl = cum_results_benchmark

    def _assign_final_strategy_results(self,
                                       results: pd.DataFrame,
                                       backtest: Backtest):
        # For a key, designated as the final strategy save that as the "strategy"

        # backtest.pnl_cum()
        # self._strategy_components_pnl_after_portfolio_weights = backtest.components_pnl_cum()
        # self._strategy_components_pnl_ret_stats_after_portfolio_weights = backtest.components_pnl_ret_stats()

        self._strategy_pnl = results  # Cumulative P&L for the final strategy
        self._strategy_components_pnl = backtest.components_pnl_cum()  # P&L of the individual components (after portfolio level vol adjustments)
        self._strategy_components_pnl_ret_stats = backtest.components_pnl_ret_stats().split_into_dict()  # backtest.get_pnl_components_ret_stats()

        self._individual_leverage = backtest.individual_leverage()

        self._strategy_pnl_ret_stats = backtest.portfolio_pnl_ret_stats()
        self._strategy_leverage = backtest.portfolio_leverage()

        # Collect the position sizes and trade sizes (in several different formats)
        self._strategy_signal = backtest.portfolio_signal()
        self._strategy_trade_no = backtest.portfolio_trade_no()
        self._strategy_trade = backtest.portfolio_trade()

        # Scaled by notional
        self._strategy_signal_notional = backtest.portfolio_signal_notional()
        self._strategy_trade_notional = backtest.portfolio_trade_notional()
        self._strategy_trade_notional_sizes = backtest.portfolio_trade_notional_sizes()

        # Scaled by notional and adjusted into contract sizes
        self._strategy_signal_contracts = backtest.portfolio_signal_contracts()
        self._strategy_trade_contracts = backtest.portfolio_trade_contracts()

        # Get PnL by component (before portfolio vol targeting and after)
        self._strategy_group_pnl_trades = backtest.pnl_trades()  # get individual trades P&L before (before portfolio adjustment)
        self._strategy_pnl_trades_components = backtest.components_pnl_trades()

        # Get the total size of longs, short, net exposure and total exposure
        self._strategy_total_longs = backtest.portfolio_total_longs()
        self._strategy_total_shorts = backtest.portfolio_total_shorts()
        self._strategy_net_exposure = backtest.portfolio_net_exposure()
        self._strategy_total_exposure = backtest.portfolio_total_exposure()

        # Get the total notionals of longs, short, net exposure and total exposure
        self._strategy_total_longs_notional = backtest.portfolio_total_longs_notional()
        self._strategy_total_shorts_notional = backtest.portfolio_total_shorts_notional()
        self._strategy_net_exposure_notional = backtest.portfolio_net_exposure_notional()
        self._strategy_total_exposure_notional = backtest.portfolio_total_exposure_notional()

    def construct_individual_strategy(
            self, br: BacktestRequest,
            spot_df: pd.DataFrame,
            spot_df2: pd.DataFrame,
            asset_df: pd.DataFrame,
            tech_params: TechParams,
            key: str,
            contract_value_df: pd.DataFrame,
            run_in_parallel: bool,
            compress_output: bool):
        """Combines the signal with asset returns to find the returns of an individual strategy

        Parameters
        ----------
        br : BacktestRequest
            Parameters for backtest such as start and finish dates

        spot_df : pd.DataFrame
            Market time series for generating signals

        spot_df2 : pd.DataFrame
            Secondary Market time series for generated signals (can be of different frequency)

        tech_params : TechParams
            Parameters for generating signals

        contract_value_df : pd.DataFrame
            Dataframe with the contract sizes for each asset

        Returns
        -------
        portfolio_cum : pd.DataFrame
        backtest : Backtest
        """
        backtest = Backtest()

        logger = LoggerManager().getLogger(__name__)

        logger.info("Calculating trading signals for " + key + "...")

        signal = self.construct_signal(spot_df=spot_df, spot_df2=spot_df2,
                                       tech_params=tech_params, br=br,
                                       run_in_parallel=run_in_parallel)

        logger.info("Calculated trading signals for " + key)

        backtest.calculate_trading_PnL(br, asset_df, signal,
                                       contract_value_df,
                                       run_in_parallel)  # calculate P&L (and adjust signals for vol etc)

        if br.write_csv: backtest.pnl_cum().to_csv(
            self.DUMP_CSV + key + ".csv")

        if br.calc_stats:
            desc = [key + ' ' + str(backtest.portfolio_pnl_desc()[0])]
        else:
            desc = [key]

        # For final strategy return heavyweight backtest object (contains lots of auxilliary information about trades etc)
        if key == self.FINAL_STRATEGY and compress_output:
            logger.debug('Compressing ' + key)

            backtest = blosc.compress(pickle.dumps(backtest))

            logger.debug('Compressed ' + key)

        logger.info('Calculated for ' + key)

        if key != self.FINAL_STRATEGY:
            # return desc, backtest.portfolio_cum(), backtest.portfolio_leverage(), backtest.pnl_ret_stats(), key, None
            return desc, backtest.portfolio_cum(), backtest.portfolio_leverage(), backtest.portfolio_pnl_ret_stats(), key, None

        return desc, backtest.portfolio_cum(), backtest.portfolio_leverage(), backtest.portfolio_pnl_ret_stats(), key, backtest

        # have lightweight output for subcomponents of portfolio
        # return desc, backtest.portfolio_cum(), backtest.portfolio_leverage(), backtest.portfolio_pnl_ret_stats(), \
        #       key, _

    def compare_strategy_vs_benchmark(
            self,
            br: BacktestRequest,
            strategy_df: pd.DataFrame,
            benchmark_df: pd.DataFrame):
        """Compares the trading strategy we are backtesting against a benchmark

        Parameters
        ----------
        br : BacktestRequest
            Parameters for backtest such as start and finish dates
        strategy_df : pd.DataFrame
            Strategy time series
        benchmark_df : pd.DataFrame
            Benchmark time series
        """

        if br.include_benchmark:
            ret_stats = RetStats(br.resample_ann_factor)
            risk_engine = RiskEngine()
            filter = Filter()
            calculations = Calculations()

            # Align strategy time series with that of benchmark
            benchmark_df.columns = [x + ' be' for x in benchmark_df.columns]
            strategy_df, benchmark_df = strategy_df.align(benchmark_df,
                                                          join='left', axis=0)

            # If necessary apply vol target to benchmark (to make it comparable with strategy)
            if br.portfolio_vol_adjust is True:
                benchmark_df = risk_engine.calculate_vol_adjusted_index_from_prices(
                    benchmark_df, br=br)

            # Only calculate return statistics if this has been specified (note when different frequencies of data
            # might underrepresent vol
            # if calc_stats:
            benchmark_df = benchmark_df.fillna(method='ffill')
            benchmark_df = self._filter_by_plot_start_finish_date(benchmark_df,
                                                                  br)

            ret_stats.calculate_ret_stats_from_prices(benchmark_df,
                                                      br.ann_factor)

            if br.calc_stats:
                benchmark_df.columns = ret_stats.summary()

            # Realign strategy & benchmark
            strategy_benchmark_df = strategy_df.join(benchmark_df, how='inner')
            strategy_benchmark_df = strategy_benchmark_df.fillna(
                method='ffill')

            strategy_benchmark_df = self._filter_by_plot_start_finish_date(
                strategy_benchmark_df, br)

            if br.cum_index == 'mult':
                strategy_benchmark_df = calculations.create_mult_index_from_prices(
                    strategy_benchmark_df)
            elif br.cum_index == 'add':
                strategy_benchmark_df = calculations.create_add_index_from_prices(
                    strategy_benchmark_df)

            self._strategy_benchmark_pnl = benchmark_df
            self._strategy_benchmark_pnl_ret_stats = ret_stats

            return strategy_benchmark_df

        return strategy_df

    def _filter_by_plot_start_finish_date(
            self,
            df: pd.DataFrame,
            br: BacktestRequest) -> pd.DataFrame:
        if br.plot_start is None and br.plot_finish is None:
            return df
        else:
            filter = Filter()
            plot_start = br.start_date;
            plot_finish = br.finish_date

            if br.plot_start is not None:
                plot_start = br.plot_start

            if br.plot_finish is not None:
                plot_finish = br.plot_finish

            return filter.filter_time_series_by_date(plot_start, plot_finish,
                                                     df)

    def _flatten_list(self, list_of_lists: List[str]) -> List[str]:
        """Flattens list, particularly useful for combining baskets

        Parameters
        ----------
        list_of_lists : str (list)
            List to be flattened

        Returns
        -------

        """
        result = []

        for i in list_of_lists:
            # only append if i is a basestring (superclass of string)
            if isinstance(i, str):
                result.append(i)
            # otherwise call this function recursively
            else:
                result.extend(self._flatten_list(i))

        return result

    def strategy_name(self) -> str:
        return self.FINAL_STRATEGY

    def individual_leverage(self) -> pd.DataFrame:
        return self._individual_leverage

    def strategy_group_pnl_trades(self) -> pd.DataFrame:
        return self._strategy_group_pnl_trades

    ### components (after signal and portfolio weighting)
    def strategy_components_pnl(self) -> pd.DataFrame:
        return self._strategy_components_pnl

    def strategy_components_pnl_ret_stats(self) -> pd.DataFrame:
        return self._strategy_components_pnl_ret_stats

    ### Final strategy
    def strategy_pnl(self) -> pd.DataFrame:
        return self._strategy_pnl

    def strategy_pnl_ret_stats(self) -> pd.DataFrame:
        return self._strategy_pnl_ret_stats

    def strategy_leverage(self) -> pd.DataFrame:
        return self._strategy_leverage

    ### Final PNL strategy + benchmark
    def strategy_benchmark_pnl(self) -> pd.DataFrame:
        return self._strategy_benchmark_pnl

    def strategy_benchmark_pnl_ret_stats(self) -> pd.DataFrame:
        return self._strategy_benchmark_pnl_ret_stats

    ### Final PNL + group
    def strategy_group_pnl(self) -> pd.DataFrame:
        return self._strategy_group_pnl

    def strategy_group_pnl_ret_stats(self) -> pd.DataFrame:
        return self._strategy_group_pnl_ret_stats

    ### Final P&L + group + benchmark
    def strategy_group_benchmark_pnl(self) -> pd.DataFrame:
        return self._strategy_group_benchmark_pnl

    def strategy_group_benchmark_pnl_ret_stats(self) -> pd.DataFrame:
        return self._strategy_group_benchmark_pnl_ret_stats

    def strategy_group_leverage(self) -> pd.DataFrame:
        return self._strategy_group_leverage

    # Signals
    def strategy_signal(self) -> pd.DataFrame:
        return self._strategy_signal

    def strategy_trade(self) -> pd.DataFrame:
        return self._strategy_trade

    def strategy_signal_notional(self) -> pd.DataFrame:
        return self._strategy_signal_notional

    def strategy_trade_notional(self) -> pd.DataFrame:
        return self._strategy_trade_notional

    def strategy_trade_notional_sizes(self) -> pd.DataFrame:
        return self._strategy_trade_notional_sizes

    def strategy_signal_contracts(self) -> pd.DataFrame:
        return self._strategy_signal_contracts

    def strategy_trade_contracts(self) -> pd.DataFrame:
        return self._strategy_trade_contracts

    def strategy_total_longs(self) -> pd.DataFrame:
        return self._strategy_total_longs

    def strategy_total_shorts(self) -> pd.DataFrame:
        return self._strategy_total_shorts

    def strategy_net_exposure(self) -> pd.DataFrame:
        return self._strategy_net_exposure

    def strategy_total_exposure(self) -> pd.DataFrame:
        return self._strategy_total_exposure

    def strategy_total_longs_notional(self) -> pd.DataFrame:
        return self._strategy_total_longs_notional

    def strategy_total_shorts_notional(self) -> pd.DataFrame:
        return self._strategy_total_shorts_notional

    def strategy_net_exposure_notional(self) -> pd.DataFrame:
        return self._strategy_net_exposure_notional

    def strategy_total_exposure_notional(self) -> pd.DataFrame:
        return self._strategy_total_exposure_notional

    #### Plotting

    #### Plotting

    def _reduce_plot(self,
                     data_frame: pd.DataFrame,
                     reduce_plot: bool = True,
                     resample: str = "B") -> pd.DataFrame:
        """Reduces the frequency of a time series to every business day so it can be plotted more easily

        Parameters
        ----------
        data_frame: pd.DataFrame
            Strategy time series

        Returns
        -------
        pd.DataFrame
        """
        try:
            if reduce_plot and resample is not None:
                # make plots on every business day (will downsample intraday data)
                data_frame = data_frame.resample(resample).last()
                data_frame = data_frame.fillna(method='pad')

            return data_frame
        except:
            return data_frame

    def _chart_return_with_df(
            self,
            df: pd.DataFrame,
            style: Style,
            silent_plot: bool,
            chart_type: str = "line",
            ret_with_df: bool = False,
            split_on_char: str = None):

        if split_on_char is not None:
            d_split = []

            for d in df.columns:
                try:
                    d_split.append(d.split(".")[0])
                except:
                    d_split.append(d)

            df.columns = d_split

        chart = Chart(df, engine=self.DEFAULT_PLOT_ENGINE,
                      chart_type=chart_type, style=style)
        if not (silent_plot): chart.plot()
        if ret_with_df:
            return chart, df

        return chart

        ##### Quick helper functions to plot aspects of the strategy such as P&L, leverage etc.

    def plot_individual_leverage(
            self,
            strip: str = None,
            silent_plot: bool = False,
            reduce_plot: bool = True,
            resample: str = "B",
            ret_with_df: bool = False,
            split_on_char: str = None):

        style = self._create_style("Individual Leverage",
                                   "Individual Leverage",
                                   reduce_plot=reduce_plot)

        try:
            df = self._strip_dataframe(
                self._reduce_plot(self._individual_leverage,
                                  reduce_plot=reduce_plot, resample=resample),
                strip)

            return self._chart_return_with_df(df, style, silent_plot,
                                              chart_type='line',
                                              ret_with_df=ret_with_df,
                                              split_on_char=split_on_char)
        except:
            pass

    def plot_strategy_group_pnl_trades(
            self,
            strip: str = None,
            silent_plot: bool = False,
            reduce_plot: bool = True,
            resample: str = "B",
            ret_with_df: bool = False,
            split_on_char: str = None):

        style = self._create_style("(bp)", "Individual Trade PnL",
                                   reduce_plot=reduce_plot)

        # zero when there isn't a trade exit
        # strategy_pnl_trades = self._strategy_pnl_trades * 100 * 100
        # strategy_pnl_trades = strategy_pnl_trades.dropna()

        # note only works with single large basket trade
        try:
            strategy_pnl_trades = self._strategy_group_pnl_trades.fillna(
                0) * 100 * 100
            df = self._strip_dataframe(self._reduce_plot(
                strategy_pnl_trades, reduce_plot=reduce_plot,
                resample=resample), strip)

            return self._chart_return_with_df(
                df, style, silent_plot, chart_type='line',
                ret_with_df=ret_with_df,
                split_on_char=split_on_char)
        except:
            pass

    def plot_strategy_pnl(
            self,
            strip: str = None,
            silent_plot: bool = False,
            reduce_plot: bool = True,
            resample: str = "B",
            ret_with_df: bool = False,
            split_on_char: str = None):

        style = self._create_style("", "Strategy PnL", reduce_plot=reduce_plot)

        try:
            df = self._strip_dataframe(self._reduce_plot(
                self._strategy_pnl, reduce_plot=reduce_plot,
                resample=resample), strip)

            if hasattr(self, 'br'):
                if self.br.write_csv_pnl:
                    df.to_csv(
                        self.DUMP_PATH + self.FINAL_STRATEGY + "_pnl.csv")

            return self._chart_return_with_df(
                df, style, silent_plot, chart_type="line",
                ret_with_df=ret_with_df,
                split_on_char=split_on_char)
        except Exception as e:
            print(str(e))

    def plot_strategy_trade_no(
            self,
            strip: str = None,
            silent_plot: bool = False,
            reduce_plot: bool = True,
            resample: str = "B",
            ret_with_df: bool = False,
            split_on_char: str = None):
        df_trades = self._strategy_trade_no

        if strip is not None: df_trades.index = [k.replace(strip, '')
                                                 for k in df_trades.index]

        style = self._create_style("", "", reduce_plot=reduce_plot)

        try:
            style.file_output = self.DUMP_PATH + self.FINAL_STRATEGY + " (Strategy trade no).png"
            style.html_file_output = self.DUMP_PATH + self.FINAL_STRATEGY + " (Strategy trade no).html"

            df = self._strip_dataframe(self._reduce_plot(
                df_trades, reduce_plot=reduce_plot, resample=resample), strip)

            return self._chart_return_with_df(
                df, style, silent_plot, chart_type='bar',
                ret_with_df=ret_with_df,
                split_on_char=split_on_char)
        except:
            pass

    def plot_strategy_signal_proportion(
            self,
            strip: str = None,
            silent_plot: bool = False,
            reduce_plot: bool = True,
            resample: str = "B",
            ret_with_df: bool = False,
            split_on_char: str = None):

        signal = self._strategy_signal

        ####### count number of long, short and flat periods in our sample
        long = signal[signal > 0].count()
        short = signal[signal < 0].count()
        flat = signal[signal == 0].count()

        df = pd.DataFrame(index=long.index, columns=['Long', 'Short', 'Flat'])

        df["Long"] = long
        df["Short"] = short
        df["Flat"] = flat

        if strip is not None: df.index = [k.replace(strip, '') for k in
                                          df.index]

        style = self._create_style("", "")

        try:
            style.file_output = self.DUMP_PATH + self.FINAL_STRATEGY + " (Strategy signal proportion).png"
            style.html_file_output = self.DUMP_PATH + self.FINAL_STRATEGY + " (Strategy signal proportion).html"

            df = self._strip_dataframe(
                self._reduce_plot(df), strip, reduce_plot=reduce_plot,
                resample=resample)

            return self._chart_return_with_df(
                df, style, silent_plot, chart_type="bar",
                ret_with_df=ret_with_df,
                split_on_char=split_on_char)
        except:
            pass

    def plot_strategy_leverage(
            self,
            strip: str = None,
            silent_plot: bool = False,
            reduce_plot: bool = True,
            resample: str = "B",
            ret_with_df: bool = False,
            split_on_char: str = None):
        style = self._create_style("Portfolio Leverage", "Strategy Leverage",
                                   reduce_plot=reduce_plot)

        try:
            df = self._strip_dataframe(
                self._reduce_plot(self._strategy_leverage,
                                  reduce_plot=reduce_plot, resample=resample),
                strip)

            return self._chart_return_with_df(df, style, silent_plot,
                                              chart_type='line',
                                              ret_with_df=ret_with_df,
                                              split_on_char=split_on_char)
        except:
            pass

        ##### Plot the individual components cumulative returns and return statistics (including portfolio level constraints)

    def plot_strategy_components_pnl(
            self,
            strip: str = None,
            silent_plot: bool = False,
            reduce_plot: bool = True,
            resample: str = "B",
            ret_with_df: bool = False,
            split_on_char: str = None):

        style = self._create_style("Ind Components", "Strategy PnL Components",
                                   reduce_plot=reduce_plot)

        try:
            df = self._strip_dataframe(
                self._reduce_plot(self._strategy_components_pnl,
                                  reduce_plot=reduce_plot, resample=resample),
                strip)

            return self._chart_return_with_df(df, style, silent_plot,
                                              chart_type='line',
                                              ret_with_df=ret_with_df,
                                              split_on_char=split_on_char)
        except:
            pass

    def plot_strategy_components_pnl_ir(
            self,
            strip: str = None,
            silent_plot: bool = False,
            ret_with_df: bool = False,
            split_on_char: str = None):
        return self._plot_ret_stats_helper(
            self._strategy_components_pnl_ret_stats, 'IR', 'Ind Component',
            'Ind Component IR',
            strip=strip,
            silent_plot=silent_plot, ret_with_df=ret_with_df,
            split_on_char=split_on_char)

    def plot_strategy_components_pnl_returns(
            self,
            strip: str = None,
            silent_plot: bool = False,
            ret_with_df: bool = False,
            split_on_char: str = None):
        return self._plot_ret_stats_helper(
            self._strategy_components_pnl_ret_stats, 'Returns',
            'Ind Component (%)',
            'Ind Component Returns', strip=strip,
            silent_plot=silent_plot, ret_with_df=ret_with_df,
            split_on_char=split_on_char)

    def plot_strategy_components_pnl_vol(
            self,
            strip: str = None,
            silent_plot: bool = False,
            ret_with_df: bool = False,
            split_on_char: str = None):
        return self._plot_ret_stats_helper(
            self._strategy_components_pnl_ret_stats, 'Vol',
            'Ind Component (%)',
            'Ind Component Vol', strip=strip,
            silent_plot=silent_plot, ret_with_df=ret_with_df,
            split_on_char=split_on_char)

    def plot_strategy_components_pnl_drawdowns(
            self,
            strip: str = None,
            silent_plot: bool = False,
            ret_with_df: bool = False,
            split_on_char: str = None):
        return self._plot_ret_stats_helper(
            self._strategy_components_pnl_ret_stats, 'Drawdowns',
            'Ind Component (%)',
            'Ind Component Drawdowns', strip=strip,
            silent_plot=silent_plot, ret_with_df=ret_with_df,
            split_on_char=split_on_char)

    def plot_strategy_components_pnl_yoy(
            self,
            strip: str = None,
            silent_plot: bool = False,
            ret_with_df: bool = False,
            split_on_char: str = None):

        return self.plot_yoy_helper(self._strategy_components_pnl_ret_stats,
                                    'Ind Component YoY', 'Ind Component (%)',
                                    strip=strip, silent_plot=silent_plot,
                                    ret_with_df=ret_with_df,
                                    split_on_char=split_on_char)

        ##### plot the cumulative returns and return statistics for the strategy group
        ##### this will plot the final strategy, benchmark and all the individual baskets (as though they were run by themselves)

    def plot_strategy_group_benchmark_pnl(
            self,
            strip: str = None,
            silent_plot: bool = False,
            reduce_plot: bool = True,
            resample: str = "B",
            ret_with_df: bool = False,
            split_on_char: str = None):
        logger = LoggerManager().getLogger(__name__)

        style = self._create_style("", "Group Benchmark PnL - cumulative")

        strat_list = self._strategy_group_benchmark_pnl.columns  # .sort_values()

        for line in strat_list: logger.info(line)

        # plot cumulative line of returns
        df = self._strip_dataframe(
            self._reduce_plot(self._strategy_group_benchmark_pnl,
                              reduce_plot=reduce_plot, resample=resample),
            strip)

        return self._chart_return_with_df(
            df, style, silent_plot, chart_type="line", ret_with_df=ret_with_df,
            split_on_char=split_on_char)

    def plot_strategy_group_benchmark_pnl_ir(
            self,
            strip: str = None,
            silent_plot: bool = False,
            ret_with_df: bool = False,
            split_on_char: str = None):
        return self._plot_ret_stats_helper(
            self._strategy_group_benchmark_pnl_ret_stats, "IR", "",
            'Group Benchmark IR',
            strip=strip, silent_plot=silent_plot, ret_with_df=ret_with_df,
            split_on_char=split_on_char)

    def plot_strategy_group_benchmark_pnl_returns(
            self,
            strip: str = None,
            silent_plot: bool = False,
            ret_with_df: bool = False,
            split_on_char: str = None):
        return self._plot_ret_stats_helper(
            self._strategy_group_benchmark_pnl_ret_stats, "Returns", '(%)',
            "Group Benchmark Returns",
            strip=strip, silent_plot=silent_plot, ret_with_df=ret_with_df,
            split_on_char=split_on_char)

    def plot_strategy_group_benchmark_pnl_vol(
            self,
            strip: str = None,
            silent_plot: bool = False,
            ret_with_df: bool = False,
            split_on_char: str = None):
        return self._plot_ret_stats_helper(
            self._strategy_group_benchmark_pnl_ret_stats, 'Vol', '(%)',
            'Group Benchmark Vol',
            strip=strip, silent_plot=silent_plot, ret_with_df=ret_with_df,
            split_on_char=split_on_char)

    def plot_strategy_group_benchmark_pnl_drawdowns(
            self,
            strip: str = None,
            silent_plot: bool = False,
            ret_with_df: bool = False,
            split_on_char: str = None):
        return self._plot_ret_stats_helper(
            self._strategy_group_benchmark_pnl_ret_stats, 'Drawdowns', '(%)',
            'Group Benchmark Drawdowns', strip=strip,
            silent_plot=silent_plot, ret_with_df=ret_with_df,
            split_on_char=split_on_char)

    def _plot_ret_stats_helper(self, ret_stats, metric, title, file_tag,
                               strip=None, silent_plot=False,
                               ret_with_df=False, split_on_char=None):
        style = self._create_style(title, file_tag)
        keys = ret_stats.keys()
        ret_metric = []

        for key in keys:
            if metric == "IR":
                ret_metric.append(ret_stats[key].inforatio()[0])
            elif metric == "Returns":
                ret_metric.append(ret_stats[key].ann_returns()[0] * 100)
            elif metric == "Vol":
                ret_metric.append(ret_stats[key].ann_vol()[0] * 100)
            elif metric == "Drawdowns":
                ret_metric.append(ret_stats[key].drawdowns()[0] * 100)

        if strip is not None: keys = [k.replace(strip, '') for k in keys]

        ret_stats = pd.DataFrame(index=keys, data=ret_metric, columns=[metric])
        # ret_stats = ret_stats.sort_index()
        style.file_output = self.DUMP_PATH + self.FINAL_STRATEGY + ' (' + file_tag + ') ' + str(
            style.scale_factor) + '.png'
        style.html_file_output = self.DUMP_PATH + self.FINAL_STRATEGY + ' (' + file_tag + ') ' + str(
            style.scale_factor) + '.html'
        style.display_brand_label = False

        return self._chart_return_with_df(ret_stats, style, silent_plot,
                                          chart_type='bar',
                                          ret_with_df=ret_with_df,
                                          split_on_char=split_on_char)

    def plot_strategy_group_benchmark_pnl_yoy(
            self,
            strip: str = None,
            silent_plot: bool = False,
            ret_with_df: bool = False,
            split_on_char: str = None):

        return self.plot_yoy_helper(
            self._strategy_group_benchmark_pnl_ret_stats, "",
            "Group Benchmark PnL YoY",
            strip=strip,
            silent_plot=silent_plot, ret_with_df=ret_with_df,
            split_on_char=split_on_char)

    def plot_yoy_helper(
            self,
            ret_stats: dict,
            title: str,
            file_tag: str,
            strip: str = None,
            silent_plot: bool = False,
            ret_with_df: bool = False,
            split_on_char: str = None):

        style = self._create_style(title, title)
        # keys = self._strategy_group_benchmark_ret_stats.keys()
        yoy = []

        for key in ret_stats.keys():
            col = ret_stats[key].yoy_rets()
            col.columns = [key]
            yoy.append(col)

        calculations = Calculations()
        ret_stats = calculations.join(yoy, how='outer')
        ret_stats.index = ret_stats.index.year

        ret_stats = self._strip_dataframe(ret_stats, strip)

        # ret_stats = ret_stats.sort_index()
        style.file_output = self.DUMP_PATH + self.FINAL_STRATEGY + ' (' + file_tag + ') ' \
                            + str(style.scale_factor) + '.png'
        style.html_file_output = self.DUMP_PATH + self.FINAL_STRATEGY + ' (' + file_tag + ') ' \
                                 + str(style.scale_factor) + '.html'
        style.display_brand_label = False
        style.date_formatter = "%Y"

        ret_stats = ret_stats * 100

        return self._chart_return_with_df(ret_stats, style, silent_plot,
                                          chart_type='line',
                                          ret_with_df=ret_with_df,
                                          split_on_char=split_on_char)

    def plot_strategy_group_leverage(
            self,
            silent_plot: bool = False,
            reduce_plot: bool = True,
            resample: str = "B",
            ret_with_df: bool = False,
            split_on_char: str = None):

        style = self._create_style("Leverage", "Group Leverage",
                                   reduce_plot=reduce_plot)

        df = self._reduce_plot(self._strategy_group_leverage,
                               reduce_plot=reduce_plot, resample=resample)

        return self._chart_return_with_df(df, style, silent_plot,
                                          chart_type='line',
                                          ret_with_df=ret_with_df,
                                          split_on_char=split_on_char)

    ###### Plot signals and trades, in terms of units, notionals and contract sizes (eg. for futures)

    def plot_strategy_all_signals(
            self,
            signal_show: str = None,
            strip: str = None,
            silent_plot: bool = False,
            reduce_plot: bool = True,
            resample: str = "B",
            ret_with_df: bool = False,
            split_on_char: str = None,
            multiplier: int = 100):

        style = self._create_style("positions (% portfolio notional)",
                                   "Positions", reduce_plot=reduce_plot)

        df = self._strategy_signal.copy() * multiplier

        if signal_show is not None:

            if signal_show != []:
                not_found = []

                if split_on_char is not None:
                    for d in df.columns:
                        d_split = d.split(split_on_char)[0]

                        if d_split not in signal_show:
                            not_found.append(d)

                    df = df.drop(not_found, axis=1)

        try:
            df = self._strip_dataframe(
                self._reduce_plot(df, reduce_plot=reduce_plot,
                                  resample=resample), strip)
            return self._chart_return_with_df(df, style, silent_plot,
                                              chart_type='line',
                                              ret_with_df=ret_with_df)
        except:
            pass

    def plot_strategy_signals(
            self,
            date: str = None,
            strip: str = None,
            silent_plot: bool = False,
            strip_times: bool = False,
            ret_with_df: bool = False,
            split_on_char: str = None,
            multiplier: int = 100):
        return self._plot_signal(self._strategy_signal,
                                 label="positions (% portfolio notional)",
                                 caption="Positions",
                                 date=date, strip=strip,
                                 silent_plot=silent_plot,
                                 strip_times=strip_times,
                                 ret_with_df=ret_with_df,
                                 split_on_char=split_on_char,
                                 multiplier=multiplier)

    def plot_strategy_trades(
            self,
            date: str = None,
            strip: str = None,
            silent_plot: bool = False,
            strip_times: bool = False,
            ret_with_df: bool = False,
            split_on_char: str = None,
            multiplier: int = 100):
        return self._plot_signal(self._strategy_trade,
                                 label="trades (% portfolio notional)",
                                 caption="Trades",
                                 date=date, strip=strip,
                                 silent_plot=silent_plot,
                                 strip_times=strip_times,
                                 ret_with_df=ret_with_df,
                                 split_on_char=split_on_char,
                                 multiplier=multiplier)

    def plot_strategy_signals_notional(
            self,
            date: str = None,
            strip: str = None,
            silent_plot: bool = False,
            strip_times: bool = False,
            ret_with_df: bool = False,
            split_on_char: str = None,
            multiplier: int = 1):

        return self._plot_signal(
            self._strategy_signal_notional,
            label="positions (scaled by notional)",
            caption="Positions",
            date=date, strip=strip, silent_plot=silent_plot,
            strip_times=strip_times,
            ret_with_df=ret_with_df,
            split_on_char=split_on_char,
            multiplier=multiplier)

    def plot_strategy_trades_notional(
            self,
            date: str = None,
            strip: str = None,
            silent_plot: bool = False,
            strip_times: bool = False,
            split_on_char: str = None,
            multiplier: int = 1):

        return self._plot_signal(
            self._strategy_trade_notional, label="trades (scaled by notional)",
            caption="Trades",
            date=date, strip=strip, silent_plot=silent_plot,
            strip_times=strip_times,
            split_on_char=split_on_char, multiplier=multiplier)

    def plot_strategy_trades_notional_sizes(
            self,
            strip: str = None,
            silent_plot: bool = False,
            ret_with_df: bool = False,
            split_on_char: str = None):

        if strip is not None: self._strategy_trade_notional_sizes.index = [
            k.replace(strip, '')
            for k in
            self._strategy_trade_notional_sizes.index]

        style = self._create_style("", "", reduce_plot=False)

        try:
            style.file_output = self.DUMP_PATH + self.FINAL_STRATEGY + " (Strategy trade notional size).png"
            style.html_file_output = self.DUMP_PATH + self.FINAL_STRATEGY + " (Strategy trade notional size).html"

            df = self._strip_dataframe(self._strategy_trade_notional_sizes,
                                       strip)

            return self._chart_return_with_df(df, style, silent_plot,
                                              chart_type='bar',
                                              ret_with_df=ret_with_df,
                                              split_on_char=split_on_char)
        except:
            pass

    def plot_strategy_signals_contracts(
            self,
            date: str = None,
            strip: str = None,
            silent_plot: bool = False,
            strip_times: bool = False,
            ret_with_df: bool = False,
            split_on_char: str = None,
            multiplier: int = 1):
        return self._plot_signal(self._strategy_signal_contracts,
                                 label="positions (contracts)",
                                 caption="Positions",
                                 date=date, strip=strip,
                                 silent_plot=silent_plot,
                                 strip_times=strip_times,
                                 ret_with_df=ret_with_df,
                                 split_on_char=split_on_char,
                                 multiplier=multiplier)

    def plot_strategy_trades_contracts(
            self,
            date: str = None,
            strip: str = None,
            silent_plot: bool = False,
            strip_times: bool = False,
            ret_with_df: bool = False,
            split_on_char: str = None,
            multiplier: int = 1):
        return self._plot_signal(self._strategy_trade_contracts,
                                 label="trades (contracts)",
                                 caption="Contracts",
                                 date=date, strip=strip,
                                 silent_plot=silent_plot,
                                 strip_times=strip_times,
                                 ret_with_df=ret_with_df,
                                 split_on_char=split_on_char,
                                 multiplier=multiplier)

        ###### plot aggregated portfolio exposures

    def plot_strategy_total_exposures(
            self,
            strip: str = None,
            silent_plot: bool = False,
            reduce_plot: bool = True,
            resample: str = "B",
            ret_with_df: bool = False,
            split_on_char: str = None):

        style = self._create_style("", "Strategy Total Exposures")
        df = pd.concat(
            [self._strategy_total_longs, self._strategy_total_shorts,
             self._strategy_total_exposure],
            axis=1)

        try:
            df = self._strip_dataframe(
                self._reduce_plot(df, reduce_plot=reduce_plot,
                                  resample=resample), strip)
            return self._chart_return_with_df(df, style, silent_plot,
                                              chart_type='line',
                                              ret_with_df=ret_with_df,
                                              split_on_char=split_on_char)
        except:
            pass

    def plot_strategy_net_exposures(
            self,
            strip: str = None,
            silent_plot: bool = False,
            reduce_plot: bool = True,
            resample: str = "B",
            ret_with_df: bool = False,
            split_on_char: str = None):
        style = self._create_style("", "Strategy Net Exposures",
                                   reduce_plot=reduce_plot)

        try:
            df = self._strip_dataframe(
                self._reduce_plot(self._strategy_net_exposure,
                                  reduce_plot=reduce_plot, resample=resample),
                strip)
            return self._chart_return_with_df(df, style, silent_plot,
                                              chart_type='line',
                                              ret_with_df=ret_with_df,
                                              split_on_char=split_on_char)
        except:
            pass

    def plot_strategy_total_exposures_notional(
            self,
            strip: str = None,
            silent_plot: bool = False,
            reduce_plot: bool = True,
            resample: str = "B",
            ret_with_df: bool = False,
            split_on_char: str = None):

        style = self._create_style("(mm)", "Strategy Total Exposures (mm)",
                                   reduce_plot=reduce_plot)
        df = pd.concat([self._strategy_total_longs_notional,
                        self._strategy_total_shorts_notional,
                        self._strategy_total_exposure_notional], axis=1)

        try:
            df = self._strip_dataframe(
                self._reduce_plot(df / 1000000.0, reduce_plot=reduce_plot,
                                  resample=resample),
                strip)
            return self._chart_return_with_df(df, style, silent_plot,
                                              chart_type='line',
                                              ret_with_df=ret_with_df,
                                              split_on_char=split_on_char)
        except:
            pass

    def plot_strategy_net_exposures_notional(
            self,
            strip: str = None,
            silent_plot: bool = False,
            reduce_plot: bool = True,
            resample: str = "B",
            ret_with_df: bool = False,
            split_on_char: str = None):

        style = self._create_style("(mm)", "Strategy Net Exposures (mm)",
                                   reduce_plot=reduce_plot)

        try:
            df = self._strip_dataframe(self._reduce_plot(
                self._strategy_net_exposure_notional / 1000000.0,
                reduce_plot=reduce_plot, resample=resample), strip)
            return self._chart_return_with_df(df, style, silent_plot,
                                              chart_type='line',
                                              ret_with_df=ret_with_df,
                                              split_on_char=split_on_char)
        except:
            pass

        #### Grab signals for specific days

    def _grab_signals(self, strategy_signal, date=None, strip=None):
        if date is None:
            last_day = strategy_signal.iloc[-1].transpose().to_frame()
        else:
            if not (isinstance(date, list)):
                date = [date]

            last_day = []

            # In case our history is not long enough
            for d in date:
                try:
                    last_day.append(
                        strategy_signal.iloc[d].transpose().to_frame())
                except:
                    pass

            last_day = pd.concat(last_day, axis=1)
            last_day = last_day.sort_index(axis=1)

        if strip is not None:
            last_day.index = [x.replace(strip, '') for x in last_day.index]

        return last_day

    def _plot_signal(self, sig, label=' ', caption='', date=None, strip=None,
                     silent_plot=False, strip_times=False,
                     ret_with_df=False, split_on_char=None, multiplier=100):

        ######## Plot signals

        strategy_signal = multiplier * (sig)
        last_day = self._grab_signals(strategy_signal, date=date, strip=strip)

        style = self._create_style(label, caption)

        # style.legend_x_pos = 1
        style.legend_y_anchor = 'top'

        if strip_times:
            try:
                last_day.index = [x.date() for x in last_day.index]
            except:
                pass

            try:
                last_day.columns = [x.date() for x in last_day.columns]
            except:
                pass

        return self._chart_return_with_df(last_day, style, silent_plot,
                                          chart_type='bar',
                                          ret_with_df=ret_with_df,
                                          split_on_char=split_on_char)

    def _strip_dataframe(self, data_frame, strip):
        if strip is None:
            return data_frame

        if not (isinstance(strip, list)):
            strip = [strip]

        for s in strip:
            if s == '.':
                data_frame.columns = [x.split(s)[0] if s in x else x for x in
                                      data_frame.columns]
            else:
                data_frame.columns = [x.replace(s, '') if s in x else x for x
                                      in data_frame.columns]

        return data_frame

    def _create_style(self, title, file_add, reduce_plot=True):
        style = copy.deepcopy(self.CHART_STYLE)

        if self.SHOW_TITLES:
            style.title = self.FINAL_STRATEGY + " " + title

        style.display_legend = True
        style.scale_factor = self.SCALE_FACTOR
        style.width = self.WIDTH
        style.height = self.HEIGHT
        style.source = self.CHART_SOURCE
        style.silent_display = not (self.SHOW_CHARTS)

        style.legend_bgcolor = 'rgba(0,0,0,0)'

        # When plotting many points use WebGl version of plotly if specified
        if not (reduce_plot):
            style.plotly_webgl = True

        if self.DEFAULT_PLOT_ENGINE not in ['plotly',
                                            'cufflinks'] and self.SAVE_FIGURES:
            style.file_output = self.DUMP_PATH + self.FINAL_STRATEGY + ' (' + file_add + ') ' \
                                + str(style.scale_factor) + '.png'

        style.html_file_output = self.DUMP_PATH + self.FINAL_STRATEGY + ' (' + file_add + ') ' \
                                 + str(style.scale_factor) + '.html'

        try:
            style.silent_display = self.SILENT_DISPLAY
        except:
            pass

        return style


#######################################################################################################################

class PortfolioWeightConstruction(object):
    """Creates dynamics weights for signals and also the portfolio

    """

    def __init__(self, br=None):
        self._br = br
        self._risk_engine = RiskEngine()
        self._calculations = Calculations()

    def optimize_portfolio_weights(
            self,
            returns_df: pd.DataFrame,
            signal_df: pd.DataFrame,
            signal_pnl_cols: List[str],
            br: BacktestRequest = None) -> (
    pd.DataFrame, pd.DataFrame, pd.DataFrame,
    pd.DataFrame, pd.DataFrame, pd.DataFrame):

        if br is None:
            br = self._br

        tc = br.spot_tc_bp
        rc = br.spot_rc_bp

        individual_leverage_df = None

        # Do we have a vol target for individual signals?
        if br.signal_vol_adjust is True:
            leverage_df = self._risk_engine.calculate_leverage_factor(
                returns_df,
                br.signal_vol_target,
                br.signal_vol_max_leverage,
                br.signal_vol_periods, br.signal_vol_obs_in_year,
                br.signal_vol_rebalance_freq,
                br.signal_vol_resample_freq,
                br.signal_vol_resample_type,
                period_shift=br.signal_vol_period_shift)

            signal_df = pd.DataFrame(
                signal_df.values * leverage_df.values,
                index=signal_df.index, columns=signal_df.columns)

            individual_leverage_df = leverage_df  # Contains leverage of individual signal (before portfolio vol target)

        signal_pnl = self._calculations.calculate_signal_returns_with_tc_matrix(
            signal_df, returns_df, tc=tc, rc=rc)
        signal_pnl.columns = signal_pnl_cols

        adjusted_weights_matrix = None

        # Portfolio is average of the underlying signals: should we sum them or average them or use another
        # weighting scheme?
        if br.portfolio_combination is not None:
            if br.portfolio_combination == "sum" and br.portfolio_combination_weights is None:
                portfolio = pd.DataFrame(data=signal_pnl.sum(axis=1),
                                         index=signal_pnl.index,
                                         columns=["Portfolio"])
            elif br.portfolio_combination == "mean" and br.portfolio_combination_weights is None:
                portfolio = pd.DataFrame(data=signal_pnl.mean(axis=1),
                                         index=signal_pnl.index,
                                         columns=["Portfolio"])

                adjusted_weights_matrix = self.calculate_signal_weights_for_portfolio(
                    br, signal_pnl, method="mean")
            elif "weighted" in br.portfolio_combination and isinstance(
                    br.portfolio_combination_weights, dict):

                # Get the weights for each asset
                adjusted_weights_matrix = self.calculate_signal_weights_for_portfolio(
                    br, signal_pnl, method=br.portfolio_combination)

                portfolio = pd.DataFrame(
                    data=(signal_pnl.values * adjusted_weights_matrix),
                    index=signal_pnl.index)
                is_all_na = pd.isnull(portfolio).all(axis=1)
                portfolio = pd.DataFrame(portfolio.sum(axis=1),
                                         columns=["Portfolio"])

                # Overwrite days when every asset PnL was null is NaN with nan
                portfolio[is_all_na] = np.nan
        else:
            # Just assume to take the mean / ie. equal weights for each signal
            portfolio = pd.DataFrame(data=signal_pnl.mean(axis=1),
                                     index=signal_pnl.index,
                                     columns=["Portfolio"])

            adjusted_weights_matrix = self.calculate_signal_weights_for_portfolio(
                br, signal_pnl, method="mean")

        portfolio_leverage_df = pd.DataFrame(
            data=np.ones(len(signal_pnl.index)), index=signal_pnl.index,
            columns=["Portfolio"])

        # Should we apply vol target on a portfolio level basis?
        if br.portfolio_vol_adjust is True:
            # Calculate portfolio leverage
            portfolio_leverage_df = self._risk_engine.calculate_leverage_factor(
                portfolio,
                br.portfolio_vol_target,
                br.portfolio_vol_max_leverage,
                br.portfolio_vol_periods,
                br.portfolio_vol_obs_in_year,
                br.portfolio_vol_rebalance_freq,
                br.portfolio_vol_resample_freq,
                br.portfolio_vol_resample_type,
                period_shift=br.portfolio_vol_period_shift)

            # portfolio, portfolio_leverage_df = risk_engine.calculate_vol_adjusted_returns(portfolio, br = br)

        # Multiply portfolio leverage * individual signals to get final position signals
        length_cols = len(signal_df.columns)
        leverage_matrix = np.transpose(
            np.repeat(portfolio_leverage_df.values.flatten()[np.newaxis, :],
                      length_cols, 0))

        # Final portfolio signals (including signal & portfolio leverage)
        portfolio_signal = pd.DataFrame(
            data=np.multiply(leverage_matrix, signal_df.values),
            index=signal_df.index, columns=signal_df.columns)

        # Later, when we plot the portfolio components, we do that without weighting the individual components
        portfolio_signal_before_weighting = portfolio_signal.copy()

        if br.portfolio_combination is not None:
            if 'sum' in br.portfolio_combination:
                pass
            elif br.portfolio_combination == 'mean' \
                    or (br.portfolio_combination == 'weighted' and isinstance(
                br.portfolio_combination_weights, dict)):
                portfolio_signal = pd.DataFrame(
                    data=(portfolio_signal.values * adjusted_weights_matrix),
                    index=portfolio_signal.index,
                    columns=portfolio_signal.columns)
        else:
            # Otherwise it's "mean"
            portfolio_signal = pd.DataFrame(
                data=(portfolio_signal.values * adjusted_weights_matrix),
                index=portfolio_signal.index,
                columns=portfolio_signal.columns)

        return portfolio_signal_before_weighting, portfolio_signal, portfolio_leverage_df, portfolio, individual_leverage_df, signal_pnl

    def calculate_signal_weights_for_portfolio(
            self,
            br: Backtest,
            signal_pnl: pd.DataFrame,
            method: str = "mean") -> pd.DataFrame:
        """Calculates the weights of each signal for the portfolio

        Parameters
        ----------
        br : BacktestRequest
            Parameters for the backtest specifying start date, finish data,
            transaction costs etc.

        signal_pnl : pd.DataFrame
            Contains the daily P&L for the portfolio

        method : String
            "mean" - assumes equal weighting for each signal
            "weighted" - can use predefined user weights (eg. if we assign
            weighting of 1, 1, 0.5, for three signals the third signal will
            have a weighting of half versus the others)

        weights : dict
            Portfolio weights

        Returns
        -------
        pd.DataFrame
            Contains the portfolio weights
        """

        if method == "mean":
            weights_vector = np.ones(len(signal_pnl.columns))
        elif method == "weighted" or "weighted-sum":
            # Get the weights for each asset
            weights_vector = np.array(
                [float(br.portfolio_combination_weights[col]) for col in
                 signal_pnl.columns])

        # Repeat this down for every day
        weights_matrix = np.repeat(weights_vector[np.newaxis, :],
                                   len(signal_pnl.index), 0)

        # Where we don't have old price data, make the weights 0 there
        ind = np.isnan(signal_pnl.values)
        weights_matrix[ind] = 0

        if method != "weighted-sum":
            # The total weights will vary, as historically might not have all the assets trading
            total_weights = np.sum(weights_matrix, axis=1)

            # Replicate across columns
            total_weights = np.transpose(
                np.repeat(total_weights[np.newaxis, :],
                          len(signal_pnl.columns), 0))

            # To avoid divide by zero
            total_weights[total_weights == 0.0] = 1.0

            adjusted_weights_matrix = weights_matrix / total_weights
            adjusted_weights_matrix[ind] = np.nan

            return adjusted_weights_matrix

        return weights_matrix


#######################################################################################################################

class RiskEngine(object):
    """Adjusts signal weighting according to risk constraints (volatility
    targeting and position limit constraints)

    """

    def calculate_vol_adjusted_index_from_prices(
            self,
            prices_df: pd.DataFrame,
            br: BacktestRequest) -> pd.DataFrame:
        """Adjusts an index of prices for a vol target

        Parameters
        ----------
        br : BacktestRequest
            Parameters for the backtest specifying start date, finish data,
            transaction costs etc.
        asset_a_df : pd.DataFrame
            Asset prices to be traded

        Returns
        -------
        pd.Dataframe containing vol adjusted index
        """

        calculations = Calculations()

        returns_df, leverage_df = self.calculate_vol_adjusted_returns(
            prices_df, br, returns=False)

        if br.cum_index == 'mult':
            return calculations.create_mult_index(returns_df)
        elif br.cum_index == 'add':
            return calculations.create_add_index(returns_df)

    def calculate_vol_adjusted_returns(
            self,
            returns_df: pd.DataFrame,
            br: BacktestRequest,
            returns: bool = True) -> (pd.DataFrame, pd.DataFrame):
        """Adjusts returns for a vol target

        Parameters
        ----------
        br : BacktestRequest
            Parameters for the backtest specifying start date, finish data,
            transaction costs etc.
        returns_a_df : pd.DataFrame
            Asset returns to be traded

        Returns
        -------
        pd.DataFrame
        """

        calculations = Calculations()

        if not returns: returns_df = calculations.calculate_returns(returns_df)

        leverage_df = self.calculate_leverage_factor(returns_df,
                                                     br.portfolio_vol_target,
                                                     br.portfolio_vol_max_leverage,
                                                     br.portfolio_vol_periods,
                                                     br.portfolio_vol_obs_in_year,
                                                     br.portfolio_vol_rebalance_freq,
                                                     br.portfolio_vol_resample_freq,
                                                     br.portfolio_vol_resample_type,
                                                     period_shift=br.portfolio_vol_period_shift)

        vol_returns_df = calculations.calculate_signal_returns_with_tc_matrix(
            leverage_df, returns_df, tc=br.spot_tc_bp)
        vol_returns_df.columns = returns_df.columns

        return vol_returns_df, leverage_df

    def calculate_leverage_factor(
            self,
            returns_df: pd.DataFrame,
            vol_target: float,
            vol_max_leverage: float,
            vol_periods: int = 60,
            vol_obs_in_year: int = 252,
            vol_rebalance_freq: str = "BM",
            resample_freq: str = None,
            resample_type: str = "mean",
            returns: bool = True,
            period_shift: int = 0) -> pd.DataFrame:
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
        resample_type : str
            do we need to resample the underlying data first? (eg. have we got intraday data?)
        returns : boolean
            is this returns time series or prices?
        period_shift : int
            should we delay the signal by a number of periods?

        Returns
        -------
        pd.Dataframe
        """

        calculations = Calculations()
        filter = Filter()

        if resample_freq is not None:
            return
            # TODO not implemented yet

        if not returns: returns_df = calculations.calculate_returns(returns_df)

        roll_vol_df = calculations.rolling_volatility(returns_df,
                                                      periods=vol_periods,
                                                      obs_in_year=vol_obs_in_year).shift(
            period_shift)

        # calculate the leverage as function of vol target (with max lev constraint)
        lev_df = vol_target / roll_vol_df

        if vol_max_leverage is not None:
            lev_df[lev_df > vol_max_leverage] = vol_max_leverage

        if resample_type is not None:
            lev_df = filter.resample_time_series_frequency(lev_df,
                                                           vol_rebalance_freq,
                                                           resample_type)

            returns_df, lev_df = calculations.join_left_fill_right(returns_df,
                                                                   lev_df)

        # # in case leverage changes on a weekend do outer join, and fill down
        # # the leverage
        # returns_df_1, lev_df = returns_df.align(lev_df, join='outer', axis=0)
        # lev_df = lev_df.fillna(method='ffill')
        #
        # # now realign back to days when we trade
        # returns_df, lev_df = returns_df.align(lev_df, join='left', axis=0)

        lev_df[
        0:vol_periods] = np.nan  # ignore the first elements before the vol window kicks in

        return lev_df

    def calculate_position_clip_adjustment(
            self,
            portfolio_net_exposure: pd.DataFrame,
            portfolio_total_exposure: pd.DataFrame,
            br) -> pd.DataFrame:
        """Calculate the leverage adjustment that needs to be made in the portfolio such that either the net exposure or
        the absolute exposure fits within predefined limits

        Parameters
        ----------
        portfolio_net_exposure : DataFrame
            Net exposure of the whole portfolio
        portfolio_total_exposure : DataFrame
            Absolute exposure of the whole portfolio
        br : BacktestRequest
            Includes parameters for setting position limits

        Returns
        -------
        DataFrame
        """

        position_clip_adjustment = None

        # Adjust leverage of portfolio based on max NET position sizes
        if br.max_net_exposure is not None:
            portfolio_net_exposure = portfolio_net_exposure.shift(
                br.position_clip_period_shift)

            # add further constraints on portfolio (total net amount of longs and short)
            position_clip_adjustment = pd.DataFrame(
                data=np.ones(len(portfolio_net_exposure.index)),
                index=portfolio_net_exposure.index,
                columns=['Portfolio'])

            portfolio_abs_exposure = portfolio_net_exposure.abs()

            # For those periods when the absolute net positioning is greater
            # than our limit cut down the leverage
            position_clip_adjustment[
                (portfolio_abs_exposure > br.max_net_exposure).values] = \
                br.max_net_exposure / portfolio_abs_exposure

        # Adjust leverage of portfolio based on max TOTAL position sizes
        if br.max_abs_exposure is not None:
            portfolio_abs_exposure = portfolio_abs_exposure.shift(
                br.position_clip_period_shift)

            # add further constraints on portfolio (total net amount of
            # longs and short)
            position_clip_adjustment = pd.DataFrame(
                data=np.ones(len(portfolio_abs_exposure.index)),
                index=portfolio_abs_exposure.index,
                columns=['Portfolio'])

            # For those periods when the absolute TOTAL positioning is
            # greater than our limit cut down the leverage
            position_clip_adjustment[
                (portfolio_total_exposure > br.max_abs_exposure).values] = \
                br.max_abs_exposure / portfolio_total_exposure

        # Only allow the position clip adjustment to change on certain
        # days (eg. 'BM' = month end)
        if br.position_clip_rebalance_freq is not None:
            calculations = Calculations()
            filter = Filter()

            position_clip_adjustment = filter.resample_time_series_frequency(
                position_clip_adjustment,
                br.position_clip_rebalance_freq,
                br.position_clip_resample_type)

            a, position_clip_adjustment = calculations.join_left_fill_right(
                portfolio_net_exposure,
                position_clip_adjustment)

        return position_clip_adjustment
