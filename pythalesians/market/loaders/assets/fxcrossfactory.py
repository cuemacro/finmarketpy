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

"""

FXCrossFactory

Provides various functions for generating FX time series.

"""

from pythalesians.util.loggermanager import LoggerManager

from pythalesians.market.requests.timeseriesrequest import TimeSeriesRequest
from pythalesians.timeseries.calcs.timeseriescalcs import TimeSeriesCalcs
from pythalesians.market.loaders.cachedtimeseriesfactory import CachedTimeSeriesFactory
from pythalesians.market.loaders.cachedtimeseriesfactory import LightTimeSeriesFactory

from pythalesians.util.fxconv import FXConv
from pythalesians.util.constants import Constants

class FXCrossFactory:

    def __init__(self):
        self.logger = LoggerManager().getLogger(__name__)
        self.fxconv = FXConv()

        if Constants().default_time_series_factory == 'lighttimeseriesfactory':
            self.time_series_factory = LightTimeSeriesFactory()
        else:
            self.time_series_factory = CachedTimeSeriesFactory()
        return

    def get_fx_cross_tick(self, start, end, cross,
                     cut = "NYC", source = "gain", cache_algo='cache_algo_return', type = 'spot'):

        if isinstance(cross, str):
            cross = [cross]

        time_series_request = TimeSeriesRequest()
        time_series_factory = self.time_series_factory
        data_frame_agg = None

        time_series_request.gran_freq = "tick"                  # tick

        time_series_request.freq_mult = 1                       # 1 min
        time_series_request.cut = cut                           # NYC/BGN ticker
        time_series_request.fields = ['bid', 'ask']             # bid/ask field only
        time_series_request.cache_algo = cache_algo             # cache_algo_only, cache_algo_return, internet_load

        time_series_request.environment = 'backtest'
        time_series_request.start_date = start
        time_series_request.finish_date = end
        time_series_request.data_source = source

        time_series_request.category = 'fx'

        for cr in cross:

            if (type == 'spot'):
                time_series_request.tickers = cr

                cross_vals = time_series_factory.harvest_time_series(time_series_request)
                cross_vals.columns = [cr + '.bid', cr + '.ask']

            if data_frame_agg is None:
                data_frame_agg = cross_vals
            else:
                data_frame_agg = data_frame_agg.join(cross_vals, how='outer')

        # strip the nan elements
        data_frame_agg = data_frame_agg.dropna()
        return data_frame_agg


    def get_fx_cross(self, start, end, cross,
                     cut = "NYC", source = "bloomberg", freq = "intraday", cache_algo='cache_algo_return', type = 'spot'):

        if source == "gain" or source == 'dukascopy' or freq == 'tick':
            return self.get_fx_cross_tick(start, end, cross,
                     cut = cut, source = source, cache_algo='cache_algo_return', type = 'spot')

        if isinstance(cross, str):
            cross = [cross]

        time_series_request = TimeSeriesRequest()
        time_series_factory = self.time_series_factory
        time_series_calcs = TimeSeriesCalcs()
        data_frame_agg = None

        if freq == 'intraday':
            time_series_request.gran_freq = "minute"                # intraday

        elif freq == 'daily':
            time_series_request.gran_freq = "daily"                 # intraday

        time_series_request.freq_mult = 1                       # 1 min
        time_series_request.cut = cut                           # NYC/BGN ticker
        time_series_request.fields = 'close'                    # close field only
        time_series_request.cache_algo = cache_algo             # cache_algo_only, cache_algo_return, internet_load

        time_series_request.environment = 'backtest'
        time_series_request.start_date = start
        time_series_request.finish_date = end
        time_series_request.data_source = source

        for cr in cross:
            base = cr[0:3]
            terms = cr[3:6]

            if (type == 'spot'):
                # non-USD crosses
                if base != 'USD' and terms != 'USD':
                    base_USD = self.fxconv.correct_notation('USD' + base)
                    terms_USD = self.fxconv.correct_notation('USD' + terms)

                    # TODO check if the cross exists in the database

                    # download base USD cross
                    time_series_request.tickers = base_USD
                    time_series_request.category = self.fxconv.em_or_g10(base, freq)
                    base_vals = time_series_factory.harvest_time_series(time_series_request)

                    # download terms USD cross
                    time_series_request.tickers = terms_USD
                    time_series_request.category = self.fxconv.em_or_g10(terms, freq)
                    terms_vals = time_series_factory.harvest_time_series(time_series_request)

                    if (base_USD[0:3] == 'USD'):
                        base_vals = 1 / base_vals
                    if (terms_USD[0:3] == 'USD'):
                        terms_vals = 1 / terms_vals

                    base_vals.columns = ['temp']
                    terms_vals.columns = ['temp']
                    cross_vals = base_vals.div(terms_vals, axis = 'index')
                    cross_vals.columns = [cr + '.close']

                else:
                    if base == 'USD': non_USD = terms
                    if terms == 'USD': non_USD = base

                    correct_cr = self.fxconv.correct_notation(cr)

                    time_series_request.tickers = correct_cr
                    time_series_request.category = self.fxconv.em_or_g10(non_USD, freq)
                    cross_vals = time_series_factory.harvest_time_series(time_series_request)

                    # flip if not convention
                    if(correct_cr != cr):
                        cross_vals = 1 / cross_vals

                    cross_vals.columns.names = [cr + '.close']

            elif type[0:3] == "tot":
                if freq == 'daily':
                    # download base USD cross
                    time_series_request.tickers = base + 'USD'
                    time_series_request.category = self.fxconv.em_or_g10(base, freq) + '-tot'

                    if type == "tot":
                        base_vals = time_series_factory.harvest_time_series(time_series_request)
                    else:
                        x = 0

                    # download terms USD cross
                    time_series_request.tickers = terms + 'USD'
                    time_series_request.category = self.fxconv.em_or_g10(terms, freq) + '-tot'

                    if type == "tot":
                        terms_vals = time_series_factory.harvest_time_series(time_series_request)
                    else:
                        x = 0

                    base_rets = time_series_calcs.calculate_returns(base_vals)
                    terms_rets = time_series_calcs.calculate_returns(terms_vals)

                    cross_rets = base_rets.sub(terms_rets.iloc[:,0],axis=0)

                    # first returns of a time series will by NaN, given we don't know previous point
                    cross_rets.iloc[0] = 0

                    cross_vals = time_series_calcs.create_mult_index(cross_rets)
                    cross_vals.columns = [cr + '-tot.close']

                elif freq == 'intraday':
                    self.logger.info('Total calculated returns for intraday not implemented yet')
                    return None

            if data_frame_agg is None:
                data_frame_agg = cross_vals
            else:
                data_frame_agg = data_frame_agg.join(cross_vals, how='outer')

        # strip the nan elements
        data_frame_agg = data_frame_agg.dropna()
        return data_frame_agg

