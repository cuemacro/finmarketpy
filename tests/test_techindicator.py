__author__ = "saeedamen"  # Saeed Amen  # noqa: D100

#
# Copyright 2016-2020 Cuemacro - https://www.cuemacro.com / @cuemacro
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the  # noqa: E501
# License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the License for the specific language governing permissions and limitations under the License.
#

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from finmarketpy.economics.techindicator import TechIndicator, TechParams

tech_params = TechParams(fillna=True, atr_period=14, sma_period=3, green_n=4, green_count=9, red_n=2, red_count=13)
tech_ind = TechIndicator()
dates = pd.date_range(start="1/1/2018", end="1/08/2018")


def get_cols_name(n):  # noqa: D103
    return ["Asset%d.close" % x for x in range(1, n + 1)]  # noqa: UP031


def test_sma():  # noqa: D103
    indicator_name = "SMA"
    # Test Case 1: constant prices
    cols = get_cols_name(1)
    data_df = pd.DataFrame(index=dates, columns=cols, data=1)
    tech_ind.create_tech_ind(data_df, indicator_name, tech_params)
    expected_signal_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name, "Signal"]) for col in cols], data=-1
    )
    expected_df = pd.DataFrame(index=dates, columns=[" ".join([col, indicator_name]) for col in cols], data=1)
    expected_signal_df.iloc[: tech_params.sma_period] = np.nan
    expected_df.iloc[: tech_params.sma_period - 1] = np.nan
    df = tech_ind.get_techind()
    signal_df = tech_ind.get_signal()

    assert_frame_equal(df, expected_df)
    assert_frame_equal(signal_df, expected_signal_df)

    # Test Case 2: Normal case with one single security
    data_df = pd.DataFrame(index=dates, columns=cols, data=list(range(1, 9)))
    tech_ind.create_tech_ind(data_df, indicator_name, tech_params)
    expected_signal_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name, "Signal"]) for col in cols], data=1
    )
    expected_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name]) for col in cols], data=data_df.shift().values
    )
    df = tech_ind.get_techind()
    signal_df = tech_ind.get_signal()

    expected_signal_df.iloc[: tech_params.sma_period] = np.nan
    expected_df.iloc[: tech_params.sma_period - 1] = np.nan

    assert_frame_equal(df, expected_df)
    assert_frame_equal(signal_df, expected_signal_df)

    # Test Case 3: Normal case with multiple securities
    cols = get_cols_name(10)
    col_prices = np.array(range(1, 9))
    data_df = pd.DataFrame(index=dates, columns=cols, data=np.tile(col_prices, (len(cols), 1)).T)
    tech_ind.create_tech_ind(data_df, indicator_name, tech_params)
    expected_signal_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name, "Signal"]) for col in cols], data=1
    )
    expected_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name]) for col in cols], data=data_df.shift().values
    )
    df = tech_ind.get_techind()
    signal_df = tech_ind.get_signal()

    expected_signal_df.iloc[: tech_params.sma_period] = np.nan
    expected_df.iloc[: tech_params.sma_period - 1] = np.nan

    assert_frame_equal(df, expected_df)
    assert_frame_equal(signal_df, expected_signal_df)

    # Test Case 4: Decreasing price with multiple securities
    cols = get_cols_name(10)
    col_prices = np.array(range(8, 0, -1))
    data_df = pd.DataFrame(index=dates, columns=cols, data=np.tile(col_prices, (len(cols), 1)).T)
    tech_ind.create_tech_ind(data_df, indicator_name, tech_params)
    expected_signal_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name, "Signal"]) for col in cols], data=-1
    )
    expected_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name]) for col in cols], data=data_df.shift().values
    )
    df = tech_ind.get_techind()
    signal_df = tech_ind.get_signal()

    expected_signal_df.iloc[: tech_params.sma_period] = np.nan
    expected_df.iloc[: tech_params.sma_period - 1] = np.nan

    assert_frame_equal(df, expected_df)
    assert_frame_equal(signal_df, expected_signal_df)

    # Test Case 5: With SOME missing data
    cols = get_cols_name(1)
    data_df = pd.DataFrame(index=dates, columns=cols, data=list(range(1, 9)))
    data_df.iloc[3] = np.nan

    tech_ind.create_tech_ind(data_df, indicator_name, tech_params)
    expected_signal_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name, "Signal"]) for col in cols], data=1
    )
    expected_df = pd.DataFrame(
        index=dates,
        columns=[" ".join([col, indicator_name]) for col in cols],
        data=[np.nan, np.nan, 2, 2.67, 3.67, 4.67, 6, 7],
    )
    df = tech_ind.get_techind()
    signal_df = tech_ind.get_signal()

    expected_signal_df.iloc[: tech_params.sma_period] = np.nan

    assert_frame_equal(df.apply(lambda x: round(x, 2)), expected_df)
    assert_frame_equal(signal_df, expected_signal_df)

    # Test Case 6: With not enough data
    data_df = pd.DataFrame(index=dates, columns=cols, data=list(range(1, 9)))
    tech_params.sma_period = 20

    tech_ind.create_tech_ind(data_df, indicator_name, tech_params)
    expected_signal_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name, "Signal"]) for col in cols], data=np.nan
    )
    expected_df = pd.DataFrame(index=dates, columns=[" ".join([col, indicator_name]) for col in cols], data=np.nan)
    df = tech_ind.get_techind()
    signal_df = tech_ind.get_signal()

    assert_frame_equal(df, expected_df)
    assert_frame_equal(signal_df, expected_signal_df)


