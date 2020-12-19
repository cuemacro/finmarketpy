__author__ = 'saeedamen' # Saeed Amen / saeed@cuemacro.com

#
# Copyright 2020 Cuemacro Ltd. - http//www.cuemacro.com / @cuemacro
#
# See the License for the specific language governing permissions and limitations under the License.
#
# This may not be distributed without the permission of Cuemacro.
#

import pandas as pd

from findatapy.market import Market, MarketDataRequest
from findatapy.timeseries import Calculations, Calendar
from findatapy.util.dataconstants import DataConstants

constants = DataConstants()

class FXForwardsCurve(object):
    """Constructs continuous forwards time series total return indices from underlying forwards contracts. Incomplete!

    """

    def __init__(self, market_data_generator=None, fx_forwards_trading_tenor='1M', roll_date=0, construct_via_currency='no',
                 fx_forwards_tenor=constants.fx_forwards_tenor, base_depos_tenor=constants.base_depos_tenor):

        self._market_data_generator = market_data_generator
        self._calculations = Calculations()
        self._calendar = Calendar()

        self._fx_forwards_trading_tenor = fx_forwards_trading_tenor
        self._roll_date = roll_date
        self._construct_via_currency = construct_via_currency
        self._fx_forwards_tenor = fx_forwards_tenor
        self._base_depos_tenor = base_depos_tenor

    def generate_key(self):
        from findatapy.market.ioengine import SpeedCache

        # Don't include any "large" objects in the key
        return SpeedCache().generate_key(self, ['_market_data_generator', '_calculations', '_calendar'])

    def fetch_continuous_time_series(self, md_request, market_data_generator, fx_forwards_trading_tenor=None,
                                     roll_date=None, construct_via_currency=None, fx_forwards_tenor=None, base_depos_tenor=None):

        if market_data_generator is None: market_data_generator = self._market_data_generator
        if fx_forwards_trading_tenor is None: fx_forwards_trading_tenor = self._fx_forwards_trading_tenor
        if roll_date is None: roll_date = self._roll_date
        if construct_via_currency is None: construct_via_currency = self._construct_via_currency
        if fx_forwards_tenor is None: fx_forwards_tenor = self._fx_forwards_tenor
        if base_depos_tenor is None: base_depos_tenor = self._base_depos_tenor

        # Eg. we construct EURJPY via EURJPY directly (note: would need to have sufficient forward data for this)
        if construct_via_currency == 'no':
            # Download FX spot, FX forwards points and base depos
            market = Market(market_data_generator=market_data_generator)

            md_request_download = MarketDataRequest(md_request=md_request)

            md_request_download.category = 'fx-forwards-market'
            md_request_download.fields = 'close'
            md_request_download.abstract_curve = None
            md_request_download.fx_forwards_tenor = fx_forwards_tenor
            md_request_download.base_depos_tenor = base_depos_tenor

            forwards_market_df = market.fetch_market(md_request_download)

            return self.construct_total_return_index(md_request.tickers, fx_forwards_trading_tenor, roll_date, forwards_market_df,
                                                     fx_forwards_tenor=fx_forwards_tenor, base_depos_tenor=base_depos_tenor)
        else:
            # eg. we calculate via your domestic currency such as USD, so returns will be in your domestic currency
            # Hence AUDJPY would be calculated via AUDUSD and JPYUSD (subtracting the difference in returns)
            total_return_indices = []

            for tick in md_request.tickers:
                base = tick[0:3]
                terms = tick[3:6]

                md_request_base = MarketDataRequest(md_request=md_request)
                md_request_base.tickers = base + construct_via_currency

                md_request_terms = MarketDataRequest(md_request=md_request)
                md_request_terms.tickers = terms + construct_via_currency

                base_vals = self.fetch_continuous_time_series(md_request_base, market_data_generator,
                                                              construct_via_currency='no')
                terms_vals = self.fetch_continuous_time_series(md_request_terms, market_data_generator,
                                                               construct_via_currency='no')

                # Special case for USDUSD case (and if base or terms USD are USDUSD
                if base + terms == 'USDUSD':
                    base_rets = self._calculations.calculate_returns(base_vals)
                    cross_rets = pd.DataFrame(0, index=base_rets.index, columns=base_rets.columns)
                elif base + 'USD' == 'USDUSD':
                    cross_rets = -self._calculations.calculate_returns(terms_vals)
                elif terms + 'USD' == 'USDUSD':
                    cross_rets = self._calculations.calculate_returns(base_vals)
                else:
                    base_rets = self._calculations.calculate_returns(base_vals)
                    terms_rets = self._calculations.calculate_returns(terms_vals)

                    cross_rets = base_rets.sub(terms_rets.iloc[:, 0], axis=0)

                # First returns of a time series will by NaN, given we don't know previous point
                cross_rets.iloc[0] = 0

                cross_vals = self._calculations.create_mult_index(cross_rets)
                cross_vals.columns = [tick + '-tot.close']

                total_return_indices.append(cross_vals)

            return self._calculations.pandas_outer_join(total_return_indices)

    def unhedged_asset_fx(self, assets_df, asset_currency, home_curr, start_date, finish_date, spot_df=None):
        pass

    def hedged_asset_fx(self, assets_df, asset_currency, home_curr, start_date, finish_date, spot_df=None,
                        total_return_indices_df=None):
        pass

    def get_day_count_conv(self, currency):
        if currency in ['AUD', 'CAD', 'GBP', 'NZD']:
            return 365.0

        return 360.0

    def construct_total_return_index(self, cross_fx, fx_forwards_trading_tenor, roll_date, forwards_market_df,
                                     fx_forwards_tenor=constants.fx_forwards_tenor, base_depos_tenor=constants.base_depos_tenor):

        if not (isinstance(cross_fx, list)):
            cross_fx = [cross_fx]

        total_return_index_agg = []

        # Remove columns where there is no data (because these points typically aren't quoted)
        forwards_market_df = forwards_market_df.dropna(axis=1)

        for cross in cross_fx:

            # Eg. if we specify USDUSD
            if cross[0:3] == cross[3:6]:
                total_return_index_agg.append(
                    pd.DataFrame(100, index=forwards_market_df.index, columns=[cross + "-tot.close"]))
            else:
                spot = forwards_market_df[cross + ".close"].to_frame()

                fx_forwards_tenor_pickout = []

                for f in fx_forwards_tenor:
                    if f + ".close" in fx_forwards_tenor:
                        fx_forwards_tenor_pickout.append(f)

                    if f == fx_forwards_trading_tenor:
                        break

                divisor = 10000.0

                if cross[3:6] == 'JPY':
                    divisor = 100.0

                forward_pts = forwards_market_df[[cross + x + ".close" for x in fx_forwards_tenor_pickout]].to_frame() \
                              / divisor

                outright = spot + forward_pts

                # Calculate the time difference between each data point
                spot['index_col'] = spot.index
                time = spot['index_col'].diff()
                spot = spot.drop('index_col', 1)

                total_return_index = pd.DataFrame(index=spot.index, columns=[cross + "-tot.close"])
                total_return_index.iloc[0] = 100

                time_diff = time.values.astype(float) / 86400000000000.0  # get time difference in days

                # TODO incomplete forwards calculations
                total_return_index_agg.append(total_return_index)

        return self._calculations.pandas_outer_join(total_return_index_agg)
