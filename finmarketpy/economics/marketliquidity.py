__author__ = 'saeedamen'  # Saeed Amen

#
# Copyright 2016-2020 Cuemacro - https://www.cuemacro.com / @cuemacro
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

from findatapy.util.loggermanager import LoggerManager


class MarketLiquidity(object):
    """Calculates spread between bid/ask and also tick count.

    """

    def __init__(self):
        self.logger = LoggerManager().getLogger(__name__)
        return

    def calculate_spreads(self, data_frame, asset, bid_field='bid', ask_field='ask'):
        if isinstance(asset, str): asset = [asset]

        cols = [x + '.spread' for x in asset]

        data_frame_spreads = pandas.DataFrame(index=data_frame.index, columns=cols)

        for a in asset:
            data_frame_spreads[a + '.spread'] = data_frame[a + "." + ask_field] - data_frame[a + "." + bid_field]

        return data_frame_spreads

    def calculate_tick_count(self, data_frame, asset, freq='1h'):
        if isinstance(asset, str): asset = [asset]

        data_frame_tick_count = data_frame.resample(freq, how='count').dropna()
        data_frame_tick_count = data_frame_tick_count[[0]]

        data_frame_tick_count.columns = [x + '.event' for x in asset]

        return data_frame_tick_count


if __name__ == '__main__':
    # see examples
    pass
