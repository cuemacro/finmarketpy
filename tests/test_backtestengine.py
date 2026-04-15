"""Tests for backtestengine.py - Backtest, TradingModel, PortfolioWeightConstruction, RiskEngine."""
# ruff: noqa: D101,D102,D103

import io

import numpy as np
import pandas as pd
import pytest

from finmarketpy.backtest.backtestengine import (
    Backtest,
    PortfolioWeightConstruction,
    RiskEngine,
    TradingModel,
)
from finmarketpy.backtest.backtestrequest import BacktestRequest

# -------------------------------------------------------------------
# Helper fixtures
# -------------------------------------------------------------------


@pytest.fixture
def simple_dates():
    return pd.date_range(start="2020-01-01", periods=100, freq="B")


@pytest.fixture
def asset_df(simple_dates):
    """Simple asset price series."""
    prices = 100 + np.cumsum(np.random.default_rng(42).normal(0, 1, (100, 1)), axis=0)
    return pd.DataFrame(prices, index=simple_dates, columns=["EURUSD.close"])


@pytest.fixture
def signal_df(simple_dates):
    """Simple alternating signal."""
    signals = np.where(np.arange(100) % 10 < 5, 1.0, -1.0)
    return pd.DataFrame(signals, index=simple_dates, columns=["EURUSD.close"])


@pytest.fixture
def default_br():
    br = BacktestRequest()
    br.start_date = "2020-01-01"
    br.finish_date = "2020-06-30"
    br.spot_tc_bp = 0.5
    br.ann_factor = 252
    return br


# -------------------------------------------------------------------
# Minimal concrete TradingModel
# -------------------------------------------------------------------


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


# -------------------------------------------------------------------
# Backtest tests
# -------------------------------------------------------------------


def test_backtest_init():
    bt = Backtest()
    assert bt._pnl is None
    assert bt._portfolio is None


def test_calculate_diagnostic_pnl(asset_df, signal_df):
    bt = Backtest()
    result = bt.calculate_diagnostic_trading_PnL(asset_df, signal_df)
    assert result is not None
    assert isinstance(result, pd.DataFrame)


def test_calculate_diagnostic_pnl_with_further_df(asset_df, signal_df):
    bt = Backtest()
    further_df = [signal_df.copy()]
    further_labels = ["raw_signal"]
    result = bt.calculate_diagnostic_trading_PnL(
        asset_df, signal_df, further_df=further_df, further_df_labels=further_labels
    )
    assert result is not None
    # Should include columns from further_df
    assert any("raw_signal" in col for col in result.columns)


def test_calculate_exposures(signal_df):
    bt = Backtest()
    longs, shorts, net, total = bt.calculate_exposures(signal_df)
    assert longs is not None
    assert shorts is not None
    assert net is not None
    assert total is not None
    assert longs.columns[0] == "Total Longs"
    assert shorts.columns[0] == "Total Shorts"
    assert net.columns[0] == "Net Exposure"
    assert total.columns[0] == "Total Exposure"


def test_backtest_output():
    bt = Backtest()
    result = bt.backtest_output()
    assert result is None


def test_all_getters_return_none_initially():
    bt = Backtest()
    assert bt.pnl() is None
    assert bt._portfolio is None


def test_filter_by_plot_start_finish_date_both_none(asset_df, default_br):
    bt = Backtest()
    result = bt._filter_by_plot_start_finish_date(asset_df, default_br)
    assert result is asset_df


def test_filter_by_plot_start_finish_date_with_dates(asset_df, default_br):
    bt = Backtest()
    default_br.plot_start = "2020-02-01"
    default_br.plot_finish = "2020-04-30"
    result = bt._filter_by_plot_start_finish_date(asset_df, default_br)
    assert result is not None


def test_filter_by_plot_start_finish_date_none_df(default_br):
    bt = Backtest()
    default_br.plot_start = "2020-02-01"
    result = bt._filter_by_plot_start_finish_date(None, default_br)
    assert result is None


def test_calculate_trading_pnl(asset_df, signal_df, default_br):
    bt = Backtest()
    bt.calculate_trading_PnL(default_br, asset_df, signal_df, None, False)

    # After calling, PnL attributes should be set
    assert bt.pnl() is not None
    assert bt.portfolio_pnl() is not None
    assert bt.portfolio_cum() is not None
    assert bt.components_pnl() is not None
    assert bt.portfolio_leverage() is not None
    assert bt.portfolio_signal() is not None


