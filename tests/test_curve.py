"""Tests for curve modules (abstractcurve, abstractpricer, fxspotcurve, volstats, abstractvolsurface)."""

from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

# ---- AbstractPricer ----


def test_abstract_pricer_init():
    """AbstractPricer can be instantiated with and without market_df."""
    from finmarketpy.curve.abstractpricer import AbstractPricer

    ap = AbstractPricer()
    assert ap._market_df is None

    df = pd.DataFrame({"col": [1, 2, 3]})
    ap2 = AbstractPricer(market_df=df)
    assert ap2._market_df is not None


def test_abstract_pricer_price_instrument():
    """AbstractPricer.price_instrument returns None (placeholder)."""
    from finmarketpy.curve.abstractpricer import AbstractPricer

    ap = AbstractPricer()
    result = ap.price_instrument()
    assert result is None


# ---- AbstractCurve (via FXSpotCurve concrete implementation) ----


def test_fxspotcurve_init():
    """FXSpotCurve can be instantiated with defaults."""
    from finmarketpy.curve.fxspotcurve import FXSpotCurve

    fc = FXSpotCurve()
    assert fc is not None
    assert fc._depo_tenor == "ON"
    assert fc._field == "close"


def test_fxspotcurve_init_custom():
    """FXSpotCurve can be instantiated with custom arguments."""
    from finmarketpy.curve.fxspotcurve import FXSpotCurve

    mock_gen = MagicMock()
    fc = FXSpotCurve(
        market_data_generator=mock_gen,
        depo_tenor="1W",
        construct_via_currency="USD",
        output_calculation_fields=True,
        field="bid",
    )
    assert fc._market_data_generator is mock_gen
    assert fc._depo_tenor == "1W"
    assert fc._construct_via_currency == "USD"
    assert fc._output_calculation_fields is True
    assert fc._field == "bid"


def test_fxspotcurve_generate_key():
    """FXSpotCurve.generate_key returns a non-None string."""
    from finmarketpy.curve.fxspotcurve import FXSpotCurve

    fc = FXSpotCurve()
    key = fc.generate_key()
    assert key is not None


def test_fxspotcurve_get_day_count_conv_365():
    """get_day_count_conv returns 365 for AUD, CAD, GBP, NZD."""
    from finmarketpy.curve.fxspotcurve import FXSpotCurve

    fc = FXSpotCurve()
    for ccy in ["AUD", "CAD", "GBP", "NZD"]:
        assert fc.get_day_count_conv(ccy) == 365.0


def test_fxspotcurve_get_day_count_conv_360():
    """get_day_count_conv returns 360 for EUR, USD, JPY."""
    from finmarketpy.curve.fxspotcurve import FXSpotCurve

    fc = FXSpotCurve()
    for ccy in ["EUR", "USD", "JPY"]:
        assert fc.get_day_count_conv(ccy) == 360.0


def test_fxspotcurve_unhedged_asset_fx_returns_none():
    """unhedged_asset_fx placeholder returns None."""
    from finmarketpy.curve.fxspotcurve import FXSpotCurve

    fc = FXSpotCurve()
    result = fc.unhedged_asset_fx(None, None, None, None, None)
    assert result is None


def test_fxspotcurve_hedged_asset_fx_returns_none():
    """hedged_asset_fx placeholder returns None."""
    from finmarketpy.curve.fxspotcurve import FXSpotCurve

    fc = FXSpotCurve()
    result = fc.hedged_asset_fx(None, None, None, None, None)
    assert result is None


def test_fxspotcurve_construct_total_return_index_usdusd():
    """construct_total_return_index with USDUSD returns a 100-based index."""
    from finmarketpy.curve.fxspotcurve import FXSpotCurve

    fc = FXSpotCurve()
    dates = pd.date_range("2020-01-01", periods=10, freq="B")
    market_df = pd.DataFrame(
        {
            "USDON.close": [0.01] * 10,
        },
        index=dates,
    )
    result = fc.construct_total_return_index("USDUSD", market_df)
    assert result is not None
    assert "USDUSD-tot.close" in result.columns
    assert (result["USDUSD-tot.close"] == 100).all()


