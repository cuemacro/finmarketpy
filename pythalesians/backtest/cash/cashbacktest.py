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
CashBacktest

Conducts backtest for strategies trading cash based assets. Reports historical return statistics
and returns time series.

"""

import pandas
import numpy

from pythalesians.timeseries.calcs.timeseriescalcs import TimeSeriesCalcs
from pythalesians.timeseries.calcs.timeseriesdesc import TimeSeriesDesc
from pythalesians.util.loggermanager import LoggerManager

class CashBacktest:

    def __init__(self):
        self.logger = LoggerManager().getLogger(__name__)
        self._pnl = None
        self._portfolio = None
        return

    def calculate_trading_PnL(self, br, asset_a_df, signal_df):
        """
        calculate_trading_PnL - Calculates P&L of a trading strategy and statistics to be retrieved later

        Parameters
        ----------
        br : BacktestRequest
            Parameters for the backtest specifying start date, finish data, transaction costs etc.

        asset_a_df : pandas.DataFrame
            Asset prices to be traded

        signal_df : pandas.DataFrame
            Signals for the trading strategy
        """

        tsc = TimeSeriesCalcs()
        # signal_df.to_csv('e:/temp0.csv')
        # make sure the dates of both traded asset and signal are aligned properly
        asset_df, signal_df = asset_a_df.align(signal_df, join='left', axis = 'index')

        # only allow signals to change on the days when we can trade assets
        signal_df = signal_df.mask(numpy.isnan(asset_df.values))    # fill asset holidays with NaN signals
        signal_df = signal_df.fillna(method='ffill')                # fill these down
        asset_df = asset_df.fillna(method='ffill')                  # fill down asset holidays

        returns_df = tsc.calculate_returns(asset_df)
        tc = br.spot_tc_bp

        signal_cols = signal_df.columns.values
        returns_cols = returns_df.columns.values

        pnl_cols = []

        for i in range(0, len(returns_cols)):
            pnl_cols.append(returns_cols[i] + " / " + signal_cols[i])

        # do we have a vol target for individual signals?
        if hasattr(br, 'signal_vol_adjust'):
            if br.signal_vol_adjust is True:
                if not(hasattr(br, 'signal_vol_resample_type')):
                    br.signal_vol_resample_type = 'mean'

                leverage_df = self.calculate_leverage_factor(returns_df, br.signal_vol_target, br.signal_vol_max_leverage,
                                               br.signal_vol_periods, br.signal_vol_obs_in_year,
                                               br.signal_vol_rebalance_freq, br.signal_vol_resample_freq,
                                               br.signal_vol_resample_type)

                signal_df = pandas.DataFrame(
                    signal_df.values * leverage_df.values, index = signal_df.index, columns = signal_df.columns)

                self._individual_leverage = leverage_df     # contains leverage of individual signal (before portfolio vol target)

        _pnl = tsc.calculate_signal_returns_with_tc_matrix(signal_df, returns_df, tc = tc)
        _pnl.columns = pnl_cols

        _pnl_trades = None

        # TODO FIX very slow
        _pnl_trades = tsc.calculate_individual_trade_gains(signal_df, _pnl)

        # portfolio is average of the underlying signals: should we sum them or average them?
        if hasattr(br, 'portfolio_combination'):
            if br.portfolio_combination == 'sum':
                 portfolio = pandas.DataFrame(data = _pnl.sum(axis = 1), index = _pnl.index, columns = ['Portfolio'])
            elif br.portfolio_combination == 'mean':
                 portfolio = pandas.DataFrame(data = _pnl.mean(axis = 1), index = _pnl.index, columns = ['Portfolio'])
        else:
            portfolio = pandas.DataFrame(data = _pnl.mean(axis = 1), index = _pnl.index, columns = ['Portfolio'])

        portfolio_leverage_df = pandas.DataFrame(data = numpy.ones(len(_pnl.index)), index = _pnl.index, columns = ['Portfolio'])

        # should we apply vol target on a portfolio level basis?
        if hasattr(br, 'portfolio_vol_adjust'):
            if br.portfolio_vol_adjust is True:
                portfolio, portfolio_leverage_df = self.calculate_vol_adjusted_returns(portfolio, br = br)

        self._pnl_trades = _pnl_trades
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
            elif br.portfolio_combination == 'mean':
                self._portfolio_signal = self._portfolio_signal / float(length_cols)
        else:
            self._portfolio_signal = self._portfolio_signal / float(length_cols)

        self._pnl = _pnl                                                            # individual signals P&L

        self._tsd_pnl = TimeSeriesDesc()
        self._tsd_pnl.calculate_ret_stats(self._pnl, br.ann_factor)

        self._portfolio.columns = ['Port']
        self._tsd_portfolio = TimeSeriesDesc()
        self._tsd_portfolio.calculate_ret_stats(self._portfolio, br.ann_factor)

        self._cumpnl = tsc.create_mult_index(self._pnl)                             # individual signals cumulative P&L
        self._cumpnl.columns = pnl_cols

        self._cumportfolio = tsc.create_mult_index(self._portfolio)                 # portfolio cumulative P&L
        self._cumportfolio.columns = ['Port']

    def calculate_vol_adjusted_index_from_prices(self, prices_df, br):
        """
        calculate_vol_adjusted_index_from_price - Adjusts an index of prices for a vol target

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

        tsc = TimeSeriesCalcs()

        returns_df, leverage_df = self.calculate_vol_adjusted_returns(prices_df, br, returns = False)

        return tsc.create_mult_index(returns_df)

    def calculate_vol_adjusted_returns(self, returns_df, br, returns = True):
        """
        calculate_vol_adjusted_returns - Adjusts returns for a vol target

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

        tsc = TimeSeriesCalcs()

        if not returns: returns_df = tsc.calculate_returns(returns_df)

        if not(hasattr(br, 'portfolio_vol_resample_type')):
            br.portfolio_vol_resample_type = 'mean'

        leverage_df = self.calculate_leverage_factor(returns_df,
                                                               br.portfolio_vol_target, br.portfolio_vol_max_leverage,
                                                               br.portfolio_vol_periods, br.portfolio_vol_obs_in_year,
                                                               br.portfolio_vol_rebalance_freq, br.portfolio_vol_resample_freq,
                                                               br.portfolio_vol_resample_type)

        vol_returns_df = tsc.calculate_signal_returns_with_tc_matrix(leverage_df, returns_df, tc = br.spot_tc_bp)
        vol_returns_df.columns = returns_df.columns

        return vol_returns_df, leverage_df

    def calculate_leverage_factor(self, returns_df, vol_target, vol_max_leverage, vol_periods = 60, vol_obs_in_year = 252,
                                  vol_rebalance_freq = 'BM', data_resample_freq = None, data_resample_type = 'mean',
                                  returns = True, period_shift = 0):
        """
        calculate_leverage_factor - Calculates the time series of leverage for a specified vol target

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

        vol_resample_freq : str
            do we need to resample the underlying data first? (eg. have we got intraday data?)

        returns : boolean
            is this returns time series or prices?

        period_shift : int
            should we delay the signal by a number of periods?

        Returns
        -------
        pandas.Dataframe
        """

        tsc = TimeSeriesCalcs()

        if data_resample_freq is not None:
            return
            # TODO not implemented yet

        if not returns: returns_df = tsc.calculate_returns(returns_df)

        roll_vol_df = tsc.rolling_volatility(returns_df,
                                        periods = vol_periods, obs_in_year = vol_obs_in_year).shift(period_shift)

        # calculate the leverage as function of vol target (with max lev constraint)
        lev_df = vol_target / roll_vol_df
        lev_df[lev_df > vol_max_leverage] = vol_max_leverage

        # should we take the mean, first, last in our resample
        if data_resample_type == 'mean':
            lev_df = lev_df.resample(vol_rebalance_freq).mean()
        elif data_resample_type == 'first':
            lev_df = lev_df.resample(vol_rebalance_freq).first()
        elif data_resample_type == 'last':
            lev_df = lev_df.resample(vol_rebalance_freq).last()
        else:
            # TODO implement other types
            return

        returns_df, lev_df = returns_df.align(lev_df, join='left', axis = 0)

        lev_df = lev_df.fillna(method='ffill')
        lev_df.ix[0:vol_periods] = numpy.nan    # ignore the first elements before the vol window kicks in

        return lev_df

    def get_backtest_output(self):
        return

    def get_pnl(self):
        """
        get_pnl - Gets P&L returns

        Returns
        -------
        pandas.Dataframe
        """
        return self._pnl

    def get_pnl_trades(self):
        """
        get_pnl_trades - Gets P&L of each individual trade per signal

        Returns
        -------
        pandas.Dataframe
        """
        return self._pnl_trades

    def get_pnl_desc(self):
        """
        get_pnl_desc - Gets P&L return statistics in a string format

        Returns
        -------
        str
        """
        return self._tsd_signals.summary()

    def get_pnl_tsd(self):
        """
        get_pnl_tsd - Gets P&L return statistics of individual strategies as class to be queried

        Returns
        -------
        TimeSeriesDesc
        """

        return self._tsd_pnl

    def get_cumpnl(self):
        """
        get_cumpnl - Gets P&L as a cumulative time series of individual assets

        Returns
        -------
        pandas.DataFrame
        """

        return self._cumpnl

    def get_cumportfolio(self):
        """
        get_cumportfolio - Gets P&L as a cumulative time series of portfolio

        Returns
        -------
        pandas.DataFrame
        """

        return self._cumportfolio

    def get_portfolio_pnl(self):
        """
        get_portfolio_pnl - Gets portfolio returns in raw form (ie. not indexed into cumulative form)

        Returns
        -------
        pandas.DataFrame
        """

        return self._portfolio

    def get_portfolio_pnl_desc(self):
        """
        get_portfolio_pnl_desc - Gets P&L return statistics of portfolio as string

        Returns
        -------
        pandas.DataFrame
        """

        return self._tsd_portfolio.summary()

    def get_portfolio_pnl_tsd(self):
        """
        get_portfolio_pnl_tsd - Gets P&L return statistics of portfolio as class to be queried

        Returns
        -------
        TimeSeriesDesc
        """

        return self._tsd_portfolio

    def get_individual_leverage(self):
        """
        get_individual_leverage - Gets leverage for each asset historically

        Returns
        -------
        pandas.DataFrame
        """

        return self._individual_leverage

    def get_porfolio_leverage(self):
        """
        get_portfolio_leverage - Gets the leverage for the portfolio

        Returns
        -------
        pandas.DataFrame
        """

        return self._portfolio_leverage

    def get_porfolio_signal(self):
        """
        get_portfolio_signal - Gets the signals (with individual leverage & portfolio leverage) for each asset, which
        equates to what we would trade in practice

        Returns
        -------
        DataFrame
        """

        return self._portfolio_signal

    def get_signal(self):
        """
        get_signal - Gets the signals (with individual leverage, but excluding portfolio leverage) for each asset

        Returns
        -------
        pandas.DataFrame
        """

        return self._signal

if __name__ == '__main__':
    # see cashbacktest_examples
    pass