def test_calculate_trading_pnl_getters(asset_df, signal_df, default_br):
    bt = Backtest()
    bt.calculate_trading_PnL(default_br, asset_df, signal_df, None, False)

    # These will call lazy-calculate methods
    trade_no = bt.portfolio_trade_no()
    assert trade_no is not None

    pnl_cum = bt.pnl_cum()
    assert pnl_cum is not None

    components_cum = bt.components_pnl_cum()
    assert components_cum is not None

    portfolio_trade = bt.portfolio_trade()
    assert portfolio_trade is not None

    total_longs = bt.portfolio_total_longs()
    assert total_longs is not None

    total_shorts = bt.portfolio_total_shorts()
    assert total_shorts is not None

    net_exposure = bt.portfolio_net_exposure()
    assert net_exposure is not None

    total_exposure = bt.portfolio_total_exposure()
    assert total_exposure is not None

    # individual_leverage is None when signal_vol_adjust=False (default)
    bt.individual_leverage()

    components_pnl_ret_stats = bt.components_pnl_ret_stats()
    assert components_pnl_ret_stats is not None

    portfolio_ret_stats = bt.portfolio_pnl_ret_stats()
    assert portfolio_ret_stats is not None

    portfolio_desc = bt.portfolio_pnl_desc()
    assert portfolio_desc is not None

    # These return None when not set
    assert bt.portfolio_total_longs_notional() is None
    assert bt.portfolio_total_shorts_notional() is None
    assert bt.portfolio_net_exposure_notional() is None
    assert bt.portfolio_total_exposure_notional() is None
    assert bt.portfolio_signal_notional() is None
    assert bt.portfolio_trade_notional() is None
    assert bt.portfolio_trade_notional_sizes() is None
    assert bt.portfolio_signal_contracts() is None
    assert bt.portfolio_trade_contracts() is None


def test_pnl_ret_stats(asset_df, signal_df, default_br):
    """Test pnl_ret_stats returns ret stats object."""
    bt = Backtest()
    bt.calculate_trading_PnL(default_br, asset_df, signal_df, None, False)
    result = bt.pnl_ret_stats()
    assert result is not None


def test_pnl_trades_lazy(asset_df, signal_df, default_br):
    bt = Backtest()
    bt.calculate_trading_PnL(default_br, asset_df, signal_df, None, False)

    # pnl_trades is computed lazily
    trades = bt.pnl_trades()
    assert trades is not None


def test_components_pnl_trades_lazy(asset_df, signal_df, default_br):
    bt = Backtest()
    bt.calculate_trading_PnL(default_br, asset_df, signal_df, None, False)

    trades = bt.components_pnl_trades()
    assert trades is not None


def test_trade_no_lazy(asset_df, signal_df, default_br):
    bt = Backtest()
    bt.calculate_trading_PnL(default_br, asset_df, signal_df, None, False)
    trade_no = bt.trade_no()
    assert trade_no is not None


def test_signal_getter(asset_df, signal_df, default_br):
    bt = Backtest()
    bt.calculate_trading_PnL(default_br, asset_df, signal_df, None, False)
    sig = bt.signal()
    assert sig is not None


def test_calculate_trading_pnl_add_cumindex(asset_df, signal_df, default_br):
    """Test with cum_index='add'."""
    default_br.cum_index = "add"
    bt = Backtest()
    bt.calculate_trading_PnL(default_br, asset_df, signal_df, None, False)
    assert bt.portfolio_cum() is not None


# -------------------------------------------------------------------
# TradingModel tests
# -------------------------------------------------------------------


def test_trading_model_init():
    tm = MinimalTradingModel()
    assert tm.br is not None


def test_trading_model_save_load_model():
    tm = MinimalTradingModel()
    buf = io.BytesIO()
    TradingModel.save_model(tm, buf)
    buf.seek(0)
    loaded = TradingModel.load_model(buf)
    assert loaded is not None
    assert isinstance(loaded, MinimalTradingModel)


def test_trading_model_flatten_list():
    tm = MinimalTradingModel()
    result = tm._flatten_list(["a", ["b", "c"], "d"])
    assert result == ["a", "b", "c", "d"]


def test_trading_model_flatten_list_all_strings():
    tm = MinimalTradingModel()
    result = tm._flatten_list(["a", "b", "c"])
    assert result == ["a", "b", "c"]


def test_trading_model_construct_strategy():
    tm = MinimalTradingModel()
    tm.construct_strategy()

    # After construction, these should be populated
    assert tm.strategy_pnl() is not None
    assert tm.strategy_group_pnl() is not None
    assert tm.strategy_group_leverage() is not None


def test_trading_model_construct_strategy_with_br():
    tm = MinimalTradingModel()
    br = tm.load_parameters()
    tm.construct_strategy(br=br)
    assert tm.strategy_pnl() is not None


def test_trading_model_strategy_getters():
    tm = MinimalTradingModel()
    tm.construct_strategy()

    # These all return attributes set in _assign_final_strategy_results
    assert tm.strategy_pnl() is not None
    assert tm.strategy_pnl_ret_stats() is not None
    assert tm.strategy_leverage() is not None
    assert tm.strategy_signal() is not None
    assert tm.strategy_trade() is not None
    assert tm.strategy_components_pnl() is not None
    assert tm.strategy_components_pnl_ret_stats() is not None
    # individual_leverage is None when signal_vol_adjust=False (default)
    tm.individual_leverage()
    assert tm.strategy_total_longs() is not None
    assert tm.strategy_total_shorts() is not None
    assert tm.strategy_net_exposure() is not None
    assert tm.strategy_total_exposure() is not None
    # Notional-scaled are None since portfolio_notional_size is not set
    assert tm.strategy_signal_notional() is None
    assert tm.strategy_trade_notional() is None
    assert tm.strategy_trade_notional_sizes() is None
    assert tm.strategy_signal_contracts() is None
    assert tm.strategy_trade_contracts() is None
    assert tm.strategy_total_longs_notional() is None
    assert tm.strategy_total_shorts_notional() is None
    assert tm.strategy_net_exposure_notional() is None
    assert tm.strategy_total_exposure_notional() is None


