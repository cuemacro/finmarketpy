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

class TimeSeriesCalcs:

    def calculate_signal_tc(self, signal_data_frame, tc, period_shift = 1):
        return (signal_data_frame.shift(period_shift) - signal_data_frame).abs().multiply(tc)

    def calculate_entry_tc(self, entry_data_frame, tc, period_shift = 1):
        return entry_data_frame.abs().multiply(tc)

    def calculate_signal_returns(self, signal_data_frame, returns_data_frame, period_shift = 1):
        return signal_data_frame.shift(period_shift) * returns_data_frame

    def calculate_signal_returns_matrix(self, signal_data_frame, returns_data_frame, period_shift = 1):
        return pandas.DataFrame(
            signal_data_frame.shift(period_shift).values * returns_data_frame.values, index = returns_data_frame.index)

    def calculate_signal_returns_with_tc(self, signal_data_frame, returns_data_frame, tc, period_shift = 1):
        return signal_data_frame.shift(period_shift) * returns_data_frame - self.calculate_signal_tc(signal_data_frame, tc, period_shift)

    def calculate_signal_returns_with_tc_matrix(self, signal_data_frame, returns_data_frame, tc, period_shift = 1):
        return pandas.DataFrame(
            signal_data_frame.shift(period_shift).values * returns_data_frame.values -
                (numpy.abs(signal_data_frame.shift(period_shift).values - signal_data_frame.values) * tc), index = returns_data_frame.index)

    def calculate_returns(self, data_frame, period_shift = 1):
        return data_frame / data_frame.shift(period_shift) - 1

    def calculate_diff_returns(self, data_frame, period_shift = 1):
        return data_frame - data_frame.shift(period_shift)

    def calculate_log_returns(self, data_frame, period_shift = 1):
        return math.log(data_frame / data_frame.shift(period_shift))

    def create_mult_index(self, df_rets):
        df = 100.0 * (1.0 + df_rets).cumprod()

        # get the first non-nan values for rets and then start index
        # one before that (otherwise will ignore first rets point)
        first_date_indices = df_rets.apply(lambda series: series.first_valid_index())
        first_ord_indices = list()

        for i in first_date_indices:
            ind = df.index.searchsorted(i)

            if ind > 0: ind = ind - 1

            first_ord_indices.append(ind)

        for i in range(0, len(df.columns)):
            df.iloc[first_ord_indices[i],i] = 100

        return df

    def create_mult_index_from_prices(self, data_frame):
        return self.create_mult_index(self.calculate_returns(data_frame))

    def rolling_z_score(self, data_frame, periods):
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

    ##### various methods for averaging time series by hours, mins and days to create summary time series
    def average_by_hour_min_of_day(self, data_frame):
        return data_frame.\
            groupby([data_frame.index.hour, data_frame.index.minute]).mean()

    def average_by_hour_min_of_day_pretty_output(self, data_frame):
        data_frame = data_frame.\
            groupby([data_frame.index.hour, data_frame.index.minute]).mean()

        data_frame.index = data_frame.index.map(lambda t: datetime.time(*t))

        return data_frame

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

if __name__ == '__main__':

    tsc = TimeSeriesCalcs()
    tsf = TimeSeriesFilter()

    # test rolling ewma
    date_range = pandas.bdate_range('2014-01-01', '2014-02-28')

    print(tsc.get_bus_day_of_month(date_range))

    foo = pandas.DataFrame(numpy.arange(0.0,13.0))
    print(tsc.rolling_ewma(foo, span=3))