def test_fxspotcurve_construct_total_return_index_eurusd():
    """construct_total_return_index with EURUSD creates expected output."""
    from finmarketpy.curve.fxspotcurve import FXSpotCurve

    fc = FXSpotCurve(depo_tenor="ON")
    dates = pd.date_range("2020-01-01", periods=20, freq="B")
    np.random.seed(42)
    market_df = pd.DataFrame(
        {
            "EURUSD.close": 1.10 + np.cumsum(np.random.normal(0, 0.001, 20)),
            "EURON.close": [0.005] * 20,  # 0.5% base deposit
            "USDON.close": [0.025] * 20,  # 2.5% terms deposit
        },
        index=dates,
    )
    result = fc.construct_total_return_index("EURUSD", market_df)
    assert result is not None
    assert "EURUSD-tot.close" in result.columns
    assert result["EURUSD-tot.close"].iloc[0] == pytest.approx(100.0)


def test_fxspotcurve_construct_total_return_index_output_fields():
    """construct_total_return_index with output_calculation_fields=True adds extra columns."""
    from finmarketpy.curve.fxspotcurve import FXSpotCurve

    fc = FXSpotCurve(depo_tenor="ON", output_calculation_fields=True)
    dates = pd.date_range("2020-01-01", periods=20, freq="B")
    np.random.seed(0)
    market_df = pd.DataFrame(
        {
            "EURUSD.close": 1.10 + np.cumsum(np.random.normal(0, 0.001, 20)),
            "EURON.close": [0.005] * 20,
            "USDON.close": [0.025] * 20,
        },
        index=dates,
    )
    result = fc.construct_total_return_index("EURUSD", market_df)
    assert "EURUSD-carry.close" in result.columns
    assert "EURUSD-tot-return.close" in result.columns
    assert "EURUSD-spot-return.close" in result.columns


def test_fxspotcurve_construct_total_return_index_list():
    """construct_total_return_index with list of crosses."""
    from finmarketpy.curve.fxspotcurve import FXSpotCurve

    fc = FXSpotCurve(depo_tenor="ON")
    dates = pd.date_range("2020-01-01", periods=20, freq="B")
    np.random.seed(7)
    market_df = pd.DataFrame(
        {
            "EURUSD.close": 1.10 + np.cumsum(np.random.normal(0, 0.001, 20)),
            "GBPUSD.close": 1.28 + np.cumsum(np.random.normal(0, 0.001, 20)),
            "EURON.close": [0.005] * 20,
            "USDON.close": [0.025] * 20,
            "GBPON.close": [0.008] * 20,
        },
        index=dates,
    )
    result = fc.construct_total_return_index(["EURUSD", "GBPUSD"], market_df)
    assert "EURUSD-tot.close" in result.columns
    assert "GBPUSD-tot.close" in result.columns


# ---- curve __init__.py (imports) ----


def test_curve_package_imports():
    """Curve package exposes AbstractCurve, FXForwardsCurve, FXSpotCurve."""
    from finmarketpy.curve import AbstractCurve, FXForwardsCurve, FXSpotCurve

    assert AbstractCurve is not None
    assert FXForwardsCurve is not None
    assert FXSpotCurve is not None


# ---- VolStats ----


def test_volstats_init():
    """VolStats can be instantiated."""
    from finmarketpy.curve.volatility.volstats import VolStats

    vs = VolStats()
    assert vs is not None
    assert vs._market_df is None


def test_volstats_init_with_data():
    """VolStats can be instantiated with market_df."""
    from finmarketpy.curve.volatility.volstats import VolStats

    df = pd.DataFrame({"EURUSDVON.close": [5.0] * 20})
    vs = VolStats(market_df=df)
    assert vs._market_df is not None


def test_volstats_calculate_realized_vol_daily():
    """calculate_realized_vol with daily frequency returns expected output."""
    from finmarketpy.curve.volatility.volstats import VolStats

    rng = np.random.default_rng(42)
    dates = pd.date_range("2019-01-01", periods=300, freq="B")
    spot = 1.10 + np.cumsum(rng.normal(0, 0.001, 300))
    market_df = pd.DataFrame({"EURUSD.close": spot}, index=dates)

    vs = VolStats(market_df=market_df)
    result = vs.calculate_realized_vol("EURUSD", tenor_label="1M", freq="daily")
    assert result is not None
    assert isinstance(result, pd.DataFrame)
    assert "EURUSDH1M.close" in result.columns