def test_roc():  # noqa: D103
    indicator_name = "ROC"
    # Test Case 1: constant prices
    cols = get_cols_name(1)
    tech_params.roc_period = 3
    data_df = pd.DataFrame(index=dates, columns=cols, data=1)
    tech_ind.create_tech_ind(data_df, indicator_name, tech_params)
    expected_signal_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name, "Signal"]) for col in cols], data=-1
    )
    expected_df = pd.DataFrame(index=dates, columns=[" ".join([col, indicator_name]) for col in cols], data=0)
    expected_signal_df.iloc[: tech_params.roc_period] = np.nan
    expected_df.iloc[: tech_params.roc_period] = np.nan
    df = tech_ind.get_techind()
    signal_df = tech_ind.get_signal()

    assert_frame_equal(df, expected_df)
    assert_frame_equal(signal_df, expected_signal_df)

    # Test Case 2: Increasing prices, fixed rate
    cols = get_cols_name(1)
    tech_params.roc_period = 1
    data_df = pd.DataFrame(index=dates, columns=cols, data=[1, 2, 4, 8, 16, 32, 64, 128])
    tech_ind.create_tech_ind(data_df, indicator_name, tech_params)
    expected_signal_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name, "Signal"]) for col in cols], data=1
    )
    expected_df = pd.DataFrame(index=dates, columns=[" ".join([col, indicator_name]) for col in cols], data=1)
    expected_signal_df.iloc[: tech_params.roc_period] = np.nan
    expected_df.iloc[: tech_params.roc_period] = np.nan
    df = tech_ind.get_techind()
    signal_df = tech_ind.get_signal()

    assert_frame_equal(df, expected_df)
    assert_frame_equal(signal_df, expected_signal_df)

    tech_params.roc_period = 2
    data_df = pd.DataFrame(index=dates, columns=cols, data=[1, 2, 4, 8, 16, 32, 64, 128])
    tech_ind.create_tech_ind(data_df, indicator_name, tech_params)
    expected_signal_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name, "Signal"]) for col in cols], data=1
    )
    expected_df = pd.DataFrame(index=dates, columns=[" ".join([col, indicator_name]) for col in cols], data=3)
    expected_signal_df.iloc[: tech_params.roc_period] = np.nan
    expected_df.iloc[: tech_params.roc_period] = np.nan
    df = tech_ind.get_techind()
    signal_df = tech_ind.get_signal()

    assert_frame_equal(df, expected_df)
    assert_frame_equal(signal_df, expected_signal_df)

    tech_params.roc_period = 3
    data_df = pd.DataFrame(index=dates, columns=cols, data=[1, 2, 4, 8, 16, 32, 64, 128])
    tech_ind.create_tech_ind(data_df, indicator_name, tech_params)
    expected_signal_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name, "Signal"]) for col in cols], data=1
    )
    expected_df = pd.DataFrame(index=dates, columns=[" ".join([col, indicator_name]) for col in cols], data=7)
    expected_signal_df.iloc[: tech_params.roc_period] = np.nan
    expected_df.iloc[: tech_params.roc_period] = np.nan
    df = tech_ind.get_techind()
    signal_df = tech_ind.get_signal()

    assert_frame_equal(df, expected_df)
    assert_frame_equal(signal_df, expected_signal_df)

    # Test Case 3: Missing values
    cols = get_cols_name(1)
    tech_params.roc_period = 1
    data_df = pd.DataFrame(index=dates, columns=cols, data=[1, 2, 4, 8, 16, 32, 64, 128])
    data_df.iloc[3] = np.nan
    tech_ind.create_tech_ind(data_df, indicator_name, tech_params)
    expected_signal_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name, "Signal"]) for col in cols], data=[1, 1, 1, -1, 1, 1, 1, 1]
    )
    expected_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name]) for col in cols], data=[1, 1, 1, 0, 3, 1, 1, 1]
    )
    expected_signal_df.iloc[: tech_params.roc_period] = np.nan
    expected_df.iloc[: tech_params.roc_period] = np.nan
    df = tech_ind.get_techind()
    signal_df = tech_ind.get_signal()

    assert_frame_equal(df, expected_df)
    assert_frame_equal(signal_df, expected_signal_df)


