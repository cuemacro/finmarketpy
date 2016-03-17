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
#the License for the specific language governing permissions and limitations under the License.
#

"""
TimeSeriesCalcs

Calculations on time series, such as calculating strategy returns and various wrappers on pandas for rolling sums etc.

"""

import pandas
import math
import datetime

import numpy
import pandas.tseries.offsets
from pythalesians.util.calendar import Calendar

from pythalesians.timeseries.calcs.timeseriesfilter import TimeSeriesFilter
from pandas.stats.api import ols

class TimeSeriesCalcs:

    def calculate_signal_tc(self, signal_data_frame, tc, period_shift = 1):
        """
        calculate_signal_tc - Calculates the transaction costs for a particular signal

        Parameters
        ----------
        signal_data_frame : DataFrame
            contains trading signals
        tc : float
            transaction costs
        period_shift : int
            number of periods to shift signal

        Returns
        -------
        DataFrame
        """
        return (signal_data_frame.shift(period_shift) - signal_data_frame).abs().multiply(tc)

    def calculate_entry_tc(self, entry_data_frame, tc, period_shift = 1):
        """
        calculate_entry_tc - Calculates the transaction costs for defined trading points

        Parameters
        ----------
        entry_data_frame : DataFrame
            contains points where we enter/exit trades
        tc : float
            transaction costs
        period_shift : int
            number of periods to shift signal

        Returns
        -------
        DataFrame
        """
        return entry_data_frame.abs().multiply(tc)

    def calculate_signal_returns(self, signal_data_frame, returns_data_frame, period_shift = 1):
        """
        calculate_signal_returns - Calculates the trading startegy returns for given signal and asset

        Parameters
        ----------
        signal_data_frame : DataFrame
            trading signals
        returns_data_frame: DataFrame
            returns of asset to be traded
        period_shift : int
            number of periods to shift signal

        Returns
        -------
        DataFrame
        """
        return signal_data_frame.shift(period_shift) * returns_data_frame

    def calculate_individual_trade_gains(self, signal_data_frame, strategy_returns_data_frame):
        """
        calculate_individual_trade_gains - Calculates profits on every trade

        Parameters
        ----------
        signal_data_frame : DataFrame
            trading signals
        strategy_returns_data_frame: DataFrame
            returns of strategy to be tested
        period_shift : int
            number of periods to shift signal

        Returns
        -------
        DataFrame
        """

        # signal need to be aligned to NEXT period for returns
        signal_data_frame_pushed = signal_data_frame.shift(1)

        # find all the trade points
        trade_points = ((signal_data_frame - signal_data_frame.shift(1)).abs())
        cumulative = self.create_mult_index(strategy_returns_data_frame)

        indices = trade_points > 0
        indices.columns = cumulative.columns

        # get P&L for every trade (from the end point - start point)
        trade_returns = numpy.nan * cumulative
        trade_points_cumulative = cumulative[indices]

        # for each set of signals/returns, calculate the trade returns - where there isn't a trade
        # assign a NaN
        # TODO do in one vectorised step without for loop
        for col_name in trade_points_cumulative:
            col = trade_points_cumulative[col_name]
            col = col.dropna()
            col = col / col.shift(1) - 1

            # TODO experiment with quicker ways of writing below?
            # for val in col.index:
                # trade_returns.set_value(val, col_name, col[val])
                # trade_returns.ix[val, col_name] = col[val]

            date_indices = trade_returns.index.searchsorted(col.index)
            trade_returns.ix[date_indices, col_name] = col

        return trade_returns

    def calculate_signal_returns_matrix(self, signal_data_frame, returns_data_frame, period_shift = 1):
        """
        calculate_signal_returns_matrix - Calculates the trading strategy returns for given signal and asset
        as a matrix multiplication

        Parameters
        ----------
        signal_data_frame : DataFrame
            trading signals
        returns_data_frame: DataFrame
            returns of asset to be traded
        period_shift : int
            number of periods to shift signal

        Returns
        -------
        DataFrame
        """
        return pandas.DataFrame(
            signal_data_frame.shift(period_shift).values * returns_data_frame.values, index = returns_data_frame.index)

    def calculate_signal_returns_with_tc(self, signal_data_frame, returns_data_frame, tc, period_shift = 1):
        """
        calculate_singal_returns_with_tc - Calculates the trading startegy returns for given signal and asset including
        transaction costs

        Parameters
        ----------
        signal_data_frame : DataFrame
            trading signals
        returns_data_frame: DataFrame
            returns of asset to be traded
        tc : float
            transaction costs
        period_shift : int
            number of periods to shift signal

        Returns
        -------
        DataFrame
        """
        return signal_data_frame.shift(period_shift) * returns_data_frame - self.calculate_signal_tc(signal_data_frame, tc, period_shift)

    def calculate_signal_returns_with_tc_matrix(self, signal_data_frame, returns_data_frame, tc, period_shift = 1):
        """
        calculate_singal_returns_with_tc_matrix - Calculates the trading startegy returns for given signal and asset
        with transaction costs with matrix multiplication

        Parameters
        ----------
        signal_data_frame : DataFrame
            trading signals
        returns_data_frame: DataFrame
            returns of asset to be traded
        tc : float
            transaction costs
        period_shift : int
            number of periods to shift signal

        Returns
        -------
        DataFrame
        """
        return pandas.DataFrame(
            signal_data_frame.shift(period_shift).values * returns_data_frame.values -
                (numpy.abs(signal_data_frame.shift(period_shift).values - signal_data_frame.values) * tc), index = returns_data_frame.index)

    def calculate_returns(self, data_frame, period_shift = 1):
        """
        calculate_returns - Calculates the simple returns for an asset

        Parameters
        ----------
        data_frame : DataFrame
            asset price
        period_shift : int
            number of periods to shift signal

        Returns
        -------
        DataFrame
        """
        return data_frame / data_frame.shift(period_shift) - 1

    def calculate_diff_returns(self, data_frame, period_shift = 1):
        """
        calculate_diff_returns - Calculates the differences for an asset

        Parameters
        ----------
        data_frame : DataFrame
            asset price
        period_shift : int
            number of periods to shift signal

        Returns
        -------
        DataFrame
        """
        return data_frame - data_frame.shift(period_shift)

    def calculate_log_returns(self, data_frame, period_shift = 1):
        """
        calculate_log_returns - Calculates the log returns for an asset

        Parameters
        ----------
        data_frame : DataFrame
            asset price
        period_shift : int
            number of periods to shift signal

        Returns
        -------
        DataFrame
        """
        return math.log(data_frame / data_frame.shift(period_shift))

    def create_mult_index(self, df_rets):
        """
        calculate_mult_index - Calculates a multiplicative index for a time series of returns

        Parameters
        ----------
        df_rets : DataFrame
            asset price returns

        Returns
        -------
        DataFrame
        """
        df = 100.0 * (1.0 + df_rets).cumprod()

        # get the first non-nan values for rets and then start index
        # one before that (otherwise will ignore first rets point)
        first_date_indices = df_rets.apply(lambda series: series.first_valid_index())
        first_ord_indices = list()

        for i in first_date_indices:
            try:
                ind = df.index.searchsorted(i)
            except:
                ind = 0

            if ind > 0: ind = ind - 1

            first_ord_indices.append(ind)

        for i in range(0, len(df.columns)):
            df.iloc[first_ord_indices[i],i] = 100

        return df

    def create_mult_index_from_prices(self, data_frame):
        """
        calculate_mult_index_from_prices - Calculates a multiplicative index for a time series of prices

        Parameters
        ----------
        df_rets : DataFrame
            asset price

        Returns
        -------
        DataFrame
        """
        return self.create_mult_index(self.calculate_returns(data_frame))

    def rolling_z_score(self, data_frame, periods):
        """
        rolling_z_score - Calculates the rolling z score for a time series

        Parameters
        ----------
        data_frame : DataFrame
            asset prices
        periods : int
            rolling window for z score computation

        Returns
        -------
        DataFrame
        """
        return (data_frame - pandas.rolling_mean(data_frame, periods)) / pandas.rolling_std(data_frame, periods)

    def rolling_volatility(self, data_frame, periods, obs_in_year = 252):
        """
        rolling_volatility - Calculates the annualised rolling volatility

        Parameters
        ----------
        data_frame : DataFrame
            contains returns time series
        obs_in_year : int
            number of observation in the year

        Returns
        -------
        DataFrame
        """

        return pandas.rolling_std(data_frame, periods) * math.sqrt(obs_in_year)

    def rolling_mean(self, data_frame, periods):
        return self.rolling_average(data_frame, periods)

    def rolling_average(self, data_frame, periods):
        """
        rolling_average - Calculates the rolling moving average

        Parameters
        ----------
        data_frame : DataFrame
            contains time series
        periods : int
            periods in the average

        Returns
        -------
        DataFrame
        """
        return pandas.rolling_mean(data_frame, periods)

    def rolling_sparse_average(self, data_frame, periods):
        """
        rolling_sparse_average - Calculates the rolling moving average of a sparse time series

        Parameters
        ----------
        data_frame : DataFrame
            contains time series
        periods : int
            number of periods in the rolling sparse average

        Returns
        -------
        DataFrame
        """

        # 1. calculate rolling sum (ignore NaNs)
        # 2. count number of non-NaNs
        # 3. average of non-NaNs
        foo = lambda z: z[pandas.notnull(z)].sum()

        rolling_sum = pandas.rolling_apply(data_frame, periods, foo, min_periods=1)
        rolling_non_nans = pandas.stats.moments.rolling_count(data_frame, periods, freq=None, center=False, how=None)

        return rolling_sum / rolling_non_nans

    def rolling_sparse_sum(self, data_frame, periods):
        """
        rolling_sparse_sum - Calculates the rolling moving sum of a sparse time series

        Parameters
        ----------
        data_frame : DataFrame
            contains time series
        periods : int
            period for sparse rolling sum

        Returns
        -------
        DataFrame
        """

        # 1. calculate rolling sum (ignore NaNs)
        # 2. count number of non-NaNs
        # 3. average of non-NaNs
        foo = lambda z: z[pandas.notnull(z)].sum()

        rolling_sum = pandas.rolling_apply(data_frame, periods, foo, min_periods=1)

        return rolling_sum

    def rolling_median(self, data_frame, periods):
        """
        rolling_median - Calculates the rolling moving average

        Parameters
        ----------
        data_frame : DataFrame
            contains time series
        periods : int
            number of periods in the median

        Returns
        -------
        DataFrame
        """
        return pandas.rolling_median(data_frame, periods)

    def rolling_sum(self, data_frame, periods):
        """
        rolling_sum - Calculates the rolling sum

        Parameters
        ----------
        data_frame : DataFrame
            contains time series
        periods : int
            period for rolling sum

        Returns
        -------
        DataFrame
        """
        return pandas.rolling_sum(data_frame, periods)

    def cum_sum(self, data_frame):
        """
        cum_sum - Calculates the cumulative sum

        Parameters
        ----------
        data_frame : DataFrame
            contains time series

        Returns
        -------
        DataFrame
        """
        return data_frame.cumsum()

    def rolling_ewma(self, data_frame, periods):
        """
        rolling_ewma - Calculates exponentially weighted moving average

        Parameters
        ----------
        data_frame : DataFrame
            contains time series
        periods : int
            periods in the EWMA

        Returns
        -------
        DataFrame
        """

        # span = 2 / (1 + periods)

        return pandas.ewma(data_frame, span=periods)

    ##### correlation methods
    def rolling_corr(self, data_frame1, periods, data_frame2 = None, pairwise = False, flatten_labels = True):
        """
        rolling_corr - Calculates rolling correlation wrapping around pandas functions

        Parameters
        ----------
        data_frame1 : DataFrame
            contains time series to run correlations on
        periods : int
            period of rolling correlations
        data_frame2 : DataFrame (optional)
            contains times series to run correlation against
        pairwise : boolean
            should we do pairwise correlations only?

        Returns
        -------
        DataFrame
        """

        panel = pandas.rolling_corr(data_frame1, data_frame2, periods, pairwise = pairwise)

        try:
            df = panel.to_frame(filter_observations=False).transpose()

        except:
            df = panel

        if flatten_labels:
            if pairwise:
                series1 = df.columns.get_level_values(0)
                series2 = df.columns.get_level_values(1)
                new_labels = []

                for i in range(len(series1)):
                    new_labels.append(series1[i] + " v " + series2[i])

            else:
                new_labels = []

                try:
                    series1 = data_frame1.columns
                except:
                    series1 = [data_frame1.name]

                series2 = data_frame2.columns

                for i in range(len(series1)):
                    for j in range(len(series2)):
                        new_labels.append(series1[i] + " v " + series2[j])

            df.columns = new_labels

        return df

    def linear_regression(self, df_y, df_x):
        return pandas.stats.api.ols(y = df_y, x = df_x)

    def linear_regression_single_vars(self, df_y, df_x, y_vars, x_vars):
        stats = []

        for i in range(0, len(y_vars)):
            y = df_y[y_vars[i]]
            x = df_x[x_vars[i]]

            try:
                out = pandas.stats.api.ols(y = y, x = x)
            except:
                out = None

            stats.append(out)

        return stats

    def strip_linear_regression_output(self, indices, ols_list, var):

        if not(isinstance(var, list)):
            var = [var]

        df = pandas.DataFrame(index = indices, columns=var)

        for v in var:
            list_o = []

            for o in ols_list:
                if o is None:
                    list_o.append(numpy.nan)
                else:
                    if v == 't_stat':
                        list_o.append(o.t_stat.x)
                    elif v == 't_stat_intercept':
                        list_o.append(o.t_stat.intercept)
                    elif v == 'beta':
                        list_o.append(o.beta.x)
                    elif v == 'beta_intercept':
                        list_o.append(o.beta.intercept)
                    else:
                        return None

            df[v] = list_o
        return df

    ##### various methods for averaging time series by hours, mins and days to create summary time series
    def average_by_hour_min_of_day(self, data_frame):
        return data_frame.\
            groupby([data_frame.index.hour, data_frame.index.minute]).mean()

    def average_by_hour_min_of_day_pretty_output(self, data_frame):
        data_frame = data_frame.\
            groupby([data_frame.index.hour, data_frame.index.minute]).mean()

        data_frame.index = data_frame.index.map(lambda t: datetime.time(*t))

        return data_frame

    def all_by_hour_min_of_day_pretty_output(self, data_frame):

        df_new = []

        for group in data_frame.groupby(data_frame.index.date):
            df_temp = group[1]
            df_temp.index = df_temp.index.time
            df_temp.columns = [group[0]]
            df_new.append(df_temp)

        return pandas.concat(df_new, axis=1)

    def average_by_year_hour_min_of_day_pretty_output(self, data_frame):
        # years = range(data_frame.index[0].year, data_frame.index[-1].year)
        #
        # time_of_day = []
        #
        # for year in years:
        #     temp = data_frame.ix[data_frame.index.year == year]
        #     time_of_day.append(temp.groupby(temp.index.time).mean())
        #
        # data_frame = pandas.concat(time_of_day, axis=1, keys = years)
        data_frame = data_frame.\
            groupby([data_frame.index.year, data_frame.index.hour, data_frame.index.minute]).mean()

        data_frame = data_frame.unstack(0)

        data_frame.index = data_frame.index.map(lambda t: datetime.time(*t))

        return data_frame

    def average_by_annualised_year(self, data_frame, obs_in_year = 252):
        data_frame = data_frame.\
            groupby([data_frame.index.year]).mean() * obs_in_year

        return data_frame

    def average_by_month(self, data_frame):
        data_frame = data_frame.\
            groupby([data_frame.index.month]).mean()

        return data_frame

    def average_by_bus_day(self, data_frame, cal = "FX"):
        date_index = data_frame.index

        return data_frame.\
            groupby([Calendar().get_bus_day_of_month(date_index, cal)]).mean()

    def average_by_month_day_hour_min_by_bus_day(self, data_frame, cal = "FX"):
        date_index = data_frame.index

        return data_frame.\
            groupby([date_index.month,
                     Calendar().get_bus_day_of_month(date_index, cal),
                     date_index.hour, date_index.minute]).mean()

    def average_by_month_day_by_bus_day(self, data_frame, cal = "FX"):
        date_index = data_frame.index

        return data_frame.\
            groupby([date_index.month,
                     Calendar().get_bus_day_of_month(date_index, cal)]).mean()

    def average_by_month_day_by_day(self, data_frame, cal = "FX"):
        date_index = data_frame.index

        return data_frame.\
            groupby([date_index.month, date_index.day]).mean()

    def group_by_year(self, data_frame):
        date_index = data_frame.index

        return data_frame.\
            groupby([date_index.year])

    def average_by_day_hour_min_by_bus_day(self, data_frame):
        date_index = data_frame.index

        return data_frame.\
            groupby([Calendar().get_bus_day_of_month(date_index),
                     date_index.hour, date_index.minute]).mean()

    def remove_NaN_rows(self, data_frame):
        return data_frame.dropna()

    def get_top_valued_sorted(self, df, order_column, n = 20):
        df_sorted = df.sort(columns=order_column)
        df_sorted = df_sorted.tail(n=n)

        return df_sorted

    def get_bottom_valued_sorted(self, df, order_column, n = 20):
        df_sorted = df.sort(columns=order_column)
        df_sorted = df_sorted.head(n=n)

        return df_sorted

    def convert_month_day_to_date_time(self, df, year = 1970):
        new_index = []

        # TODO use map?
        for i in range(0, len(df.index)):
            x = df.index[i]
            new_index.append(datetime.date(year, x[0], int(x[1])))

        df.index = pandas.DatetimeIndex(new_index)

        return df

if __name__ == '__main__':

    # test functions
    tsc = TimeSeriesCalcs()
    tsf = TimeSeriesFilter()

    # test rolling ewma
    date_range = pandas.bdate_range('2014-01-01', '2014-02-28')

    print(tsc.get_bus_day_of_month(date_range))

    foo = pandas.DataFrame(numpy.arange(0.0,13.0))
    print(tsc.rolling_ewma(foo, span=3))
