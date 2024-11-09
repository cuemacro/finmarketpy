import pytest_lazyfixture
import pytest
import pandas as pd
from finmarketpy.economics.seasonality import Seasonality

@pytest.fixture
def sample_data():
    dates = pd.date_range(start='2020-01-01', periods=100, freq='H')
    data = pd.DataFrame(data={'value': range(100)}, index=dates)
    return data

def test_time_of_day_seasonality(sample_data):
    seasonality = Seasonality()
    result = seasonality.time_of_day_seasonality(sample_data)
    assert not result.empty

def test_bus_day_of_month_seasonality_from_prices(sample_data):
    seasonality = Seasonality()
    result = seasonality.bus_day_of_month_seasonality_from_prices(sample_data)
    assert not result.empty

def test_monthly_seasonality_from_prices(sample_data):
    seasonality = Seasonality()
    result = seasonality.monthly_seasonality_from_prices(sample_data)
    assert not result.empty

def test_adjust_rolling_seasonality(sample_data):
    seasonality = Seasonality()
    result = seasonality.adjust_rolling_seasonality(sample_data, window=10, likely_period=24)
    assert not result.empty