def test_volstats_calculate_realized_vol_with_spot_df():
    """calculate_realized_vol with spot_df argument."""
    from finmarketpy.curve.volatility.volstats import VolStats

    rng = np.random.default_rng(0)
    dates = pd.date_range("2019-01-01", periods=300, freq="B")
    spot = pd.Series(1.10 + np.cumsum(rng.normal(0, 0.001, 300)), index=dates, name="EURUSD.close")

    vs = VolStats()
    result = vs.calculate_realized_vol("EURUSD", spot_df=spot, tenor_label="ON", freq="daily")
    assert result is not None
    assert "EURUSDH ON.close" in result.columns or "EURUSDHON.close" in result.columns


def test_volstats_calculate_realized_vol_with_explicit_spot():
    """calculate_realized_vol with spot_df passed explicitly (independent of market_df)."""
    from finmarketpy.curve.volatility.volstats import VolStats

    rng = np.random.default_rng(1)
    dates = pd.date_range("2019-01-01", periods=300, freq="B")
    spot = 1.10 + np.cumsum(rng.normal(0, 0.001, 300))
    spot_series = pd.Series(spot, index=dates, name="EURUSD.close")

    vs = VolStats()
    result = vs.calculate_realized_vol("EURUSD", spot_df=spot_series, tenor_label="1M", freq="daily")
    assert result is not None
    assert "EURUSDH1M.close" in result.columns


def test_volstats_calculate_vol_risk_premium():
    """calculate_vol_risk_premium returns expected vrp DataFrame."""
    from finmarketpy.curve.volatility.volstats import VolStats

    rng = np.random.default_rng(5)
    dates = pd.date_range("2019-01-01", periods=300, freq="B")

    implied_vol = pd.DataFrame(
        {"EURUSDVON.close": 6.0 + rng.normal(0, 0.5, 300)},
        index=dates,
    )
    realized_vol = pd.DataFrame(
        {"EURUSDHON.close": 5.5 + rng.normal(0, 0.5, 300)},
        index=dates,
    )

    vs = VolStats()
    result = vs.calculate_vol_risk_premium(
        "EURUSD", tenor_label="ON", implied_vol=implied_vol, realized_vol=realized_vol
    )
    assert result is not None
    assert "EURUSDVRPON.close" in result.columns


def test_volstats_calculate_vol_risk_premium_adj_friday():
    """calculate_vol_risk_premium with adj_ON_friday=True."""
    from finmarketpy.curve.volatility.volstats import VolStats

    rng = np.random.default_rng(6)
    dates = pd.date_range("2019-01-01", periods=300, freq="B")

    implied_vol = pd.DataFrame(
        {"EURUSDVON.close": 6.0 + rng.normal(0, 0.5, 300)},
        index=dates,
    )
    realized_vol = pd.DataFrame(
        {"EURUSDHON.close": 5.5 + rng.normal(0, 0.5, 300)},
        index=dates,
    )

    vs = VolStats()
    result = vs.calculate_vol_risk_premium(
        "EURUSD", tenor_label="ON", implied_vol=implied_vol, realized_vol=realized_vol, adj_ON_friday=True
    )
    assert result is not None


def test_volstats_calculate_implied_vol_addon_weighted_median():
    """calculate_implied_vol_addon with weighted-median-model."""
    from finmarketpy.curve.volatility.volstats import VolStats

    rng = np.random.default_rng(7)
    dates = pd.date_range("2019-01-01", periods=100, freq="B")
    implied_vol = pd.DataFrame(
        {"EURUSDVON.close": 6.0 + rng.normal(0, 0.3, 100)},
        index=dates,
    )

    vs = VolStats()
    result = vs.calculate_implied_vol_addon(
        "EURUSD", implied_vol=implied_vol, tenor_label="ON", model_algo="weighted-median-model"
    )
    assert result is not None
    assert "EURUSDADDON.close" in result.columns


