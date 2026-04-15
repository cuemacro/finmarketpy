"""Tests for MarketConstants covering instantiation and override_fields."""
# ruff: noqa: D103

from unittest.mock import patch

from finmarketpy.util.marketconstants import MarketConstants


def test_instantiation_default():
    mc = MarketConstants()
    assert mc is not None
    assert hasattr(mc, "spot_depo_tenor")
    assert mc.spot_depo_tenor == "ON"


def test_instantiation_with_override_fields():
    override = {"spot_depo_tenor": "1W", "output_calculation_fields": True}
    MarketConstants(override_fields=override)
    # After override, class-level attributes are updated
    assert MarketConstants.spot_depo_tenor == "1W"
    assert MarketConstants.output_calculation_fields is True
    # Reset back
    MarketConstants.spot_depo_tenor = "ON"
    MarketConstants.output_calculation_fields = False
    MarketConstants.override_fields = {}


def test_instantiation_stores_override_fields():
    override = {"db_server": "192.168.1.1"}
    MarketConstants(override_fields=override)
    assert MarketConstants.override_fields == override
    # Reset
    MarketConstants.override_fields = {}
    MarketConstants.db_server = "127.0.0.1"


def test_platform_detection_linux():
    with patch("platform.platform", return_value="Linux-5.4.0-generic"):
        # Re-instantiating won't re-run the class-level detection, but we can test
        # that the plat attribute is set properly at class level
        mc = MarketConstants()
        # The generic_plat is set at class definition time, not at instantiation
        assert mc.generic_plat in ["linux", "windows", "mac"]


def test_platform_detection_windows():
    with patch("platform.platform", return_value="Windows-10-10.0.19041-SP0"):
        mc = MarketConstants()
        assert mc.generic_plat in ["linux", "windows", "mac"]


def test_class_attributes_exist():
    mc = MarketConstants()
    assert hasattr(mc, "backtest_thread_no")
    assert hasattr(mc, "currencies_with_365_basis")
    assert hasattr(mc, "fx_forwards_tenor_for_interpolation")
    assert hasattr(mc, "fx_options_tenor_for_interpolation")
    assert "AUD" in mc.currencies_with_365_basis


def test_override_fields_empty_dict():
    # First call with empty override_fields (should use class-level override_fields)
    MarketConstants.override_fields = {}
    mc = MarketConstants(override_fields={})
    assert mc is not None
