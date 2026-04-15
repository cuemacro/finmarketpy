"""Tests for Seasonality."""
# ruff: noqa: D103

import numpy as np
import pandas as pd
import pytest

from finmarketpy.economics.seasonality import Seasonality


@pytest.fixture
def returns_df():
    """Create a simple daily returns DataFrame."""
    rng = np.random.default_rng(42)
    dates = pd.date_range(start="2015-01-01", end="2022-12-31", freq="B")
    data = rng.normal(0, 0.01, (len(dates), 1))
    df = pd.DataFrame(data, index=dates, columns=["Asset"])
    return df


@pytest.fixture
def prices_df():
    """Create a simple daily prices DataFrame."""
    rng = np.random.default_rng(42)
    dates = pd.date_range(start="2015-01-01", end="2022-12-31", freq="B")
    prices = 100 + np.cumsum(rng.normal(0, 0.5, (len(dates), 1)), axis=0)
    df = pd.DataFrame(prices, index=dates, columns=["Asset"])
    return df


def test_seasonality_init():
    s = Seasonality()
    assert s is not None


def test_monthly_seasonality(returns_df):
    s = Seasonality()
    result = s.monthly_seasonality(returns_df)
    assert result is not None
    assert isinstance(result, pd.DataFrame)


def test_monthly_seasonality_no_cum(returns_df):
    s = Seasonality()
    result = s.monthly_seasonality(returns_df, cum=False)
    assert result is not None
    # Should have 12 rows (one per month)
    assert result.shape[0] == 12


def test_monthly_seasonality_add_average(returns_df):
    s = Seasonality()
    result = s.monthly_seasonality(returns_df, add_average=True, cum=False)
    assert "Avg" in result.columns


def test_monthly_seasonality_from_prices(prices_df):
    s = Seasonality()
    result = s.monthly_seasonality_from_prices(prices_df)
    assert result is not None


def test_bus_day_of_month_seasonality(returns_df):
    s = Seasonality()
    result = s.bus_day_of_month_seasonality(returns_df, month_list=[1, 2, 3], cum=False)
    assert result is not None


def test_bus_day_of_month_seasonality_cum(returns_df):
    s = Seasonality()
    result = s.bus_day_of_month_seasonality(returns_df, month_list=[1, 2], cum=True)
    assert result is not None


def test_bus_day_of_month_seasonality_add_average(returns_df):
    s = Seasonality()
    result = s.bus_day_of_month_seasonality(returns_df, month_list=[1, 2, 3], cum=False, add_average=True)
    assert result is not None


def test_time_of_day_seasonality_no_years():
    """Test time_of_day_seasonality - no years argument (seconds=False)."""
    s = Seasonality()
    rng = np.random.default_rng(42)
    dates = pd.date_range(start="2020-01-01", periods=100, freq="1h")
    df = pd.DataFrame(rng.normal(0, 0.01, (100, 1)), index=dates, columns=["Asset"])
    result = s.time_of_day_seasonality(df, years=False, seconds=False)
    assert result is not None


def test_time_of_day_seasonality_with_years():
    """Test time_of_day_seasonality with years=True."""
    s = Seasonality()
    rng = np.random.default_rng(42)
    # Use multiple years
    dates = pd.date_range(start="2020-01-01", end="2021-12-31", freq="1h")
    df = pd.DataFrame(rng.normal(0, 0.01, (len(dates), 1)), index=dates, columns=["Asset"])
    result = s.time_of_day_seasonality(df, years=True, seconds=False)
    assert result is not None


def test_time_of_day_seasonality_seconds():
    """Test time_of_day_seasonality with seconds=True."""
    s = Seasonality()
    rng = np.random.default_rng(42)
    dates = pd.date_range(start="2020-01-01", periods=60, freq="1min")
    df = pd.DataFrame(rng.normal(0, 0.01, (60, 1)), index=dates, columns=["Asset"])
    result = s.time_of_day_seasonality(df, years=False, seconds=True)
    assert result is not None


def test_bus_day_seasonality_calendar_days(returns_df):
    """Test bus_day_of_month_seasonality with calendar days."""
    s = Seasonality()
    result = s.bus_day_of_month_seasonality(returns_df, month_list=[1, 2, 3], cum=False, resample_freq="D")
    assert result is not None


def test_bus_day_no_partition(returns_df):
    """Test bus_day_of_month_seasonality with partition_by_month=False."""
    s = Seasonality()
    result = s.bus_day_of_month_seasonality(returns_df, month_list=[1, 2, 3], cum=False, partition_by_month=False)
    assert result is not None


def test_time_of_day_seasonality_seconds_with_years():
    """Test time_of_day_seasonality with years=True and seconds=True (line 57)."""
    s = Seasonality()
    rng = np.random.default_rng(42)
    dates = pd.date_range(start="2020-01-01", end="2021-12-31", freq="1min")
    df = pd.DataFrame(rng.normal(0, 0.01, (len(dates), 1)), index=dates, columns=["Asset"])
    result = s.time_of_day_seasonality(df, years=True, seconds=True)
    assert result is not None


def test_bus_day_of_month_seasonality_default_month_list(returns_df):
    """Test bus_day_of_month_seasonality with month_list=None to hit default (line 112)."""
    s = Seasonality()
    result = s.bus_day_of_month_seasonality(returns_df, month_list=None, cum=False)
    assert result is not None


def test_bus_day_of_month_seasonality_price_index(prices_df):
    """Test bus_day_of_month_seasonality with price_index=True (lines 117-118)."""
    s = Seasonality()
    result = s.bus_day_of_month_seasonality(prices_df, month_list=[1, 2, 3], cum=False, price_index=True)
    assert result is not None