def test_sma2():  # noqa: D103
    indicator_name = "SMA2"
    tech_params.sma_period = 2
    tech_params.sma2_period = 3

    # Test Case 1: Increasing prices
    cols = get_cols_name(1)
    signals = ["SMA", "SMA2"]
    data_df = pd.DataFrame(index=dates, columns=cols, data=list(range(1, 9)))
    tech_ind.create_tech_ind(data_df, indicator_name, tech_params)
    expected_signal_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name, "Signal"]) for col in cols], data=1
    )
    expected_df = pd.DataFrame(
        index=dates,
        columns=[" ".join([col, sig]) for col in cols for sig in signals],
        data=[
            [np.nan, np.nan],
            [1.5, np.nan],
            [2.5, 2.0],
            [3.5, 3.0],
            [4.5, 4.0],
            [5.5, 5.0],
            [6.5, 6.0],
            [7.5, 7.0],
        ],
    )
    expected_signal_df.iloc[: tech_params.sma2_period] = np.nan
    df = tech_ind.get_techind()
    signal_df = tech_ind.get_signal()

    assert_frame_equal(df, expected_df)
    assert_frame_equal(signal_df, expected_signal_df)

    # Test Case 2: Decreasing prices
    cols = get_cols_name(1)
    signals = ["SMA", "SMA2"]
    data_df = pd.DataFrame(index=dates, columns=cols, data=list(range(8, 0, -1)))
    tech_ind.create_tech_ind(data_df, indicator_name, tech_params)
    expected_signal_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name, "Signal"]) for col in cols], data=-1
    )
    expected_df = pd.DataFrame(
        index=dates,
        columns=[" ".join([col, sig]) for col in cols for sig in signals],
        data=[
            [np.nan, np.nan],
            [7.5, np.nan],
            [6.5, 7.0],
            [5.5, 6.0],
            [4.5, 5.0],
            [3.5, 4.0],
            [2.5, 3.0],
            [1.5, 2.0],
        ],
    )
    expected_signal_df.iloc[: tech_params.sma2_period] = np.nan
    df = tech_ind.get_techind()
    signal_df = tech_ind.get_signal()

    assert_frame_equal(df, expected_df)
    assert_frame_equal(signal_df, expected_signal_df)

    # Test Case 3: Constant prices
    cols = get_cols_name(1)
    signals = ["SMA", "SMA2"]
    data_df = pd.DataFrame(index=dates, columns=cols, data=1)
    tech_ind.create_tech_ind(data_df, indicator_name, tech_params)

    expected_signal_df = pd.DataFrame(
        data=-1.0,
        index=dates,
        columns=[" ".join([col, indicator_name, "Signal"]) for col in cols],
    )
    expected_signal_df.iloc[: tech_params.sma2_period] = np.nan

    signal_df = tech_ind.get_signal()
    assert_frame_equal(signal_df, expected_signal_df)

    expected_df = pd.DataFrame(
        data=1.0,
        index=dates,
        columns=[" ".join([col, sig]) for col in cols for sig in signals],
    )
    expected_df.iloc[: tech_params.sma2_period - 1] = np.nan
    expected_df.loc["2018-01-02", "Asset1.close SMA"] = 1.0

    df = tech_ind.get_techind()
    assert_frame_equal(df, expected_df)