if __name__ == '__main__':
    logger = LoggerManager.getLogger(__name__)

    fxcf = FXCrossFactory()

    path = "d:/"

    import datetime

    # DEMO: download intraday download
    if True:
        #
        start = '01 Jan 2014'
        end = '06 Nov 2014'
        cross = 'EURGBP'
        intraday_vals = fxcf.get_fx_cross(start, end, cross, cut = "NYC", source = "bloomberg", freq = "intraday", cache_algo = 'cache_algo_return')

        logger.info("Plot intraday values for " + cross)
        logger.info(intraday_vals.tail(n=100))

        # test download intraday download
        start = '01 Jan 2002'
        end = '03 Apr 2016'
        cross = ['EURUSD']
        intraday_vals = fxcf.get_fx_cross(start, end, cross, cut = "NYC", source = "bloomberg", freq = "intraday", cache_algo='internet_load_return')

        logger.info("Plot intraday values for " + str(cross))
        logger.info(intraday_vals)

    # DEMO: download daily FX cross data
    if False:
        start = '01 Jan 2015'
        end = datetime.datetime.utcnow()
        cross = 'AUDJPY'
        daily_vals = fxcf.get_fx_cross(start, end, cross, cut = "BGN", source = "bloomberg", freq = "daily", cache_algo='cache_algo_return')

        logger.info("Plot daily values for " + cross)
        logger.info(daily_vals.tail(n=100))

        tot_daily_vals = fxcf.get_fx_cross(start, end, cross, cut = "NYC", source = "bloomberg", freq = "daily", cache_algo='cache_algo_return', type='tot')

        logger.info("Plot daily total return values for " + cross)
        logger.info(tot_daily_vals.tail(n=100))

        compare_spot_tot = daily_vals.join(tot_daily_vals, how='inner')

        compare_spot_tot = compare_spot_tot/compare_spot_tot.shift(1) - 1
        compare_spot_tot.iloc[0] = 0
        compare_spot_index = 100 * (1 + compare_spot_tot).cumprod()

        logger.info("Plot daily spot vs. total return values for " + cross)
        logger.info(compare_spot_index.tail(n=100))

        import matplotlib.pyplot as plt

        compare_spot_index.plot()
        plt.show()

    # DEMO: Load up Gain Capital FX tick data, resampling to 1 minute and then plot
    if False:
        # test download intraday and tick download (for
        start = '01 Jan 2008'
        end = '28 Feb 2015'
        cross = 'USDJPY'

        logger.info("Compare intraday and tick data sources for " + cross)

        intraday_vals =  fxcf.get_fx_cross(start, end, cross, cut = "NYC", source = "bloomberg", freq = "intraday", cache_algo='cache_algo_return')

        tick_vals = fxcf.get_fx_cross(start, end, cross, source='gain', freq='tick')

        logger.info(tick_vals.tail(n=1000))

        compare_ticks = intraday_vals.join(tick_vals.resample('1min', how='last'), how='outer')

        last = compare_ticks.tail(n = 5000)
        last.to_csv(path + cross + '.csv')

        compare_ticks = compare_ticks.resample('60min', how='last')

        import matplotlib.pyplot as plt

        compare_ticks.plot()
        plt.show()

    # DEMO: Load up DukasCopy FX tick data, resampling to 1 minute (and later 60 minutes) and then plot
    if False:
        # test download intraday and tick download (for
        start = '01 Jan 2008'
        end = '28 Feb 2015'
        cross = 'EURUSD'

        logger.info("Compare intraday and tick data sources for " + cross)

        intraday_vals =  fxcf.get_fx_cross(start, end, cross, cut = "NYC", source = "bloomberg", freq = "intraday", cache_algo='cache_algo_return')

        tick_vals = fxcf.get_fx_cross(start, end, cross, source='dukascopy', freq='tick')

        logger.info(tick_vals.tail(n=1000))

        compare_ticks = intraday_vals.join(tick_vals.resample('1min', how='last'), how='outer')

        last = compare_ticks.tail(n = 5000)
        last.to_csv(path + cross + '.csv')

        compare_ticks = compare_ticks.resample('60min', how='last')

        import matplotlib.pyplot as plt

        compare_ticks.plot()
        plt.show()
