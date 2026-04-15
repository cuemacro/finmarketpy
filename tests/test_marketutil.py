"""Tests for MarketUtil.parse_date covering all branches."""
# ruff: noqa: D103

import datetime

import pandas as pd
import pytest

from finmarketpy.util.marketutil import MarketUtil


@pytest.fixture
def mu():
    return MarketUtil()


def test_parse_date_midnight(mu):
    result = mu.parse_date("midnight")
    now = datetime.datetime.utcnow()
    assert result.year == now.year
    assert result.month == now.month
    assert result.day == now.day
    assert result.hour == 0
    assert result.minute == 0
    assert result.second == 0


def test_parse_date_decade(mu):
    result = mu.parse_date("decade")
    assert isinstance(result, pd.Timestamp)
    # Should be approximately 10 years ago
    now = datetime.datetime.utcnow()
    diff_days = (now - result.to_pydatetime()).days
    assert 3640 <= diff_days <= 3660


def test_parse_date_year(mu):
    result = mu.parse_date("year")
    now = datetime.datetime.utcnow()
    diff_days = (now - result.to_pydatetime()).days
    assert 364 <= diff_days <= 366


def test_parse_date_month(mu):
    result = mu.parse_date("month")
    now = datetime.datetime.utcnow()
    diff_days = (now - result.to_pydatetime()).days
    assert 29 <= diff_days <= 31


def test_parse_date_week(mu):
    result = mu.parse_date("week")
    now = datetime.datetime.utcnow()
    diff_days = (now - result.to_pydatetime()).days
    assert 6 <= diff_days <= 8


def test_parse_date_day(mu):
    result = mu.parse_date("day")
    now = datetime.datetime.utcnow()
    diff_hours = (now - result.to_pydatetime()).total_seconds() / 3600
    assert 23 <= diff_hours <= 25


def test_parse_date_hour(mu):
    result = mu.parse_date("hour")
    now = datetime.datetime.utcnow()
    diff_mins = (now - result.to_pydatetime()).total_seconds() / 60
    assert 59 <= diff_mins <= 61


def test_parse_date_format_b_d_y_hm(mu):
    result = mu.parse_date("Jun 1 2005 01:33")
    assert result.year == 2005
    assert result.month == 6
    assert result.day == 1
    assert result.hour == 1
    assert result.minute == 33


def test_parse_date_format_d_b_y_hm(mu):
    result = mu.parse_date("1 Jun 2005 01:33")
    assert result.year == 2005
    assert result.month == 6
    assert result.day == 1


def test_parse_date_format_b_d_y(mu):
    result = mu.parse_date("Jun 1 2005")
    assert result.year == 2005
    assert result.month == 6
    assert result.day == 1


def test_parse_date_format_d_b_y(mu):
    result = mu.parse_date("1 Jun 2005")
    assert result.year == 2005
    assert result.month == 6
    assert result.day == 1


def test_parse_date_non_string(mu):
    dt = datetime.datetime(2021, 5, 15)
    result = mu.parse_date(dt)
    assert isinstance(result, pd.Timestamp)
    assert result.year == 2021
    assert result.month == 5
    assert result.day == 15


def test_parse_date_timestamp_non_string(mu):
    ts = pd.Timestamp("2020-03-01")
    result = mu.parse_date(ts)
    assert result == ts