def test_polarity():  # noqa: D103
    indicator_name = "polarity"

    # Test Case 1: constant prices
    cols = get_cols_name(1)
    data_df = pd.DataFrame(index=dates, columns=cols, data=1)
    tech_ind.create_tech_ind(data_df, indicator_name, tech_params)
    expected_signal_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, "Polarity", "Signal"]) for col in cols], data=1
    )
    expected_df = pd.DataFrame(index=dates, columns=[" ".join([col, "Polarity"]) for col in cols], data=1)
    df = tech_ind.get_techind()
    signal_df = tech_ind.get_signal()

    assert_frame_equal(df, expected_df)
    assert_frame_equal(signal_df, expected_signal_df, check_dtype=False)

    # Test Case 2: Increasing prices
    cols = get_cols_name(1)
    data_df = pd.DataFrame(index=dates, columns=cols, data=[1, 2, 4, 8, 16, 32, 64, 128])
    tech_ind.create_tech_ind(data_df, indicator_name, tech_params)
    expected_signal_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, "Polarity", "Signal"]) for col in cols], data=1
    )
    expected_df = pd.DataFrame(index=dates, columns=[" ".join([col, "Polarity"]) for col in cols], data=data_df.values)
    df = tech_ind.get_techind()
    signal_df = tech_ind.get_signal()

    assert_frame_equal(df, expected_df)
    assert_frame_equal(signal_df, expected_signal_df, check_dtype=False)

    # Test Case 3: Decreasing prices
    cols = get_cols_name(1)
    data_df = pd.DataFrame(index=dates, columns=cols, data=list(range(-1, -9, -1)))
    tech_ind.create_tech_ind(data_df, indicator_name, tech_params)
    expected_signal_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, "Polarity", "Signal"]) for col in cols], data=-1
    )
    expected_df = pd.DataFrame(index=dates, columns=[" ".join([col, "Polarity"]) for col in cols], data=data_df.values)
    df = tech_ind.get_techind()
    signal_df = tech_ind.get_signal()

    assert_frame_equal(df, expected_df)
    assert_frame_equal(signal_df, expected_signal_df, check_dtype=False)

    # Test Case 4: Missing values
    cols = get_cols_name(1)
    tech_params.roc_period = 1
    data_df = pd.DataFrame(index=dates, columns=cols, data=[1, 2, 4, 8, 16, 32, 64, 128])
    data_df.iloc[3] = np.nan
    tech_ind.create_tech_ind(data_df, indicator_name, tech_params)
    expected_signal_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, "Polarity", "Signal"]) for col in cols], data=1
    )
    expected_df = pd.DataFrame(
        index=dates,
        columns=[" ".join([col, "Polarity"]) for col in cols],
        data=[1.0, 2.0, 4.0, 4.0, 16.0, 32.0, 64.0, 128.0],
    )
    df = tech_ind.get_techind()
    signal_df = tech_ind.get_signal()

    assert_frame_equal(df, expected_df)
    assert_frame_equal(signal_df, expected_signal_df, check_dtype=False)


