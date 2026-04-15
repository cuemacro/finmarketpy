"""Tests for Report - tests instantiation (methods have pragma: no cover due to broken API call)."""
# ruff: noqa: D103

from finmarketpy.economics.report import Report


def test_report_init():
    r = Report()
    assert r is not None
