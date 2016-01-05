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
indexfx_examples

Examples on how to create total return indices using PyThalesians

"""

# for logging
from pythalesians.util.loggermanager import LoggerManager

# to download market data
from pythalesians.market.requests.timeseriesrequest import TimeSeriesRequest
from pythalesians.market.loaders.lighttimeseriesfactory import LightTimeSeriesFactory

from pythalesians.market.indices.indicesfx import IndicesFX

# for plotting graphs
from pythalesians.graphics.graphs.plotfactory import PlotFactory
from pythalesians.graphics.graphs.graphproperties import GraphProperties

# for making elementary calculations on the time series
from pythalesians.timeseries.calcs.timeseriescalcs import TimeSeriesCalcs

import copy

if True:
    logger = LoggerManager().getLogger(__name__)

    import datetime

    # just change "False" to "True" to run any of the below examples

    ###### download from Bloomberg spot data, deposit data and total return indices for FX
    ###### compare total return indices for FX (computed using PyThalesians) with those from Bloomberg
    if True:

        # tickers for spot data
        time_series_request_spot = TimeSeriesRequest(
                start_date = "01 Jan 1999",                     # start date
                finish_date = datetime.date.today(),            # finish date
                freq = 'daily',                                 # daily data
                data_source = 'bloomberg',                      # use Bloomberg as data source
                tickers = ['EURUSD',                            # ticker (Thalesians)
                           'GBPUSD',
                           'AUDUSD'],
                fields = ['close'],                             # which fields to download
                vendor_tickers = ['EURUSD BGN Curncy',          # ticker (Bloomberg)
                                  'GBPUSD BGN Curncy',
                                  'AUDUSD BGN Curncy'],
                vendor_fields = ['PX_LAST'],   # which Bloomberg fields to download
                cache_algo = 'internet_load_return')                # how to return data

        # tickers for overnight deposit data, which is necessary for computing total return indices
        time_series_request_deposit = copy.copy(time_series_request_spot)
        time_series_request_deposit.tickers = ['EURON', 'USDON', 'GBPON', 'AUDON']
        time_series_request_deposit.vendor_tickers = ['EUDR1T CMPN Curncy', 'USDR1T CMPN Curncy',
                                                      'BPDR1T CMPN Curncy', 'ADDR1T CMPN Curncy']

        # tickers for getting total return indices from Bloomberg directly
        time_series_request_total_ret = copy.copy(time_series_request_spot)
        time_series_request_total_ret.tickers = ['EURUSD', 'GBPUSD', 'AUDUSD']
        time_series_request_total_ret.vendor_tickers = ['EURUSDCR BGN Curncy', 'GBPUSDCR BGN Curncy', 'AUDUSDCR BGN Curncy']

        ltsf = LightTimeSeriesFactory()

        df = None
        spot_df = ltsf.harvest_time_series(time_series_request_spot)
        deposit_df = ltsf.harvest_time_series(time_series_request_deposit)
        tot_df = ltsf.harvest_time_series(time_series_request_total_ret)
        tsc = TimeSeriesCalcs()

        tot_df = tsc.create_mult_index_from_prices(tot_df) # rebase index at 100

        # we can change the
        tenor = 'ON'

        # plot total return series comparison for all our crosses
        # in practice, we would typically make a set of xxxUSD total return indices
        # and use them to compute all other crosses (assuming we are USD denominated investor)
        for cross in ['AUDUSD', 'EURUSD', 'GBPUSD']:

            # create total return index using spot + deposits
            ind = IndicesFX()
            ind_df = ind.create_total_return_index(cross, tenor, spot_df, deposit_df)
            ind_df.columns = [x + '.PYT (with carry)' for x in ind_df.columns]

            # grab total return index which we downloaded from Bloomberg
            bbg_ind_df = tot_df[cross + '.close'].to_frame()
            bbg_ind_df.columns = [x + ".BBG (with carry)" for x in bbg_ind_df.columns]

            # grab spot data
            spot_plot_df = spot_df[cross + '.close'].to_frame()
            spot_plot_df = tsc.create_mult_index_from_prices(spot_plot_df)

            # combine total return indices (computed by PyThalesians), those from Bloomberg and also spot
            # with everything already rebased at 100
            ind_df = ind_df.join(bbg_ind_df)
            ind_df = ind_df.join(spot_plot_df)

            gp = GraphProperties()
            gp.title = 'Total return indices in FX & comparing with spot'
            gp.scale_factor = 3

            pf = PlotFactory()
            pf.plot_line_graph(ind_df, adapter = 'pythalesians', gp = gp)