def test_attr():
    """Testing of attributes such as long only."""
    indicator_name = "SMA"
    tech_params = TechParams()

    # Test Case 1: Only longs or only shorts
    # Test Case 1.1: Only longs
    cols = get_cols_name(1)
    tech_params.sma_period = 3
    tech_params.only_allow_longs = True
    data_df = pd.DataFrame(index=dates, columns=cols, data=list(range(1, 9)))
    tech_ind.create_tech_ind(data_df, indicator_name, tech_params)
    expected_signal_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name, "Signal"]) for col in cols], data=1
    )
    expected_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name]) for col in cols], data=data_df.shift().values
    )
    df = tech_ind.get_techind()
    signal_df = tech_ind.get_signal()

    expected_signal_df.iloc[: tech_params.sma_period] = np.nan
    expected_df.iloc[: tech_params.sma_period - 1] = np.nan

    assert_frame_equal(df, expected_df)
    assert_frame_equal(signal_df, expected_signal_df)

    data_df = pd.DataFrame(index=dates, columns=cols, data=list(range(8, 0, -1)))
    tech_ind.create_tech_ind(data_df, indicator_name, tech_params)
    expected_signal_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name, "Signal"]) for col in cols], data=0
    )
    expected_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name]) for col in cols], data=data_df.shift().values
    )
    df = tech_ind.get_techind()
    signal_df = tech_ind.get_signal()

    expected_signal_df.iloc[: tech_params.sma_period] = np.nan
    expected_df.iloc[: tech_params.sma_period - 1] = np.nan

    assert_frame_equal(df, expected_df)
    assert_frame_equal(signal_df, expected_signal_df)

    # Test Case 1.1: Only shorts
    tech_params = TechParams()
    tech_params.sma_period = 3
    tech_params.only_allow_shorts = True
    data_df = pd.DataFrame(index=dates, columns=cols, data=list(range(1, 9)))
    tech_ind.create_tech_ind(data_df, indicator_name, tech_params)
    expected_signal_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name, "Signal"]) for col in cols], data=0
    )
    expected_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name]) for col in cols], data=data_df.shift().values
    )
    df = tech_ind.get_techind()
    signal_df = tech_ind.get_signal()

    expected_signal_df.iloc[: tech_params.sma_period] = np.nan
    expected_df.iloc[: tech_params.sma_period - 1] = np.nan

    assert_frame_equal(df, expected_df)
    assert_frame_equal(signal_df, expected_signal_df)

    data_df = pd.DataFrame(index=dates, columns=cols, data=list(range(8, 0, -1)))
    tech_ind.create_tech_ind(data_df, indicator_name, tech_params)
    expected_signal_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name, "Signal"]) for col in cols], data=-1
    )
    expected_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name]) for col in cols], data=data_df.shift().values
    )
    df = tech_ind.get_techind()
    signal_df = tech_ind.get_signal()

    expected_signal_df.iloc[: tech_params.sma_period] = np.nan
    expected_df.iloc[: tech_params.sma_period - 1] = np.nan

    assert_frame_equal(df, expected_df)
    assert_frame_equal(signal_df, expected_signal_df)

    # Test Case 2: Check incompatibility between only_allow_longs and only_allow_shorts
    tech_params = TechParams()
    tech_params.only_allow_shorts = True
    with pytest.raises(Exception):  # noqa: B017, PT011
        tech_params.only_allow_longs = True

    tech_params = TechParams()
    tech_params.only_allow_longs = True
    with pytest.raises(Exception):  # noqa: B017, PT011
        tech_params.only_allow_shorts = True

    # Test Case 3: test strip_signal_name
    tech_params = TechParams()
    tech_params.sma_period = 3
    tech_params.strip_signal_name = True
    data_df = pd.DataFrame(index=dates, columns=cols, data=list(range(1, 9)))
    tech_ind.create_tech_ind(data_df, indicator_name, tech_params)
    expected_signal_df = pd.DataFrame(index=dates, columns=cols, data=1)
    expected_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name]) for col in cols], data=data_df.shift().values
    )
    df = tech_ind.get_techind()
    signal_df = tech_ind.get_signal()

    expected_signal_df.iloc[: tech_params.sma_period] = np.nan
    expected_df.iloc[: tech_params.sma_period - 1] = np.nan

    assert_frame_equal(df, expected_df)
    assert_frame_equal(signal_df, expected_signal_df)

    # Test Case 4: test signal multiplier
    tech_params = TechParams()
    tech_params.sma_period = 3
    tech_params.signal_mult = -1
    data_df = pd.DataFrame(index=dates, columns=cols, data=list(range(1, 9)))
    tech_ind.create_tech_ind(data_df, indicator_name, tech_params)
    expected_signal_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name, "Signal"]) for col in cols], data=-1
    )
    expected_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name]) for col in cols], data=data_df.shift().values
    )
    df = tech_ind.get_techind()
    signal_df = tech_ind.get_signal()

    expected_signal_df.iloc[: tech_params.sma_period] = np.nan
    expected_df.iloc[: tech_params.sma_period - 1] = np.nan

    assert_frame_equal(df, expected_df)
    assert_frame_equal(signal_df, expected_signal_df)

    tech_params.signal_mult = 0
    data_df = pd.DataFrame(index=dates, columns=cols, data=list(range(1, 9)))
    tech_ind.create_tech_ind(data_df, indicator_name, tech_params)
    expected_signal_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name, "Signal"]) for col in cols], data=0
    )
    expected_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name]) for col in cols], data=data_df.shift().values
    )
    df = tech_ind.get_techind()
    signal_df = tech_ind.get_signal()

    expected_signal_df.iloc[: tech_params.sma_period] = np.nan
    expected_df.iloc[: tech_params.sma_period - 1] = np.nan

    assert_frame_equal(df, expected_df)
    assert_frame_equal(signal_df, expected_signal_df)

    tech_params.signal_mult = 3
    data_df = pd.DataFrame(index=dates, columns=cols, data=list(range(1, 9)))
    tech_ind.create_tech_ind(data_df, indicator_name, tech_params)
    expected_signal_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name, "Signal"]) for col in cols], data=3
    )
    expected_df = pd.DataFrame(
        index=dates, columns=[" ".join([col, indicator_name]) for col in cols], data=data_df.shift().values
    )
    df = tech_ind.get_techind()
    signal_df = tech_ind.get_signal()

    expected_signal_df.iloc[: tech_params.sma_period] = np.nan
    expected_df.iloc[: tech_params.sma_period - 1] = np.nan

    assert_frame_equal(df, expected_df)
    assert_frame_equal(signal_df, expected_signal_df)


