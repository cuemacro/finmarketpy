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
TradeAnalysis

Applies some basic trade analysis for a trading strategy (as defined by StrategyTemplate). Use PyFolio to create some
basic trading statistics.

"""

pf = None

try:
    import pyfolio as pf
except: pass

import datetime
import pandas

from pythalesians.util.loggermanager import LoggerManager
from pythalesians.timeseries.calcs.timeseriestimezone import TimeSeriesTimezone
from pythalesians.timeseries.calcs.timeseriescalcs import TimeSeriesCalcs

import matplotlib
import matplotlib.pyplot as plt

class TradeAnalysis:

    def __init__(self):
        self.logger = LoggerManager().getLogger(__name__)
        self.DUMP_PATH = 'output_data/' + datetime.date.today().strftime("%Y%m%d") + ' '
        self.scale_factor = 3
        return

    def run_strategy_returns_stats(self, strategy):
        """
        run_strategy_returns_stats - Plots useful statistics for the trading strategy (using PyFolio)

        Parameters
        ----------
        strategy : StrategyTemplate
            defining trading strategy

        """

        pnl = strategy.get_strategy_pnl()
        tz = TimeSeriesTimezone()
        tsc = TimeSeriesCalcs()

        # PyFolio assumes UTC time based DataFrames (so force this localisation)
        try:
            pnl = tz.localise_index_as_UTC(pnl)
        except: pass

        # TODO for intraday strategy make daily

        # convert DataFrame (assumed to have only one column) to Series
        pnl = tsc.calculate_returns(pnl)
        pnl = pnl[pnl.columns[0]]

        fig = pf.create_returns_tear_sheet(pnl, return_fig=True)

        plt.show()

        try:
            plt.savefig (strategy.DUMP_PATH + "stats.png")
        except: pass