def test_trading_model_group_getters():
    tm = MinimalTradingModel()
    tm.construct_strategy()
    assert tm.strategy_group_pnl() is not None
    assert tm.strategy_group_pnl_ret_stats() is not None
    assert tm.strategy_group_benchmark_pnl() is not None
    assert tm.strategy_group_benchmark_pnl_ret_stats() is not None
    assert tm.strategy_group_leverage() is not None
    # These may raise AttributeError when no benchmark/trades configured
    import contextlib

    tm.strategy_group_pnl_trades()
    with contextlib.suppress(AttributeError):
        tm.strategy_benchmark_pnl()  # Not set when include_benchmark=False
    with contextlib.suppress(AttributeError):
        tm.strategy_benchmark_pnl_ret_stats()  # Not set when include_benchmark=False


def test_trading_model_plot_methods_silent():
    """Test plot methods with silent_plot=True."""
    tm = MinimalTradingModel()
    tm.construct_strategy()

    # Plot strategy PnL
    result = tm.plot_strategy_pnl(silent_plot=True)
    assert result is not None

    result = tm.plot_strategy_leverage(silent_plot=True)
    assert result is not None

    result = tm.plot_strategy_group_benchmark_pnl(silent_plot=True)
    assert result is not None

    result = tm.plot_strategy_components_pnl(silent_plot=True)
    assert result is not None

    result = tm.plot_individual_leverage(silent_plot=True)
    assert result is not None


def test_trading_model_strip_dataframe():
    tm = MinimalTradingModel()
    df = pd.DataFrame({"EURUSD.close": [1, 2, 3]})
    result = tm._strip_dataframe(df, None)
    assert result is df

    # With strip string
    result = tm._strip_dataframe(df.copy(), ".close")
    assert "EURUSD" in result.columns

    # With list strip
    df2 = pd.DataFrame({"EURUSD.close.test": [1, 2, 3]})
    result = tm._strip_dataframe(df2, ["."])
    assert "EURUSD" in result.columns[0]


def test_trading_model_grab_signals():
    tm = MinimalTradingModel()
    tm.construct_strategy()

    sig = tm._strategy_signal
    result = tm._grab_signals(sig, date=None)
    assert result is not None

    # With a list of dates
    result = tm._grab_signals(sig, date=[-1, -2, -5])
    assert result is not None

    # With strip
    result = tm._grab_signals(sig, date=None, strip=".close")
    assert result is not None


def test_trading_model_create_style():
    tm = MinimalTradingModel()
    style = tm._create_style("test title", "test file")
    assert style is not None


def test_trading_model_reduce_plot():
    tm = MinimalTradingModel()
    dates = pd.date_range(start="2020-01-01", periods=50, freq="B")
    df = pd.DataFrame(np.random.default_rng(0).normal(0, 1, (50, 1)), index=dates)
    result = tm._reduce_plot(df, reduce_plot=True, resample="B")
    assert result is not None

    # Without reduce
    result = tm._reduce_plot(df, reduce_plot=False)
    assert result is not None


def test_trading_model_construct_strategy_benchmark():
    MinimalTradingModel()
    # construct_strategy_benchmark is not abstract; should return None or something
    # MinimalTradingModel doesn't define it, default from TradingModel base
    # will raise AttributeError because base doesn't have it unless defined
    # Actually TradingModel doesn't define construct_strategy_benchmark as abstract
    # so it'll raise AttributeError; strategy_group_benchmark_pnl uses it
    # after construct_strategy which wraps it


def test_trading_model_name():
    tm = MinimalTradingModel()
    assert tm.strategy_name() == "TestStrategy"


# -------------------------------------------------------------------
# TradingModel additional plot methods
# -------------------------------------------------------------------


def test_trading_model_plot_group_pnl_trades_silent():
    tm = MinimalTradingModel()
    tm.construct_strategy()
    # This method uses _strategy_group_pnl_trades - which gets set in construct
    # It wraps with contextlib.suppress so won't raise
    tm.plot_strategy_group_pnl_trades(silent_plot=True)
    # May be None if data not available


def test_trading_model_plot_strategy_group_benchmark_ir():
    tm = MinimalTradingModel()
    tm.construct_strategy()
    result = tm.plot_strategy_group_benchmark_pnl_ir(silent_plot=True)
    assert result is not None


def test_trading_model_plot_strategy_group_benchmark_returns():
    tm = MinimalTradingModel()
    tm.construct_strategy()
    result = tm.plot_strategy_group_benchmark_pnl_returns(silent_plot=True)
    assert result is not None


def test_trading_model_plot_strategy_group_benchmark_vol():
    tm = MinimalTradingModel()
    tm.construct_strategy()
    result = tm.plot_strategy_group_benchmark_pnl_vol(silent_plot=True)
    assert result is not None


def test_trading_model_plot_strategy_group_benchmark_drawdowns():
    tm = MinimalTradingModel()
    tm.construct_strategy()
    result = tm.plot_strategy_group_benchmark_pnl_drawdowns(silent_plot=True)
    assert result is not None