def test_ema():
    """Test EMA indicator."""
    indicator_name = "EMA"
    tp = TechParams(fillna=True, sma_period=3)
    tp.ema_period = 3

    cols = get_cols_name(1)
    data_df = pd.DataFrame(index=dates, columns=cols, data=list(range(1, 9)))
    ti = TechIndicator()
    ti.create_tech_ind(data_df, indicator_name, tp)

    techind = ti.get_techind()
    signal = ti.get_signal()

    assert techind is not None
    assert signal is not None
    assert techind.shape[0] == len(dates)
    assert signal.shape[0] == len(dates)
    # Columns should be renamed
    assert techind.columns[0] == "Asset1.close EMA"
    assert signal.columns[0] == "Asset1.close EMA Signal"


def test_sma_with_early_data():
    """Test SMA indicator with data_frame_non_nan_early (covers lines 84, 87-98)."""
    indicator_name = "SMA"
    tp = TechParams(fillna=True, sma_period=3)

    cols = get_cols_name(1)
    data_df = pd.DataFrame(index=dates, columns=cols, data=list(range(1, 9)), dtype=float)
    early_df = pd.DataFrame(index=dates, columns=cols, data=list(range(2, 10)), dtype=float)

    ti = TechIndicator()
    ti.create_tech_ind(data_df, indicator_name, tp, data_frame_non_nan_early=early_df)

    techind = ti.get_techind()
    signal = ti.get_signal()
    assert techind is not None
    assert signal is not None


