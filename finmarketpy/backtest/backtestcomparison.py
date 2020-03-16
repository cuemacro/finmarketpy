import numpy as np
import pandas as pd
from finmarketpy.util.marketconstants import MarketConstants

from findatapy.util import SwimPool
from findatapy.util import LoggerManager
from finmarketpy.backtest.backtestengine import TradingModel
from chartpy import Chart, Style, ChartConstants


class BacktestComparison(object):
    """
    Compares different backtest TradingModels
    Each model must have already been run
    """

    DEFAULT_PLOT_ENGINE = ChartConstants().chartfactory_default_engine
    SCALE_FACTOR = ChartConstants().chartfactory_scale_factor
    CHART_SOURCE = ChartConstants().chartfactory_source
    CHART_STYLE = Style()

    def __init__(self, models, ref_index=0,
                 labels=None):

        if hasattr(models, "__iter__") and all([isinstance(x, TradingModel) for x in models]):
            self.models = models
            self.ref_index = ref_index
        else:
            raise AttributeError("Models need to be an iterable of TradingModel instances.")

        self.labels = labels

    def plot_pnl(self, diff=True, silent_plot=False, reduce_plot=True):
        """
        Plots the profit and loss graph of the model.
        Returns the created Chart

        Parameters
        ---------
        diff
            if you want to get the profit differences instead of raw values
        silent_plot
            if you want to only return the chart created
        reduce_plot
            when plotting many points use WebGl version of plotly if specified
        """
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
        """
        Plots the sharpe ratio of the model
        Returns the created Chart

        Parameters
        ---------
        silent_plot
            if you want to only return the chart created
        reduce_plot:
            when plotting many points use WebGl version of plotly if specified
        """
        #sharpe does not take into account risk free rate for simplicity
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
        """
        Plots the notional trades of the model
        Returns the created Chart

        Parameters
        ---------
        diff
            if you want to get the profit differences instead of raw values
        silent_plot
            if you want to only return the chart created
        reduce_plot:
            when plotting many points use WebGl version of plotly if specified
        """
        style = self.models[self.ref_index]._create_style("", "Trades (Scaled by Notional)", reduce_plot=reduce_plot)

        models = self.models
        ref = self.ref_index

        strategy_trade_notional = [model._strategy_trade_notional for model in models]

        df = pd.concat(strategy_trade_notional, axis=1)
        #if you want to get the profit differences instead of raw values
        if diff:
            df = df.subtract(strategy_trade_notional[ref], axis='index')
        if self.labels is not None:
            df.columns = self.labels

        chart = Chart(df, engine=self.DEFAULT_PLOT_ENGINE, chart_type='bar', style=style)
        if not silent_plot:
            chart.plot()

        return chart