def test_volstats_calculate_implied_vol_addon_weighted_mean():
    """calculate_implied_vol_addon with weighted-mean-model."""
    from finmarketpy.curve.volatility.volstats import VolStats

    rng = np.random.default_rng(8)
    dates = pd.date_range("2019-01-01", periods=100, freq="B")
    implied_vol = pd.DataFrame(
        {"EURUSDVON.close": 6.0 + rng.normal(0, 0.3, 100)},
        index=dates,
    )

    vs = VolStats()
    result = vs.calculate_implied_vol_addon(
        "EURUSD", implied_vol=implied_vol, tenor_label="ON", model_algo="weighted-mean-model"
    )
    assert result is not None


def test_volstats_calculate_implied_vol_addon_from_market_df():
    """calculate_implied_vol_addon fetches implied_vol from market_df when not provided (line 252)."""
    from finmarketpy.curve.volatility.volstats import VolStats

    rng = np.random.default_rng(9)
    dates = pd.date_range("2019-01-01", periods=100, freq="B")
    # The key is asset + "V" + tenor_label + "." + field = "EURUSD" + "V" + "ON" + "." + "close"
    market_df = pd.DataFrame(
        {"EURUSDVON.close": 6.0 + rng.normal(0, 0.3, 100)},
        index=dates,
    )

    vs = VolStats(market_df=market_df)
    result = vs.calculate_implied_vol_addon(
        "EURUSD", tenor_label="ON", implied_vol=None, model_algo="weighted-median-model"
    )
    assert result is not None
    assert "EURUSDADDON.close" in result.columns


def test_volstats_adjust_implied_on_fri_vol():
    """adjust_implied_ON_fri_vol multiplies Friday values by sqrt(3)."""
    import math

    from finmarketpy.curve.volatility.volstats import VolStats

    vs = VolStats()
    # Use a full week range (Mon-Fri)
    dates = pd.date_range("2020-01-06", periods=5, freq="B")  # Mon Jan 6 to Fri Jan 10
    df = pd.DataFrame({"EURUSDVON.close": [6.0, 6.0, 6.0, 6.0, 6.0]}, index=dates)
    result = vs.adjust_implied_ON_fri_vol(df.copy())
    # Friday is weekday 4
    fri_val = result.loc[result.index.dayofweek == 4, "EURUSDVON.close"]
    assert len(fri_val) == 1
    assert abs(fri_val.iloc[0] - 6.0 * math.sqrt(3)) < 1e-10


# ---- AbstractVolSurface ----


def test_abstractvolsurface_extremes_initial_none():
    """_extremes initializes min/max from data when both are None."""
    from finmarketpy.curve.volatility.abstractvolsurface import AbstractVolSurface

    # Create a concrete subclass to test non-abstract method
    class ConcreteVolSurface(AbstractVolSurface):
        def build_vol_surface(self):
            pass

        def extract_vol_surface(self):
            pass

    avs = ConcreteVolSurface()
    data = np.array([1.0, 5.0, 3.0])
    min_v, max_v = avs._extremes(None, None, data)
    assert min_v == 1.0
    assert max_v == 5.0


def test_abstractvolsurface_extremes_updates_min():
    """_extremes updates min when new data has smaller value."""
    from finmarketpy.curve.volatility.abstractvolsurface import AbstractVolSurface

    class ConcreteVolSurface(AbstractVolSurface):
        def build_vol_surface(self):
            pass

        def extract_vol_surface(self):
            pass

    avs = ConcreteVolSurface()
    data = np.array([0.5, 3.0])
    min_v, max_v = avs._extremes(1.0, 5.0, data)
    assert min_v == 0.5
    assert max_v == 5.0


def test_abstractvolsurface_extremes_updates_max():
    """_extremes updates max when new data has larger value."""
    from finmarketpy.curve.volatility.abstractvolsurface import AbstractVolSurface

    class ConcreteVolSurface(AbstractVolSurface):
        def build_vol_surface(self):
            pass

        def extract_vol_surface(self):
            pass

    avs = ConcreteVolSurface()
    data = np.array([2.0, 8.0])
    min_v, max_v = avs._extremes(1.0, 5.0, data)
    assert min_v == 1.0
    assert max_v == 8.0


def test_abstractvolsurface_extremes_no_change():
    """_extremes does not change min/max when data falls within existing range."""
    from finmarketpy.curve.volatility.abstractvolsurface import AbstractVolSurface

    class ConcreteVolSurface(AbstractVolSurface):
        def build_vol_surface(self):
            pass

        def extract_vol_surface(self):
            pass

    avs = ConcreteVolSurface()
    data = np.array([2.0, 4.0])
    min_v, max_v = avs._extremes(1.0, 5.0, data)
    assert min_v == 1.0
    assert max_v == 5.0