def test_roc_with_early_data():
    """Test ROC indicator with early data (covers line 132)."""
    indicator_name = "ROC"
    tp = TechParams(fillna=True)
    tp.roc_period = 1

    cols = get_cols_name(1)
    data_df = pd.DataFrame(index=dates, columns=cols, data=list(range(1, 9)), dtype=float)
    early_df = pd.DataFrame(index=dates, columns=cols, data=list(range(2, 10)), dtype=float)

    ti = TechIndicator()
    ti.create_tech_ind(data_df, indicator_name, tp, data_frame_non_nan_early=early_df)

    techind = ti.get_techind()
    signal = ti.get_signal()
    assert techind is not None
    assert signal is not None


def test_bb():
    """Test Bollinger Bands indicator."""
    indicator_name = "BB"
    tp = TechParams(fillna=True, sma_period=3)
    tp.bb_period = 3
    tp.bb_mult = 2.0

    cols = get_cols_name(1)
    data_df = pd.DataFrame(index=dates, columns=cols, data=list(range(1, 9)), dtype=float)

    ti = TechIndicator()
    ti.create_tech_ind(data_df, indicator_name, tp)

    techind = ti.get_techind()
    signal = ti.get_signal()
    assert techind is not None
    assert signal is not None
    # BB produces lower, mid, upper columns
    assert techind.shape[1] == 3


def test_long_only():
    """Test long-only indicator."""
    indicator_name = "long-only"
    tp = TechParams(fillna=True)

    cols = get_cols_name(1)
    data_df = pd.DataFrame(index=dates, columns=cols, data=list(range(1, 9)), dtype=float)

    ti = TechIndicator()
    ti.create_tech_ind(data_df, indicator_name, tp)

    techind = ti.get_techind()
    signal = ti.get_signal()
    assert techind is not None
    assert signal is not None
    assert (signal.dropna() == 1).all().all()


def test_short_only():
    """Test short-only indicator."""
    indicator_name = "short-only"
    tp = TechParams(fillna=True)

    cols = get_cols_name(1)
    data_df = pd.DataFrame(index=dates, columns=cols, data=list(range(1, 9)), dtype=float)

    ti = TechIndicator()
    ti.create_tech_ind(data_df, indicator_name, tp)

    techind = ti.get_techind()
    signal = ti.get_signal()
    assert techind is not None
    assert signal is not None
    assert (signal.dropna() == 1).all().all()


def test_atr():
    """Test ATR indicator with OHLC data."""
    indicator_name = "ATR"
    tp = TechParams(fillna=True, atr_period=3)

    # ATR needs Asset1.close, Asset1.low, Asset1.high columns
    dates_atr = pd.date_range(start="1/1/2018", end="1/20/2018")
    prices = list(range(1, len(dates_atr) + 1))
    data = {
        "Asset1.close": prices,
        "Asset1.low": [p - 0.5 for p in prices],
        "Asset1.high": [p + 0.5 for p in prices],
    }
    data_df = pd.DataFrame(index=dates_atr, data=data, dtype=float)

    ti = TechIndicator()
    ti.create_tech_ind(data_df, indicator_name, tp)

    techind = ti.get_techind()
    assert techind is not None
    assert "Asset1.close ATR" in techind.columns


def test_atr_without_fillna():
    """Test ATR indicator without fillna (covers the dropna path)."""
    indicator_name = "ATR"
    tp = TechParams(fillna=False, atr_period=3)

    dates_atr = pd.date_range(start="1/1/2018", end="1/20/2018")
    prices = list(range(1, len(dates_atr) + 1))
    data = {
        "Asset1.close": prices,
        "Asset1.low": [p - 0.5 for p in prices],
        "Asset1.high": [p + 0.5 for p in prices],
    }
    data_df = pd.DataFrame(index=dates_atr, data=data, dtype=float)

    ti = TechIndicator()
    ti.create_tech_ind(data_df, indicator_name, tp)

    techind = ti.get_techind()
    assert techind is not None


