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
TimeSeriesDesc

Calculating return statistics of a time series

"""

import math

from pythalesians.timeseries.calcs.timeseriescalcs import TimeSeriesCalcs

import pandas

class TimeSeriesDesc:

    def calculate_ret_stats_from_prices(self, returns_df, ann_factor):
        tsc = TimeSeriesCalcs()

        self.calculate_ret_stats(tsc.calculate_returns(returns_df), ann_factor)

    def calculate_ret_stats(self, returns_df, ann_factor):
        tsc = TimeSeriesCalcs()

        self._rets = returns_df.mean(axis=0) * ann_factor
        self._vol = returns_df.std(axis=0) * math.sqrt(ann_factor)
        self._inforatio = self._rets / self._vol

        index_df = tsc.create_mult_index(returns_df)
        max2here = pandas.expanding_max(index_df)
        dd2here = index_df / max2here - 1

        self._dd = dd2here.min()

    def ann_returns(self):
        return self._rets

    def ann_vol(self):
        return self._vol

    def inforatio(self):
        return self._inforatio

    def drawdowns(self):
        return self._dd

    def summary(self):
        stat_list = []

        for i in range(0, len(self._rets.index)):
            stat_list.append(self._rets.index[i] + " Ret = " + str(round(self._rets[i] * 100, 1))
                             + "% Vol = " + str(round(self._vol[i] * 100, 1))
                             + "% IR = " + str(round(self._inforatio[i], 2))
                             + " Dr = " + str(round(self._dd[i] * 100, 1)) + "%")

        return stat_list