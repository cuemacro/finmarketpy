"""Tests for QuickChart."""

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from finmarketpy.economics.quickchart import QuickChart


@pytest.fixture
def sample_df():
    """A sample DataFrame for chart tests."""
    rng = np.random.default_rng(42)
    dates = pd.date_range("2020-01-01", periods=50, freq="B")
    df = pd.DataFrame(
        100 + np.cumsum(rng.normal(0, 1, (50, 1)), axis=0),
        index=dates,
        columns=["EURUSD.close"],
    )
    return df


def test_quickchart_init():
    """Test QuickChart instantiation."""
    qc = QuickChart(engine="plotly", data_source="quandl")
    assert qc is not None
    assert qc._data_source == "quandl"


def test_quickchart_init_with_mock_generator():
    """Test QuickChart with a mocked market data generator."""
    mock_gen = MagicMock()
    qc = QuickChart(engine="plotly", data_source="bloomberg", market_data_generator=mock_gen)
    assert qc is not None


def test_plot_chart_with_df(sample_df):
    """Test plot_chart with a DataFrame provided directly."""
    qc = QuickChart(engine="plotly", data_source="bloomberg")
    with patch.object(qc._chart, "plot", return_value=None) as mock_plot:
        _result_chart, result_df = qc.plot_chart(
            tickers=None,
            df=sample_df,
            plotly_plot_mode="offline_html_exc_embed_js",
        )
        mock_plot.assert_called_once()
    assert result_df is not None


def test_plot_chart_with_tickers_string(sample_df):
    """Test plot_chart with a string ticker, df provided."""
    qc = QuickChart(engine="plotly", data_source="bloomberg")
    with patch.object(qc._chart, "plot", return_value=None):
        _result_chart, result_df = qc.plot_chart(
            tickers="EURUSD",
            df=sample_df,
            plotly_plot_mode="offline_html_exc_embed_js",
        )
    assert result_df is not None


def test_plot_chart_with_tickers_list(sample_df):
    """Test plot_chart with a list of tickers, df provided."""
    qc = QuickChart(engine="plotly", data_source="bloomberg")
    with patch.object(qc._chart, "plot", return_value=None):
        _result_chart, result_df = qc.plot_chart(
            tickers=["EURUSD"],
            df=sample_df,
            plotly_plot_mode="offline_html_exc_embed_js",
        )
    assert result_df is not None


def test_plot_chart_reindex(sample_df):
    """Test plot_chart with reindex=True."""
    qc = QuickChart(engine="plotly", data_source="bloomberg")
    with patch.object(qc._chart, "plot", return_value=None):
        _result_chart, result_df = qc.plot_chart(
            df=sample_df,
            reindex=True,
            plotly_plot_mode="offline_html_exc_embed_js",
        )
    assert result_df is not None


def test_plot_chart_additive_index(sample_df):
    """Test plot_chart with additive_index=True."""
    qc = QuickChart(engine="plotly", data_source="bloomberg")
    with patch.object(qc._chart, "plot", return_value=None):
        _result_chart, result_df = qc.plot_chart(
            df=sample_df,
            additive_index=True,
            plotly_plot_mode="offline_html_exc_embed_js",
        )
    assert result_df is not None


def test_plot_chart_yoy_daily(sample_df):
    """Test plot_chart with yoy=True and freq='daily'."""
    qc = QuickChart(engine="plotly", data_source="bloomberg")
    with patch.object(qc._chart, "plot", return_value=None):
        _result_chart, result_df = qc.plot_chart(
            df=sample_df,
            yoy=True,
            freq="daily",
            plotly_plot_mode="offline_html_exc_embed_js",
        )
    assert result_df is not None


def test_plot_chart_yoy_intraday():
    """Test plot_chart with yoy=True and freq='intraday'."""
    rng = np.random.default_rng(42)
    dates = pd.date_range("2020-01-01", periods=100, freq="1min")
    df = pd.DataFrame(
        100 + np.cumsum(rng.normal(0, 0.01, (100, 1)), axis=0),
        index=dates,
        columns=["EURUSD.close"],
    )
    qc = QuickChart(engine="plotly", data_source="bloomberg")
    with patch.object(qc._chart, "plot", return_value=None):
        _result_chart, result_df = qc.plot_chart(
            df=df,
            yoy=True,
            freq="intraday",
            plotly_plot_mode="offline_html_exc_embed_js",
        )
    assert result_df is not None


def test_plot_chart_with_rhs_ticker(sample_df):
    """Test plot_chart with tickers_rhs dict - tickers must also be a dict when using tickers_rhs."""
    qc = QuickChart(engine="plotly", data_source="bloomberg")
    with patch.object(qc._chart, "plot", return_value=None):
        _result_chart, result_df = qc.plot_chart(
            df=sample_df,
            tickers={"EURUSD": "EURUSD"},
            tickers_rhs={"GBPUSD": "GBPUSD"},
            plotly_plot_mode="offline_html_exc_embed_js",
        )
    assert result_df is not None


def test_plot_chart_with_rhs_ticker_string(sample_df):
    """Test plot_chart with tickers_rhs string - tickers must also be provided."""
    qc = QuickChart(engine="plotly", data_source="bloomberg")
    with patch.object(qc._chart, "plot", return_value=None):
        _result_chart, result_df = qc.plot_chart(
            df=sample_df,
            tickers={"EURUSD": "EURUSD"},
            tickers_rhs="GBPUSD",
            plotly_plot_mode="offline_html_exc_embed_js",
        )
    assert result_df is not None


def test_plot_chart_with_ret_stats(sample_df):
    """Test plot_chart_with_ret_stats."""
    qc = QuickChart(engine="plotly", data_source="bloomberg")
    with patch.object(qc._chart, "plot", return_value=None):
        _result_chart, result_df = qc.plot_chart_with_ret_stats(
            df=sample_df,
            plotly_plot_mode="offline_html_exc_embed_js",
        )
    assert result_df is not None