def test_vwap():
    """Test VWAP indicator with OHLCV data."""
    indicator_name = "VWAP"
    tp = TechParams(fillna=True)

    dates_vwap = pd.date_range(start="1/1/2018", end="1/20/2018")
    n = len(dates_vwap)
    data = {
        "Asset1.close": list(range(10, 10 + n)),
        "Asset1.low": [p - 1 for p in range(10, 10 + n)],
        "Asset1.high": [p + 1 for p in range(10, 10 + n)],
        "Asset1.volume": [1000.0] * n,
    }
    data_df = pd.DataFrame(index=dates_vwap, data=data, dtype=float)

    ti = TechIndicator()
    ti.create_tech_ind(data_df, indicator_name, tp)

    techind = ti.get_techind()
    assert techind is not None
    assert "Asset1.close VWAP" in techind.columns


def test_vwap_without_fillna():
    """Test VWAP indicator without fillna."""
    indicator_name = "VWAP"
    tp = TechParams(fillna=False)

    dates_vwap = pd.date_range(start="1/1/2018", end="1/20/2018")
    n = len(dates_vwap)
    data = {
        "Asset1.close": list(range(10, 10 + n)),
        "Asset1.low": [p - 1 for p in range(10, 10 + n)],
        "Asset1.high": [p + 1 for p in range(10, 10 + n)],
        "Asset1.volume": [1000.0] * n,
    }
    data_df = pd.DataFrame(index=dates_vwap, data=data, dtype=float)

    ti = TechIndicator()
    ti.create_tech_ind(data_df, indicator_name, tp)

    techind = ti.get_techind()
    assert techind is not None


def test_gmma():
    """Test GMMA indicator."""
    indicator_name = "GMMA"
    tp = TechParams(fillna=True, sma_period=3)
    tp.sma2_period = 5

    # Need enough data for the longest period (60)
    dates_gmma = pd.date_range(start="1/1/2018", periods=100)
    cols = get_cols_name(1)
    data_df = pd.DataFrame(index=dates_gmma, columns=cols, data=list(range(1, 101)), dtype=float)

    ti = TechIndicator()
    ti.create_tech_ind(data_df, indicator_name, tp)

    techind = ti.get_techind()
    signal = ti.get_signal()
    assert techind is not None
    assert signal is not None
    # GMMA has 12 MA columns
    assert techind.shape[1] == 12


def test_rsi():
    """Test RSI indicator after fixing deprecated API."""
    indicator_name = "RSI"
    tp = TechParams(fillna=True)
    tp.rsi_period = 3
    tp.rsi_lower = 30
    tp.rsi_upper = 70

    # Need enough data for RSI period
    dates_rsi = pd.date_range(start="1/1/2018", periods=30)
    cols = get_cols_name(1)
    data = list(range(1, 31))
    data_df = pd.DataFrame(index=dates_rsi, columns=cols, data=data, dtype=float)

    ti = TechIndicator()
    ti.create_tech_ind(data_df, indicator_name, tp)

    techind = ti.get_techind()
    signal = ti.get_signal()
    assert techind is not None
    assert signal is not None
    assert techind.columns[0] == "Asset1.close RSI"


def test_techparams_getters():
    """Test TechParams property getters for green_n, green_count, red_n, red_count."""
    tp = TechParams(fillna=True, atr_period=14, sma_period=20, green_n=4, green_count=9, red_n=2, red_count=13)
    assert tp.green_n == 4
    assert tp.green_count == 9
    assert tp.red_n == 2
    assert tp.red_count == 13

    # Test setters too
    tp.green_n = 5
    tp.green_count = 10
    tp.red_n = 3
    tp.red_count = 14

    assert tp.green_n == 5
    assert tp.green_count == 10
    assert tp.red_n == 3
    assert tp.red_count == 14
