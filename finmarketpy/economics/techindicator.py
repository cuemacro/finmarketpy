__author__ = 'saeedamen' # Saeed Amen

#
# Copyright 2016 Cuemacro
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the
# License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the License for the specific language governing permissions and limitations under the License.
#

import pandas
import numpy

from findatapy.util.loggermanager import LoggerManager

class TechIndicator(object):
    """Calculates various technical indicators and associated trading signals.

    Signals can also be filtered to allow only longs or short and also to flip signals.

    It is possible to create subclasses of
    TechIndicator to implement your own custom signals and technical indicators.

    At present it implements the following technical indicators (and associated signals)
        SMA - simple moving averages - buy if spot above SMA, sell if below)
        EMA - exponential moving average - buy if spot spot above EMA, sell if below)
        ROC - rate of change - buy if rate of change positive, sell if negative
        polarity - buy if input is positive, sell if negative
        SMA2 - double simple moving average - buy if faster SMA above slower SMA, sell if below
        RSI - relative strength indicator - buy if RSI exits overbought, sell if RSI exits oversold
        BB - Bollinger bands - buy if spot above upper Bollinger band, sell if below lower Bollinger Band
        long_only - long only signal

    """

    def __init__(self):
        self.logger = LoggerManager().getLogger(__name__)
        self._techind = None
        self._signal = None

    def create_tech_ind(self, data_frame_non_nan, name, tech_params, data_frame_non_nan_early = None):
        self._signal = None
        self._techind = None

        data_frame = data_frame_non_nan.fillna(method="ffill")

        if data_frame_non_nan_early is not None:
            data_frame_early = data_frame_non_nan_early.fillna(method="ffill")

        if name == "SMA":

            if (data_frame_non_nan_early is not None):
                # calculate the lagged sum of the n-1 point
                rolling_sum = data_frame.shift(1).rolling(center=False, window=tech_params.sma_period - 1).sum()

                # add non-nan one for today
                rolling_sum = rolling_sum + data_frame_early

                # calculate average = sum / n
                self._techind = rolling_sum / tech_params.sma_period

                narray = numpy.where(data_frame_early > self._techind, 1, -1)
            else:
                # self._techind = pandas.rolling_mean(data_frame, tech_params.sma_period)
                self._techind = data_frame.rolling(window=tech_params.sma_period, center=False).mean()

                narray = numpy.where(data_frame > self._techind, 1, -1)

            self._signal = pandas.DataFrame(index = data_frame.index, data = narray)
            self._signal.loc[0:tech_params.sma_period] = numpy.nan
            self._signal.columns = [x + " SMA Signal" for x in data_frame.columns.values]

            self._techind.columns = [x + " SMA" for x in data_frame.columns.values]

        elif name == "EMA":

            # self._techind = pandas.ewma(data_frame, span = tech_params.ema_period)
            self._techind = data_frame.ewm(ignore_na=False,span=tech_params.ema_period,min_periods=0,adjust=True).mean()

            narray = numpy.where(data_frame > self._techind, 1, -1)

            self._signal = pandas.DataFrame(index = data_frame.index, data = narray)
            self._signal.loc[0:tech_params.ema_period] = numpy.nan
            self._signal.columns = [x + " EMA Signal" for x in data_frame.columns.values]

            self._techind.columns = [x + " EMA" for x in data_frame.columns.values]

        elif name == "ROC":

            if (data_frame_non_nan_early is not None):
                self._techind = data_frame_early / data_frame.shift(tech_params.roc_period) - 1
            else:
                self._techind = data_frame / data_frame.shift(tech_params.roc_period) - 1

            narray = numpy.where(self._techind > 0, 1, -1)

            self._signal = pandas.DataFrame(index = data_frame.index, data = narray)
            self._signal.loc[0:tech_params.roc_period] = numpy.nan
            self._signal.columns = [x + " ROC Signal" for x in data_frame.columns.values]

            self._techind.columns = [x + " ROC" for x in data_frame.columns.values]

        elif name == "polarity":
            self._techind = data_frame

            narray = numpy.where(self._techind > 0, 1, -1)

            self._signal = pandas.DataFrame(index = data_frame.index, data = narray)
            self._signal.columns = [x + " Polarity Signal" for x in data_frame.columns.values]

            self._techind.columns = [x + " Polarity" for x in data_frame.columns.values]

        elif name == "SMA2":
            sma = data_frame.rolling(window=tech_params.sma_period, center=False).mean()
            sma2 = data_frame.rolling(window=tech_params.sma2_period, center=False).mean()

            narray = numpy.where(sma > sma2, 1, -1)

            self._signal = pandas.DataFrame(index = data_frame.index, data = narray)
            self._signal.columns = [x + " SMA2 Signal" for x in data_frame.columns.values]

            sma.columns = [x + " SMA" for x in data_frame.columns.values]
            sma2.columns = [x + " SMA2" for x in data_frame.columns.values]
            most = max(tech_params.sma_period, tech_params.sma2_period)
            self._signal.loc[0:most] = numpy.nan
            self._techind = pandas.concat([sma, sma2], axis = 1)

        elif name in ['RSI']:
            # delta = data_frame.diff()
            #
            # dUp, dDown = delta.copy(), delta.copy()
            # dUp[dUp < 0] = 0
            # dDown[dDown > 0] = 0
            #
            # rolUp = pandas.rolling_mean(dUp, tech_params.rsi_period)
            # rolDown = pandas.rolling_mean(dDown, tech_params.rsi_period).abs()
            #
            # rsi = rolUp / rolDown

            # Get the difference in price from previous step
            delta = data_frame.diff()
            # Get rid of the first row, which is NaN since it did not have a previous
            # row to calculate the differences
            delta = delta[1:]

            # Make the positive gains (up) and negative gains (down) Series
            up, down = delta.copy(), delta.copy()
            up[up < 0] = 0
            down[down > 0] = 0

            # Calculate the EWMA
            roll_up1 = pandas.stats.moments.ewma(up, tech_params.rsi_period)
            roll_down1 = pandas.stats.moments.ewma(down.abs(), tech_params.rsi_period)

            # Calculate the RSI based on EWMA
            RS1 = roll_up1 / roll_down1
            RSI1 = 100.0 - (100.0 / (1.0 + RS1))

            # Calculate the SMA
            roll_up2 = up.rolling(window=tech_params.rsi_period, center=False).mean()
            roll_down2 = down.abs().rolling(window=tech_params.rsi_period, center=False).mean()

            # Calculate the RSI based on SMA
            RS2 = roll_up2 / roll_down2
            RSI2 = 100.0 - (100.0 / (1.0 + RS2))

            self._techind = RSI2
            self._techind.columns = [x + " RSI" for x in data_frame.columns.values]

            signal = data_frame.copy()

            sells = (signal.shift(-1) < tech_params.rsi_lower) & (signal > tech_params.rsi_lower)
            buys = (signal.shift(-1) > tech_params.rsi_upper) & (signal < tech_params.rsi_upper)

            # print (buys[buys == True])

            # buys
            signal[buys] =  1
            signal[sells] = -1
            signal[~(buys | sells)] = numpy.nan
            signal = signal.fillna(method = 'ffill')

            self._signal = signal

            self._signal.loc[0:tech_params.rsi_period] = numpy.nan
            self._signal.columns = [x + " RSI Signal" for x in data_frame.columns.values]

        elif name in ["BB"]:
            ## calcuate Bollinger bands
            mid = data_frame.rolling(center=False, window=tech_params.bb_period).mean(); mid.columns = [x + " BB Mid" for x in data_frame.columns.values]
            std_dev = data_frame.rolling(center=False, window=tech_params.bb_period).std()
            BB_std = tech_params.bb_mult * std_dev

            lower = pandas.DataFrame(data = mid.values - BB_std.values, index = mid.index,
                            columns = data_frame.columns)

            upper = pandas.DataFrame(data = mid.values + BB_std.values, index = mid.index,
                            columns = data_frame.columns)

            ## calculate signals
            signal = data_frame.copy()

            buys = signal > upper
            sells = signal < lower

            signal[buys] = 1
            signal[sells] = -1
            signal[~(buys | sells)] = numpy.nan
            signal = signal.fillna(method = 'ffill')

            self._signal = signal
            self._signal.loc[0:tech_params.bb_period] = numpy.nan
            self._signal.columns = [x + " " + name + " Signal" for x in data_frame.columns.values]

            lower.columns = [x + " BB Lower" for x in data_frame.columns.values]
            upper.columns = [x + " BB Mid" for x in data_frame.columns.values]
            upper.columns = [x + " BB Lower" for x in data_frame.columns.values]

            self._techind = pandas.concat([lower, mid, upper], axis = 1)
        elif name == "long-only":
            ## have +1 signals only
            self._techind = data_frame  # the technical indicator is just "prices"

            narray = numpy.ones((len(data_frame.index), len(data_frame.columns)))

            self._signal = pandas.DataFrame(index = data_frame.index, data = narray)
            self._signal.columns = [x + " Long Only Signal" for x in data_frame.columns.values]

            self._techind.columns = [x + " Long Only" for x in data_frame.columns.values]

        elif name == "ATR":
            # get all the asset names (assume we have names 'close', 'low', 'high' in the Data)
            # keep ordering of assets
            from collections import OrderedDict

            asset_name = list(OrderedDict.fromkeys([x.split('.')[0] for x in data_frame.columns]))

            df = []

            # can improve the performance of this if vectorise more!
            for a in asset_name:
                close = [a + '.close']
                low = [a + '.low']
                high = [a + '.high']

                prev_close = data_frame[close].shift(1)

                c1 = data_frame[high].values - data_frame[low].values
                c2 = numpy.abs(data_frame[high].values - prev_close.values)
                c3 = numpy.abs(data_frame[low].values - prev_close.values)

                true_range = numpy.max((c1,c2,c3), axis=0)
                true_range = pandas.DataFrame(index=data_frame.index, data=true_range, columns = [a + ' True Range'])

                df.append(true_range)

            from findatapy.timeseries import Calculations

            calc = Calculations()
            true_range = calc.pandas_outer_join(df)

            self._techind = true_range.rolling(window=tech_params.atr_period, center=False).mean()
            # self._techind = true_range.ewm(ignore_na=False, span=tech_params.atr_period, min_periods=0, adjust=True).mean()

            self._techind.columns = [x + " ATR" for x in asset_name]

        self.create_custom_tech_ind(data_frame_non_nan, name, tech_params, data_frame_non_nan_early)

        # TODO create other indicators
        if hasattr(tech_params, 'only_allow_longs'):
            self._signal[self._signal < 0] = 0

        # TODO create other indicators
        if hasattr(tech_params, 'only_allow_shorts'):
            self._signal[self._signal > 0] = 0

        # apply signal multiplier (typically to flip signals)
        if hasattr(tech_params, 'signal_mult'):
            self._signal = self._signal * tech_params.signal_mult

        if hasattr(tech_params, 'strip_signal_name'):
            if tech_params.strip_signal_name:
                self._signal.columns = data_frame.columns

        return self._techind

    def create_custom_tech_ind(self, data_frame_non_nan, name, tech_params, data_frame_non_nan_early):
        return

    def get_techind(self):
        return self._techind

    def get_signal(self):
        return self._signal

#######################################################################################################################



class TechParams:
    """Holds parameters for calculation of technical indicators.

    """
    pass

    # TODO add specific fields so can error check fields