def test_trading_model_plot_strategy_components_pnl_ir():
    tm = MinimalTradingModel()
    tm.construct_strategy()
    result = tm.plot_strategy_components_pnl_ir(silent_plot=True)
    assert result is not None


def test_trading_model_plot_strategy_components_pnl_returns():
    tm = MinimalTradingModel()
    tm.construct_strategy()
    result = tm.plot_strategy_components_pnl_returns(silent_plot=True)
    assert result is not None


def test_trading_model_plot_strategy_components_pnl_vol():
    tm = MinimalTradingModel()
    tm.construct_strategy()
    result = tm.plot_strategy_components_pnl_vol(silent_plot=True)
    assert result is not None


def test_trading_model_plot_strategy_components_pnl_drawdowns():
    tm = MinimalTradingModel()
    tm.construct_strategy()
    result = tm.plot_strategy_components_pnl_drawdowns(silent_plot=True)
    assert result is not None


def test_trading_model_plot_strategy_signal_proportion():
    tm = MinimalTradingModel()
    tm.construct_strategy()
    tm.plot_strategy_signal_proportion(silent_plot=True)


def test_trading_model_plot_strategy_signal_proportion_with_strip():
    """Test plot_strategy_signal_proportion with strip parameter (lines 1733, 1743)."""
    tm = MinimalTradingModel()
    tm.construct_strategy()
    # Calling with strip exercises line 1733; result may be None if exception is suppressed
    tm.plot_strategy_signal_proportion(silent_plot=True, strip=".close")


def test_trading_model_plot_strategy_all_signals():
    tm = MinimalTradingModel()
    tm.construct_strategy()
    tm.plot_strategy_all_signals(silent_plot=True)


def test_trading_model_plot_strategy_signals():
    tm = MinimalTradingModel()
    tm.construct_strategy()
    result = tm.plot_strategy_signals(silent_plot=True)
    assert result is not None


def test_trading_model_plot_strategy_trades():
    tm = MinimalTradingModel()
    tm.construct_strategy()
    result = tm.plot_strategy_trades(silent_plot=True)
    assert result is not None


def test_trading_model_plot_strategy_trade_no():
    tm = MinimalTradingModel()
    tm.construct_strategy()
    tm.plot_strategy_trade_no(silent_plot=True)


def test_trading_model_plot_strategy_trade_no_with_strip():
    """Test plot_strategy_trade_no with strip parameter (line 1695)."""
    tm = MinimalTradingModel()
    tm.construct_strategy()
    # strip=".close" to exercise strip branch
    tm.plot_strategy_trade_no(silent_plot=True, strip=".close")


def test_trading_model_plot_strategy_group_benchmark_pnl_yoy():
    tm = MinimalTradingModel()
    tm.construct_strategy()
    result = tm.plot_strategy_group_benchmark_pnl_yoy(silent_plot=True)
    assert result is not None


def test_trading_model_plot_strategy_components_pnl_yoy():
    tm = MinimalTradingModel()
    tm.construct_strategy()
    result = tm.plot_strategy_components_pnl_yoy(silent_plot=True)
    assert result is not None


def test_trading_model_plot_strategy_group_leverage():
    tm = MinimalTradingModel()
    tm.construct_strategy()
    result = tm.plot_strategy_group_leverage(silent_plot=True)
    assert result is not None


def test_trading_model_plot_total_exposures():
    tm = MinimalTradingModel()
    tm.construct_strategy()
    tm.plot_strategy_total_exposures(silent_plot=True)


def test_trading_model_plot_net_exposures():
    tm = MinimalTradingModel()
    tm.construct_strategy()
    tm.plot_strategy_net_exposures(silent_plot=True)


def test_trading_model_filter_by_plot_dates_both_none():
    tm = MinimalTradingModel()
    br = tm.load_parameters()
    dates = pd.date_range("2020-01-01", periods=10)
    df = pd.DataFrame(np.ones((10, 1)), index=dates)
    result = tm._filter_by_plot_start_finish_date(df, br)
    assert result is df


def test_trading_model_filter_by_plot_dates_with_dates():
    tm = MinimalTradingModel()
    br = tm.load_parameters()
    br.plot_start = "2020-01-05"
    br.plot_finish = "2020-01-08"
    dates = pd.date_range("2020-01-01", periods=10)
    df = pd.DataFrame(np.ones((10, 1)), index=dates)
    result = tm._filter_by_plot_start_finish_date(df, br)
    assert result is not None


# -------------------------------------------------------------------
# PortfolioWeightConstruction tests
# -------------------------------------------------------------------


def test_portfolio_weight_construction_init():
    br = BacktestRequest()
    pwc = PortfolioWeightConstruction(br=br)
    assert pwc is not None


