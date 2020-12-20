#
# Copyright 2016-2020 Cuemacro - https://www.cuemacro.com / @cuemacro
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
from finmarketpy.backtest.backtestengine import TradingModel
from chartpy import Chart, Style, ChartConstants

class BacktestComparison(object):

    DEFAULT_PLOT_ENGINE = ChartConstants().chartfactory_default_engine
    SCALE_FACTOR = ChartConstants().chartfactory_scale_factor
    CHART_SOURCE = ChartConstants().chartfactory_source
    CHART_STYLE = Style()

    def __init__(self, models, ref_index=0,
                 labels=None):
        """

        :param models: iterable of TradingModel instances.
        :param ref_index: index of the reference model in the list (for difference).
        """
        if hasattr(models, "__iter__") and all([isinstance(x, TradingModel) for x in models]):
            self.models = models
            self.ref_index = ref_index
        else:
            raise AttributeError("Models need to be an iterable of TradingModel instances.")

        self.labels = labels

    def plot_pnl(self, diff=True, silent_plot=False, reduce_plot=True):
        style = self.models[self.ref_index]._create_style("", "Strategy PnL", reduce_plot=reduce_plot)

        models = self.models
        ref = self.ref_index

        pnls = [model._strategy_pnl for model in models]

        df = pd.concat(pnls, axis=1)

        if diff:
            df = df.subtract(pnls[ref], axis='index')
        if self.labels is not None:
            df.columns = self.labels

        chart = Chart(df, engine=self.DEFAULT_PLOT_ENGINE, chart_type='line', style=style)
        if not silent_plot:
            chart.plot()

        return chart

    def plot_sharpe(self, silent_plot=False, reduce_plot=True):
        style = self.models[self.ref_index]._create_style("", "Sharpe Curve", reduce_plot=reduce_plot)

        models = self.models
        ref = self.ref_index

        returns = [model._strategy_pnl.pct_change() for model in models]
        stdev_of_returns = np.std(returns)

        annualized_sharpe = returns / stdev_of_returns * np.sqrt(250)

        df = pd.concat(annualized_sharpe, axis=1)

        chart = Chart(df, engine=self.DEFAULT_PLOT_ENGINE, chart_type='bar', style=style)
        if not silent_plot:
            chart.plot()
        return chart

    def plot_strategy_trade_notional(self, diff=True, silent_plot=False, reduce_plot=True):
        style = self.models[self.ref_index]._create_style("", "Trades (Scaled by Notional)", reduce_plot=reduce_plot)

        models = self.models
        ref = self.ref_index

        strategy_trade_notional = [model._strategy_trade_notional for model in models]

        df = pd.concat(strategy_trade_notional, axis=1)

        if diff:
            df = df.subtract(strategy_trade_notional[ref], axis='index')
        if self.labels is not None:
            df.columns = self.labels

        chart = Chart(df, engine=self.DEFAULT_PLOT_ENGINE, chart_type='bar', style=style)
        if not silent_plot:
            chart.plot()

        return chart