def test_abstractvolsurface_extract_across_dates():
    """extract_vol_surface_across_dates calls build/extract for each date."""
    from finmarketpy.curve.volatility.abstractvolsurface import AbstractVolSurface

    class ConcreteVolSurface(AbstractVolSurface):
        def __init__(self):
            self.build_called = []
            self.extract_called = []

        def build_vol_surface(self, date=None):
            self.build_called.append(date)

        def extract_vol_surface(self, num_strike_intervals=60):
            # Return a dict with the expected key
            data = pd.DataFrame(
                np.ones((5, 3)),
                index=np.linspace(0.8, 1.2, 5),
                columns=["1W", "1M", "3M"],
            )
            return {"vol_surface_strike_space": data}

    avs = ConcreteVolSurface()
    import datetime

    dates = [datetime.date(2020, 1, 2), datetime.date(2020, 1, 3)]
    vol_dict, extremes = avs.extract_vol_surface_across_dates(dates)
    assert len(vol_dict) == 2
    assert len(avs.build_called) == 2
    assert extremes["min_x"] is not None


def test_abstractvolsurface_extract_across_dates_no_reverse():
    """extract_vol_surface_across_dates with reverse_plot=False (line 84)."""
    from finmarketpy.curve.volatility.abstractvolsurface import AbstractVolSurface

    class ConcreteVolSurface(AbstractVolSurface):
        def __init__(self):
            pass

        def build_vol_surface(self, date=None):
            pass

        def extract_vol_surface(self, num_strike_intervals=60):
            data = pd.DataFrame(
                np.ones((5, 3)),
                index=np.linspace(0.8, 1.2, 5),
                columns=["1W", "1M", "3M"],
            )
            return {"vol_surface_strike_space": data}

    avs = ConcreteVolSurface()
    import datetime

    dates = [datetime.date(2020, 1, 2)]
    vol_dict, extremes = avs.extract_vol_surface_across_dates(dates, reverse_plot=False)
    assert len(vol_dict) == 1
    assert extremes["min_x"] is not None


# ---- FXForwardsCurve init ----


def test_fxforwardscurve_init():
    """FXForwardsCurve can be instantiated with defaults."""
    from finmarketpy.curve.fxforwardscurve import FXForwardsCurve

    fc = FXForwardsCurve()
    assert fc is not None
    assert fc._fx_forwards_trading_tenor == "1M"


def test_fxforwardscurve_generate_key():
    """FXForwardsCurve.generate_key returns a non-None value."""
    from finmarketpy.curve.fxforwardscurve import FXForwardsCurve

    fc = FXForwardsCurve()
    key = fc.generate_key()
    assert key is not None


def test_fxforwardscurve_unhedged_asset_fx_returns_none():
    """unhedged_asset_fx placeholder returns None (pass)."""
    from finmarketpy.curve.fxforwardscurve import FXForwardsCurve

    fc = FXForwardsCurve()
    result = fc.unhedged_asset_fx(None, None, None, None, None)
    assert result is None


def test_fxforwardscurve_hedged_asset_fx_returns_none():
    """hedged_asset_fx placeholder returns None (pass)."""
    from finmarketpy.curve.fxforwardscurve import FXForwardsCurve

    fc = FXForwardsCurve()
    result = fc.hedged_asset_fx(None, None, None, None, None)
    assert result is None


def test_fxforwardscurve_get_day_count_conv_365():
    """get_day_count_conv returns 365 for currencies with 365 basis."""
    from finmarketpy.curve.fxforwardscurve import FXForwardsCurve

    fc = FXForwardsCurve()
    for ccy in ["AUD", "CAD", "GBP", "NZD"]:
        assert fc.get_day_count_conv(ccy) == 365.0


def test_fxforwardscurve_get_day_count_conv_360():
    """get_day_count_conv returns 360 for other currencies."""
    from finmarketpy.curve.fxforwardscurve import FXForwardsCurve

    fc = FXForwardsCurve()
    assert fc.get_day_count_conv("EUR") == 360.0
    assert fc.get_day_count_conv("USD") == 360.0