def test_optimize_portfolio_weights_basic(asset_df, signal_df, default_br):
    from findatapy.timeseries import Calculations

    calcs = Calculations()
    returns_df = calcs.calculate_returns(asset_df)

    # Signal and returns need same columns
    returns_df.columns = ["EURUSD.close"]
    signal_df_aligned = signal_df.copy()
    returns_df_aligned, signal_df_aligned = returns_df.align(signal_df_aligned, join="inner")

    pnl_cols = ["EURUSD.close / EURUSD.close"]

    pwc = PortfolioWeightConstruction(br=default_br)
    result = pwc.optimize_portfolio_weights(returns_df_aligned, signal_df_aligned, pnl_cols)
    assert len(result) == 6


def test_optimize_portfolio_weights_sum_combination(asset_df, signal_df, default_br):
    from findatapy.timeseries import Calculations

    calcs = Calculations()
    returns_df = calcs.calculate_returns(asset_df)
    returns_df.columns = ["EURUSD.close"]
    signal_df_aligned = signal_df.copy()
    returns_df_aligned, signal_df_aligned = returns_df.align(signal_df_aligned, join="inner")
    pnl_cols = ["EURUSD.close / EURUSD.close"]

    default_br.portfolio_combination = "sum"
    pwc = PortfolioWeightConstruction(br=default_br)
    result = pwc.optimize_portfolio_weights(returns_df_aligned, signal_df_aligned, pnl_cols)
    assert len(result) == 6


def test_optimize_portfolio_weights_mean_combination(asset_df, signal_df, default_br):
    from findatapy.timeseries import Calculations

    calcs = Calculations()
    returns_df = calcs.calculate_returns(asset_df)
    returns_df.columns = ["EURUSD.close"]
    signal_df_aligned = signal_df.copy()
    returns_df_aligned, signal_df_aligned = returns_df.align(signal_df_aligned, join="inner")
    pnl_cols = ["EURUSD.close / EURUSD.close"]

    default_br.portfolio_combination = "mean"
    pwc = PortfolioWeightConstruction(br=default_br)
    result = pwc.optimize_portfolio_weights(returns_df_aligned, signal_df_aligned, pnl_cols)
    assert len(result) == 6


def test_calculate_signal_weights_mean(asset_df, signal_df, default_br):
    from findatapy.timeseries import Calculations

    calcs = Calculations()
    returns_df = calcs.calculate_returns(asset_df)
    returns_df.columns = ["EURUSD.close"]
    signal_df_aligned = signal_df.copy()
    returns_df_aligned, signal_df_aligned = returns_df.align(signal_df_aligned, join="inner")
    pnl_cols = ["EURUSD.close / EURUSD.close"]

    pwc = PortfolioWeightConstruction(br=default_br)
    from findatapy.timeseries import Calculations

    calcs = Calculations()
    signal_pnl = calcs.calculate_signal_returns_with_tc_matrix(signal_df_aligned, returns_df_aligned, tc=0)
    signal_pnl.columns = pnl_cols
    weights = pwc.calculate_signal_weights_for_portfolio(default_br, signal_pnl, method="mean")
    assert weights is not None


# -------------------------------------------------------------------
# RiskEngine tests
# -------------------------------------------------------------------


def test_risk_engine_init():
    re = RiskEngine()
    assert re is not None


def test_risk_engine_calculate_leverage_factor():
    re = RiskEngine()
    dates = pd.date_range("2020-01-01", periods=100, freq="B")
    rng = np.random.default_rng(42)
    returns = pd.DataFrame(rng.normal(0, 0.01, (100, 1)), index=dates, columns=["EURUSD"])

    lev = re.calculate_leverage_factor(
        returns,
        vol_target=0.1,
        vol_max_leverage=3.0,
        vol_periods=20,
        vol_obs_in_year=252,
        vol_rebalance_freq="BM",
        resample_freq=None,
        resample_type="mean",
    )
    assert lev is not None


def test_risk_engine_calculate_leverage_factor_with_resample_freq():
    re = RiskEngine()
    dates = pd.date_range("2020-01-01", periods=100, freq="B")
    rng = np.random.default_rng(42)
    returns = pd.DataFrame(rng.normal(0, 0.01, (100, 1)), index=dates, columns=["EURUSD"])

    # resample_freq != None triggers early return
    result = re.calculate_leverage_factor(
        returns,
        vol_target=0.1,
        vol_max_leverage=3.0,
        resample_freq="D",
    )
    assert result is None


def test_risk_engine_calculate_position_clip_adjustment_none():
    re = RiskEngine()
    br = BacktestRequest()
    dates = pd.date_range("2020-01-01", periods=20)
    net = pd.DataFrame(np.ones((20, 1)), index=dates, columns=["Net Exposure"])
    total = pd.DataFrame(np.ones((20, 1)), index=dates, columns=["Total Exposure"])

    result = re.calculate_position_clip_adjustment(net, total, br)
    assert result is None


def test_risk_engine_calculate_vol_adjusted_index(asset_df, default_br):
    re = RiskEngine()
    default_br.portfolio_vol_target = 0.1
    default_br.portfolio_vol_max_leverage = None
    default_br.portfolio_vol_periods = 20
    default_br.portfolio_vol_obs_in_year = 252
    default_br.portfolio_vol_rebalance_freq = "BM"
    default_br.portfolio_vol_resample_freq = None
    default_br.portfolio_vol_resample_type = "mean"
    default_br.portfolio_vol_period_shift = 0
    default_br.cum_index = "mult"

    result = re.calculate_vol_adjusted_index_from_prices(asset_df, default_br)
    assert result is not None


