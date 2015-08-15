__author__ = 'saeedamen' # Saeed Amen / saeed@thalesians.com

#
# Copyright 2015 Thalesians Ltd. - http//www.thalesians.com / @thalesians
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

from pythalesians.util.loggermanager import LoggerManager
from pythalesians.timeseries.calcs.timeseriescalcs import TimeSeriesCalcs


class TechIndicator:

    def __init__(self):
        self.logger = LoggerManager().getLogger(__name__)
        self._techind = None
        self._signal = None

    def create_tech_ind(self, data_frame_non_nan, name, tech_params, data_frame_non_nan_early = None):
        self._signal = None

        data_frame = data_frame_non_nan.fillna(method="ffill")

        if data_frame_non_nan_early is not None:
            data_frame_early = data_frame_non_nan_early.fillna(method="ffill")

        if name == "SMA":

            if (data_frame_non_nan_early is not None):
                # calculate the lagged sum of the n-1 point
                rolling_sum = pandas.rolling_sum(data_frame.shift(1), tech_params.sma_period - 1)

                # add non-nan one for today
                rolling_sum = rolling_sum + data_frame_early

                # calculate average = sum / n
                self._techind = rolling_sum / tech_params.sma_period

                narray = numpy.where(data_frame_early > self._techind, 1, -1)
            else:
                self._techind = pandas.rolling_mean(data_frame, tech_params.sma_period)

                narray = numpy.where(data_frame > self._techind, 1, -1)

            self._signal = pandas.DataFrame(index = data_frame.index, data = narray)
            self._signal.columns = [x + " SMA Signal" for x in data_frame.columns.values]

            self._techind.columns = [x + " SMA" for x in data_frame.columns.values]
        elif name == "ROC":

            if (data_frame_non_nan_early is not None):
                self._techind = data_frame_early / data_frame.shift(tech_params.roc_period) - 1
            else:
                self._techind = data_frame / data_frame.shift(tech_params.roc_period) - 1

            #tsc = TimeSeriesCalcs()
            #data_frame = tsc.calculate_returns(data_frame)
            #self._techind = pandas.rolling_mean(data_frame, tech_params.roc_period)

            narray = numpy.where(self._techind > 0, 1, -1)

            self._signal = pandas.DataFrame(index = data_frame.index, data = narray)
            self._signal.columns = [x + " ROC Signal" for x in data_frame.columns.values]

            self._techind.columns = [x + " ROC" for x in data_frame.columns.values]

        elif name == "SMA2":
            sma = pandas.rolling_mean(data_frame, tech_params.sma_period)
            sma2 = pandas.rolling_mean(data_frame, tech_params.sma2_period)

            narray = numpy.where(sma > sma2, 1, -1)

            self._signal = pandas.DataFrame(index = data_frame.index, data = narray)
            self._signal.columns = [x + " SMA2 Signal" for x in data_frame.columns.values]

            sma.columns = [x + " SMA" for x in data_frame.columns.values]
            sma2.columns = [x + " SMA2" for x in data_frame.columns.values]
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
            roll_up2 = pandas.rolling_mean(up, tech_params.rsi_period)
            roll_down2 = pandas.rolling_mean(down.abs(), tech_params.rsi_period)

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
            self._signal.columns = [x + " RSI Signal" for x in data_frame.columns.values]

        elif name in ["BB"]:
            ## calcuate Bollinger bands
            mid = pandas.rolling_mean(data_frame, tech_params.bb_period); mid.columns = [x + " BB Mid" for x in data_frame.columns.values]
            std_dev = pandas.rolling_std(data_frame, tech_params.bb_period)
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

        # TODO create other indicators

        # apply signal multiplier (typically to flip signals)
        if hasattr(tech_params, 'signal_mult'):
            self._signal = self._signal * tech_params.signal_mult

        return self._techind

    def get_techind(self):
        return self._techind

    def get_signal(self):
        return self._signal

if __name__ == '__main__':
    pass
    # see pythalesians-examples/techindicator_examples