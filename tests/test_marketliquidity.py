"""Tests for MarketLiquidity."""
# ruff: noqa: D103

import numpy as np
import pandas as pd
import pytest

from finmarketpy.economics.marketliquidity import MarketLiquidity


@pytest.fixture
def bid_ask_df():
    """Create a simple bid/ask DataFrame."""
    rng = np.random.default_rng(42)
    dates = pd.date_range("2020-01-01", periods=100, freq="1h")
    mid = 1.1 + rng.normal(0, 0.001, (100,))
    spread = 0.0001
    data = {
        "EURUSD.bid": mid - spread / 2,
        "EURUSD.ask": mid + spread / 2,
    }
    return pd.DataFrame(data, index=dates)


def test_market_liquidity_init():
    ml = MarketLiquidity()
    assert ml is not None
    assert ml.logger is not None


def test_calculate_spreads_single_asset_string(bid_ask_df):
    ml = MarketLiquidity()
    result = ml.calculate_spreads(bid_ask_df, "EURUSD")
    assert result is not None
    assert "EURUSD.spread" in result.columns
    # Spread should be approximately 0.0001
    assert abs(result["EURUSD.spread"].mean() - 0.0001) < 0.0001


def test_calculate_spreads_list_of_assets(bid_ask_df):
    ml = MarketLiquidity()
    result = ml.calculate_spreads(bid_ask_df, ["EURUSD"])
    assert result is not None
    assert "EURUSD.spread" in result.columns


def test_calculate_spreads_custom_fields():
    """Test with custom bid/ask field names."""
    ml = MarketLiquidity()
    dates = pd.date_range("2020-01-01", periods=10)
    df = pd.DataFrame(
        {
            "EURUSD.offer": [1.1001] * 10,
            "EURUSD.mid": [1.1000] * 10,
        },
        index=dates,
    )
    result = ml.calculate_spreads(df, "EURUSD", bid_field="mid", ask_field="offer")
    assert result is not None