def test_chart_return_with_df_split_on_char():
    """Test _chart_return_with_df with split_on_char."""
    from unittest.mock import patch

    from chartpy import Style

    tm = MinimalTradingModel()
    tm.construct_strategy()

    dates = pd.date_range("2020-01-01", periods=10)
    df = pd.DataFrame(np.ones((10, 1)), index=dates, columns=["EURUSD.close"])
    style = Style()

    # Test with split_on_char
    result = tm._chart_return_with_df(df.copy(), style, silent_plot=True, split_on_char=".")
    assert result is not None

    # Test with ret_with_df=True
    result = tm._chart_return_with_df(df.copy(), style, silent_plot=True, ret_with_df=True)
    assert isinstance(result, tuple)
    assert len(result) == 2

    # Test with silent_plot=False (mock chart.plot)
    with patch("chartpy.chart.Chart.plot", return_value=None):
        result = tm._chart_return_with_df(df.copy(), style, silent_plot=False)
    assert result is not None


def test_chart_return_with_df_split_on_char_non_string_col():
    """Test _chart_return_with_df with non-string column name triggers except branch (lines 1593-1594)."""
    from chartpy import Style

    tm = MinimalTradingModel()
    tm.construct_strategy()

    dates = pd.date_range("2020-01-01", periods=10)
    # Use integer column names so .split() raises AttributeError
    df = pd.DataFrame(np.ones((10, 1)), index=dates, columns=[42])
    style = Style()

    result = tm._chart_return_with_df(df.copy(), style, silent_plot=True, split_on_char=".")
    assert result is not None


def test_risk_engine_calculate_vol_adjusted_index_add(asset_df, default_br):
    re = RiskEngine()
    default_br.portfolio_vol_target = 0.1
    default_br.portfolio_vol_max_leverage = None
    default_br.portfolio_vol_periods = 20
    default_br.portfolio_vol_obs_in_year = 252
    default_br.portfolio_vol_rebalance_freq = "BM"
    default_br.portfolio_vol_resample_freq = None
    default_br.portfolio_vol_resample_type = "mean"
    default_br.portfolio_vol_period_shift = 0
    default_br.cum_index = "add"

    result = re.calculate_vol_adjusted_index_from_prices(asset_df, default_br)
    assert result is not None


def test_risk_engine_calculate_leverage_factor_prices_not_returns():
    """calculate_leverage_factor with returns=False (prices input) exercises line 2822."""
    re = RiskEngine()
    dates = pd.date_range("2020-01-01", periods=100, freq="B")
    rng = np.random.default_rng(42)
    prices = pd.DataFrame(100 + np.cumsum(rng.normal(0, 1, (100, 1)), axis=0), index=dates, columns=["EURUSD"])

    lev = re.calculate_leverage_factor(
        prices,
        vol_target=0.1,
        vol_max_leverage=3.0,
        vol_periods=20,
        vol_obs_in_year=252,
        vol_rebalance_freq="BM",
        resample_freq=None,
        resample_type="mean",
        returns=False,
    )
    assert lev is not None


def test_risk_engine_calculate_position_clip_max_net_exposure():
    """calculate_position_clip_adjustment with max_net_exposure set (lines 2873-2886)."""
    re = RiskEngine()
    br = BacktestRequest()
    br.max_net_exposure = 0.5
    br.position_clip_period_shift = 0
    br.position_clip_rebalance_freq = None

    dates = pd.date_range("2020-01-01", periods=50)
    net = pd.DataFrame(rng_net := np.random.default_rng(1).normal(0, 0.8, (50, 1)), index=dates, columns=["Portfolio"])
    total = pd.DataFrame(np.abs(rng_net), index=dates, columns=["Portfolio"])

    result = re.calculate_position_clip_adjustment(net, total, br)
    assert result is not None


def test_risk_engine_calculate_position_clip_max_abs_exposure():
    """calculate_position_clip_adjustment with max_abs_exposure set (lines 2892-2904)."""
    re = RiskEngine()
    br = BacktestRequest()
    br.max_net_exposure = 0.5
    br.max_abs_exposure = 0.8
    br.position_clip_period_shift = 0
    br.position_clip_rebalance_freq = None

    dates = pd.date_range("2020-01-01", periods=50)
    net = pd.DataFrame(np.random.default_rng(1).normal(0, 0.8, (50, 1)), index=dates, columns=["Portfolio"])
    total = pd.DataFrame(np.abs(np.random.default_rng(1).normal(0, 1.0, (50, 1))), index=dates, columns=["Portfolio"])

    result = re.calculate_position_clip_adjustment(net, total, br)
    assert result is not None


def test_risk_engine_calculate_position_clip_with_rebalance_freq():
    """calculate_position_clip_adjustment with position_clip_rebalance_freq set (lines 2910-2918)."""
    re = RiskEngine()
    br = BacktestRequest()
    br.max_net_exposure = 0.5
    br.position_clip_period_shift = 0
    br.position_clip_rebalance_freq = "BM"
    br.position_clip_resample_type = "last"
    br.max_abs_exposure = None

    dates = pd.date_range("2020-01-01", periods=100, freq="B")
    net = pd.DataFrame(np.random.default_rng(2).normal(0, 0.8, (100, 1)), index=dates, columns=["Portfolio"])
    total = pd.DataFrame(np.abs(net.values), index=dates, columns=["Portfolio"])

    result = re.calculate_position_clip_adjustment(net, total, br)
    assert result is not None


