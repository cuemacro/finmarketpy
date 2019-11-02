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





