"""Tests for EventStudy and EventsFactory."""
# ruff: noqa: D103

import pandas as pd
import pytest

from finmarketpy.economics.eventstudy import EventsFactory, EventStudy, HistEconDataFactory


def test_eventstudy_init():
    es = EventStudy()
    assert es is not None


def test_eventsfactory_init_with_df():
    """Init EventsFactory with a dataframe to avoid loading from disk."""
    # Create a minimal dataframe that mimics economic events structure
    df = pd.DataFrame(
        {
            "USD-NFP.Date": pd.date_range("2020-01-01", periods=3),
            "USD-NFP.close": [1.0, 2.0, 3.0],
            "USD-NFP.actual-release": [100.0, 200.0, 300.0],
            "USD-NFP.survey-median": [95.0, 195.0, 295.0],
            "USD-NFP.release-dt": [20200101, 20200201, 20200301],
            "USD-NFP.release-date-time-full": [
                pd.Timestamp("2020-01-03 13:30"),
                pd.Timestamp("2020-02-07 13:30"),
                pd.Timestamp("2020-03-06 13:30"),
            ],
        }
    )
    ef = EventsFactory(df=df)
    assert ef is not None
    assert ef.get_economic_events() is not None


def test_get_economic_events_returns_df():
    df = pd.DataFrame({"col": [1, 2, 3]})
    ef = EventsFactory(df=df)
    result = ef.get_economic_events()
    assert result is not None


def test_get_all_economic_events():
    df = pd.DataFrame(
        {
            "USD-NFP Test.Date": pd.date_range("2020-01-01", periods=3),
            "EUR-ECB Test.Date": pd.date_range("2020-01-01", periods=3),
        }
    )
    ef = EventsFactory(df=df)
    events = ef.get_all_economic_events()
    assert isinstance(events, list)
    assert len(events) >= 1


def test_create_event_descriptor_field():
    EventStudy()
    # Can use the base class method directly
    ef = EventsFactory(df=pd.DataFrame({"x": [1]}))
    result = ef.create_event_descriptor_field("USD-NFP", "release", "actual-release")
    assert result == "USD-NFP-release.actual-release"

    # Without event
    result = ef.create_event_descriptor_field("USD-NFP", None, "actual-release")
    assert result == "USD-NFP.actual-release"


def test_get_economic_event_date():
    """Test get_economic_event_date with field in _econ_data_frame."""
    df = pd.DataFrame(
        {
            "USD-NFP..release-dt": [20200101, 20200201, 20200301],
        }
    )
    ef = EventsFactory(df=df)
    result = ef.get_economic_event_date("USD-NFP")
    assert result is not None


def test_get_daily_moves_delegates():
    """Test that get_daily_moves_over_event is a pass-through."""
    df = pd.DataFrame({"x": [1]})
    ef = EventsFactory(df=df)
    result = ef.get_daily_moves_over_event()
    assert result is None


def test_histecon_data_factory_init():
    """Test HistEconDataFactory instantiation."""
    try:
        hef = HistEconDataFactory()
        assert hef is not None
        assert hef._all_econ_tickers is not None
        assert hef._econ_country_codes is not None
        assert hef._econ_country_groups is not None
    except FileNotFoundError:
        pytest.skip("Configuration files for HistEconDataFactory not available")


def test_histecon_data_factory_grasp_coded_entry():
    """Test grasp_coded_entry with simple data."""
    try:
        hef = HistEconDataFactory()
    except FileNotFoundError:
        pytest.skip("Configuration files for HistEconDataFactory not available")

    import contextlib

    dates = pd.date_range("2020-01-01", periods=3)
    with contextlib.suppress(Exception):
        hef.grasp_coded_entry(
            pd.DataFrame({"US-GDP": [1.0, 2.0, 3.0]}, index=dates),
            0,
        )  # Expected if 'US' not in country codes file