def test_trading_model_plot_strategy_all_signals_with_signal_show():
    """Test plot_strategy_all_signals with signal_show and split_on_char (lines 2125-2134)."""
    tm = MinimalTradingModel()
    tm.construct_strategy()
    # signal_show=["EURUSD"] - EURUSD.close.split(".")[0] == "EURUSD" which IS in list -> column kept
    result = tm.plot_strategy_all_signals(silent_plot=True, signal_show=["EURUSD"], split_on_char=".")
    assert result is not None

    # signal_show=["GBPUSD"] - EURUSD.close.split(".")[0] == "EURUSD" NOT in list -> triggers line 2132
    tm.plot_strategy_all_signals(silent_plot=True, signal_show=["GBPUSD"], split_on_char=".")
    # result2 may be None if all columns were dropped


def test_plot_ret_stats_helper_with_strip():
    """Test _plot_ret_stats_helper with strip argument (line 2012)."""
    tm = MinimalTradingModel()
    tm.construct_strategy()
    # plot_strategy_group_benchmark_ir uses _plot_ret_stats_helper with strip
    result = tm.plot_strategy_group_benchmark_pnl_ir(silent_plot=True, strip=".close")
    assert result is not None


def test_trading_model_plot_strategy_signals_with_strip_times():
    """Test plot_strategy_signals with strip_times=True (lines 2448-2452)."""
    tm = MinimalTradingModel()
    tm.construct_strategy()
    result = tm.plot_strategy_signals(silent_plot=True, strip_times=True)
    assert result is not None


def test_trading_model_plot_strategy_signals_with_date():
    """Test plot_strategy_signals with specific date (line 2406)."""
    tm = MinimalTradingModel()
    tm.construct_strategy()
    result = tm.plot_strategy_signals(silent_plot=True, date=-1)
    assert result is not None


def test_trading_model_create_style_no_reduce_plot():
    """Test _create_style with reduce_plot=False (line 2492)."""
    tm = MinimalTradingModel()
    tm.construct_strategy()
    style = tm._create_style("test", "test_file", reduce_plot=False)
    assert style.plotly_webgl is True


def test_pwc_calculate_signal_weights_weighted_sum():
    """Test calculate_signal_weights_for_portfolio with weighted-sum method (line 2702)."""
    pwc = PortfolioWeightConstruction()
    br = BacktestRequest()
    # Column name in signal_pnl matches pnl_cols format: "asset / signal"
    col = "EURUSD.close / EURUSD.close"
    br.portfolio_combination_weights = {col: 1.5}

    dates = pd.date_range("2020-01-01", periods=20, freq="B")
    signal_pnl = pd.DataFrame(np.random.default_rng(5).normal(0, 0.01, (20, 1)), index=dates, columns=[col])

    result = pwc.calculate_signal_weights_for_portfolio(br, signal_pnl, method="weighted-sum")
    assert result is not None


def test_pwc_calculate_signal_weights_weighted():
    """Test calculate_signal_weights_for_portfolio with weighted method (lines 2676-2678)."""
    pwc = PortfolioWeightConstruction()
    br = BacktestRequest()
    col = "EURUSD.close / EURUSD.close"
    br.portfolio_combination_weights = {col: 2.0}

    dates = pd.date_range("2020-01-01", periods=20, freq="B")
    signal_pnl = pd.DataFrame(np.random.default_rng(5).normal(0, 0.01, (20, 1)), index=dates, columns=[col])

    result = pwc.calculate_signal_weights_for_portfolio(br, signal_pnl, method="weighted-mean")
    assert result is not None


def test_trading_model_plot_notional_methods():
    """Test plot methods requiring _strategy_*_notional attributes (lines 2199, 2222, 2242-2255)."""
    tm = MinimalTradingModel()
    tm.construct_strategy()

    dates = pd.date_range("2020-01-01", periods=100, freq="B")
    notional_df = pd.DataFrame(np.ones((100, 1)), index=dates, columns=["EURUSD.close"])
    notional_sizes_df = pd.DataFrame(
        {"[-0.01, 0)": [5], "[0, 0.01)": [10]},
        index=["EURUSD.close"],
    )

    tm._strategy_signal_notional = notional_df
    tm._strategy_trade_notional = notional_df
    tm._strategy_trade_notional_sizes = notional_sizes_df

    result = tm.plot_strategy_signals_notional(silent_plot=True)
    assert result is not None

    result = tm.plot_strategy_trades_notional(silent_plot=True)
    # May return None if _strategy_trade_notional is None initially; just call it
    result = tm.plot_strategy_trades_notional_sizes(silent_plot=True)
    assert result is not None

    # Call with strip to exercise line 2243
    result = tm.plot_strategy_trades_notional_sizes(silent_plot=True, strip=".close")


