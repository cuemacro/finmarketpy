__author__ = 'saeedamen'

import pandas

from pythalesians.util.configmanager import ConfigManager
from pythalesians.util.loggermanager import LoggerManager
from pythalesians.market.loaders.assets.fxcrossfactory import FXCrossFactory

class MarketLiquidity:

    def __init__(self):
        self.config = ConfigManager()
        self.logger = LoggerManager().getLogger(__name__)
        return

    def calculate_spreads(self, data_frame, asset, bid_field = 'bid', ask_field = 'ask'):
        if isinstance(asset, str): asset = [asset]

        cols = [x + '.spread' for x in asset]

        data_frame_spreads = pandas.DataFrame(index=data_frame.index, columns=cols)

        for a in asset:
            data_frame_spreads[a + '.spread'] = data_frame[a + "." + ask_field] - data_frame[a + "." + bid_field]

        return data_frame_spreads

    def calculate_tick_count(self, data_frame, asset, freq = '1h'):
        if isinstance(asset, str): asset = [asset]

        data_frame_tick_count = data_frame.resample(freq, how='count').dropna()
        data_frame_tick_count = data_frame_tick_count[[0]]

        data_frame_tick_count.columns = [x + '.event' for x in asset]

        return data_frame_tick_count

if __name__ == '__main__':
    # see examples
    pass