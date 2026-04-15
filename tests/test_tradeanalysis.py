"""Tests for TradeAnalysis."""
# ruff: noqa: D101,D102,D103

import os
import tempfile

import numpy as np
import pandas as pd
import pytest

from finmarketpy.backtest.backtestengine import TradingModel
from finmarketpy.backtest.backtestrequest import BacktestRequest
from finmarketpy.backtest.tradeanalysis import TradeAnalysis


# Minimal model from backtestengine tests
class MinimalTradingModel(TradingModel):
    FINAL_STRATEGY = "TestStrategy"

    def load_parameters(self, br=None):
        new_br = BacktestRequest()
        new_br.start_date = "2020-01-01"
        new_br.finish_date = "2020-06-30"
        new_br.spot_tc_bp = 0.5
        new_br.ann_factor = 252
        return new_br

    def load_assets(self, br=None):
        dates = pd.date_range(start="2020-01-01", periods=100, freq="B")
        rng = np.random.default_rng(42)
        prices = 100 + np.cumsum(rng.normal(0, 1, (100, 1)), axis=0)
        asset_df = pd.DataFrame(prices, index=dates, columns=["EURUSD.close"])
        spot_df = asset_df.copy()
        basket_dict = {"EURUSD": ["EURUSD"], self.FINAL_STRATEGY: ["EURUSD"]}
        return asset_df, spot_df, spot_df.copy(), basket_dict

    def construct_signal(self, spot_df=None, spot_df2=None, tech_params=None, br=None, run_in_parallel=False):
        signals = np.where(np.arange(len(spot_df)) % 10 < 5, 1.0, -1.0)
        return pd.DataFrame(signals, index=spot_df.index, columns=spot_df.columns)

    def construct_strategy_benchmark(self):
        return None


@pytest.fixture
def built_model():
    tm = MinimalTradingModel()
    tm.construct_strategy()
    return tm


def test_trade_analysis_init():
    ta = TradeAnalysis()
    assert ta is not None
    assert ta.DEFAULT_PLOT_ENGINE is not None
    assert ta.DUMP_PATH is not None


def test_trade_analysis_init_with_engine():
    ta = TradeAnalysis(engine="plotly")
    assert ta.DEFAULT_PLOT_ENGINE == "plotly"


def test_run_excel_trade_report(built_model):
    """Test that run_excel_trade_report writes an Excel file."""
    ta = TradeAnalysis()
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        fname = f.name

    try:
        ta.run_excel_trade_report(built_model, excel_file=fname)
        assert os.path.exists(fname)
        assert os.path.getsize(fname) > 0
    finally:
        if os.path.exists(fname):
            os.unlink(fname)


def test_run_excel_trade_report_list(built_model):
    """Test that run_excel_trade_report works with a list of models."""
    ta = TradeAnalysis()
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        fname = f.name

    try:
        ta.run_excel_trade_report([built_model], excel_file=fname)
        assert os.path.exists(fname)
    finally:
        if os.path.exists(fname):
            os.unlink(fname)


def test_save_positions_trades(built_model):
    """Test save_positions_trades directly."""
    ta = TradeAnalysis()
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        fname = f.name

    try:
        writer = pd.ExcelWriter(fname, engine="xlsxwriter")
        signals = built_model.strategy_signal()
        trades = built_model.strategy_trade()
        ta.save_positions_trades(built_model, signals, trades, "pos", "trades", writer)
        writer.close()
    finally:
        if os.path.exists(fname):
            os.unlink(fname)


def test_run_excel_trade_report_with_notional(built_model):
    """Test run_excel_trade_report with _strategy_signal_notional set (lines 182)."""
    ta = TradeAnalysis()
    dates = pd.date_range(start="2020-01-01", periods=100, freq="B")
    notional_df = pd.DataFrame(
        np.ones((100, 1)),
        index=dates,
        columns=["EURUSD.close"],
    )
    # Set the attributes directly so hasattr checks pass
    built_model._strategy_signal_notional = notional_df
    built_model._strategy_trade_notional = notional_df

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        fname = f.name

    try:
        ta.run_excel_trade_report(built_model, excel_file=fname)
        assert os.path.exists(fname)
    finally:
        if os.path.exists(fname):
            os.unlink(fname)


def test_run_excel_trade_report_with_contracts(built_model):
    """Test run_excel_trade_report with _strategy_signal_contracts set (line 192)."""
    ta = TradeAnalysis()
    dates = pd.date_range(start="2020-01-01", periods=100, freq="B")
    contracts_df = pd.DataFrame(
        np.ones((100, 1)),
        index=dates,
        columns=["EURUSD.close"],
    )
    built_model._strategy_signal_contracts = contracts_df
    built_model._strategy_trade_contracts = contracts_df

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        fname = f.name

    try:
        ta.run_excel_trade_report(built_model, excel_file=fname)
        assert os.path.exists(fname)
    finally:
        if os.path.exists(fname):
            os.unlink(fname)