def test_trading_model_plot_contracts_methods():
    """Test plot methods requiring _strategy_*_contracts attributes (lines 2270, 2294)."""
    tm = MinimalTradingModel()
    tm.construct_strategy()

    dates = pd.date_range("2020-01-01", periods=100, freq="B")
    contracts_df = pd.DataFrame(np.ones((100, 1)), index=dates, columns=["EURUSD.close"])
    tm._strategy_signal_contracts = contracts_df
    tm._strategy_trade_contracts = contracts_df

    result = tm.plot_strategy_signals_contracts(silent_plot=True)
    assert result is not None

    result = tm.plot_strategy_trades_contracts(silent_plot=True)
    assert result is not None


def test_trading_model_plot_notional_exposure_methods():
    """Test plot methods requiring notional exposure attributes (lines 2358-2372, 2386-2395)."""
    tm = MinimalTradingModel()
    tm.construct_strategy()

    dates = pd.date_range("2020-01-01", periods=100, freq="B")
    exposure_df = pd.DataFrame(np.ones((100, 1)) * 1e6, index=dates, columns=["Portfolio"])

    tm._strategy_total_longs_notional = exposure_df
    tm._strategy_total_shorts_notional = exposure_df * -1
    tm._strategy_total_exposure_notional = exposure_df
    tm._strategy_net_exposure_notional = exposure_df * 0.5

    result = tm.plot_strategy_total_exposures_notional(silent_plot=True)
    assert result is not None

    result = tm.plot_strategy_net_exposures_notional(silent_plot=True)
    assert result is not None


def test_trading_model_construct_strategy_with_signal_vol_adjust():
    """Test construct_strategy with signal_vol_adjust=True (lines 2535-2551)."""

    class SignalVolAdjModel(TradingModel):
        FINAL_STRATEGY = "SignalVolAdjTest"

        def load_parameters(self, br=None):
            new_br = BacktestRequest()
            new_br.start_date = "2020-01-01"
            new_br.finish_date = "2020-06-30"
            new_br.spot_tc_bp = 0.5
            new_br.ann_factor = 252
            new_br.signal_vol_adjust = True
            new_br.signal_vol_target = 0.1
            new_br.signal_vol_max_leverage = 3.0
            new_br.signal_vol_periods = 20
            new_br.signal_vol_obs_in_year = 252
            new_br.signal_vol_rebalance_freq = "BM"
            new_br.signal_vol_resample_freq = None
            new_br.signal_vol_resample_type = "mean"
            new_br.signal_vol_period_shift = 0
            return new_br

        def load_assets(self, br=None):
            dates = pd.date_range(start="2020-01-01", periods=100, freq="B")
            rng = np.random.default_rng(99)
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

    tm = SignalVolAdjModel()
    tm.construct_strategy()
    assert tm is not None
    pnl = tm.strategy_pnl()
    assert pnl is not None


def test_trading_model_construct_strategy_weighted_combination():
    """Test construct_strategy with weighted portfolio combination (lines 2567-2578)."""

    class WeightedCombModel(TradingModel):
        FINAL_STRATEGY = "WeightedCombTest"

        def load_parameters(self, br=None):
            new_br = BacktestRequest()
            new_br.start_date = "2020-01-01"
            new_br.finish_date = "2020-06-30"
            new_br.spot_tc_bp = 0.5
            new_br.ann_factor = 252
            new_br.portfolio_combination = "weighted-mean"
            # pnl_cols format: asset_col + " / " + signal_col
            new_br.portfolio_combination_weights = {"EURUSD.close / EURUSD.close": 2.0}
            return new_br

        def load_assets(self, br=None):
            dates = pd.date_range(start="2020-01-01", periods=100, freq="B")
            rng = np.random.default_rng(77)
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

    tm = WeightedCombModel()
    tm.construct_strategy()
    assert tm is not None
    pnl = tm.strategy_pnl()
    assert pnl is not None


def test_trading_model_construct_strategy_portfolio_vol_adjust():
    """Test construct_strategy with portfolio_vol_adjust=True (line 2592)."""

    class PortVolAdjModel(TradingModel):
        FINAL_STRATEGY = "PortVolAdjTest"

        def load_parameters(self, br=None):
            new_br = BacktestRequest()
            new_br.start_date = "2020-01-01"
            new_br.finish_date = "2020-06-30"
            new_br.spot_tc_bp = 0.5
            new_br.ann_factor = 252
            new_br.portfolio_vol_adjust = True
            new_br.portfolio_vol_target = 0.1
            new_br.portfolio_vol_max_leverage = 3.0
            new_br.portfolio_vol_periods = 20
            new_br.portfolio_vol_obs_in_year = 252
            new_br.portfolio_vol_rebalance_freq = "BM"
            new_br.portfolio_vol_resample_freq = None
            new_br.portfolio_vol_resample_type = "mean"
            new_br.portfolio_vol_period_shift = 0
            return new_br

        def load_assets(self, br=None):
            dates = pd.date_range(start="2020-01-01", periods=100, freq="B")
            rng = np.random.default_rng(88)
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

    tm = PortVolAdjModel()
    tm.construct_strategy()
    assert tm is not None
    pnl = tm.strategy_pnl()
    assert pnl is not None
