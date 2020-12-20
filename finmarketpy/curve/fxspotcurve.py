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


import pandas as pd

from findatapy.market import Market, MarketDataRequest
from findatapy.timeseries import Calculations

class FXSpotCurve(object):
    """Construct total return (spot) indices for FX. In future will also convert assets from local currency to foreign currency
    denomination and construct indices from forwards series.

    """

    def __init__(self, market_data_generator=None, depo_tenor='ON', construct_via_currency='no'):
        self._market_data_generator = market_data_generator
        self._calculations = Calculations()

        self._depo_tenor = depo_tenor
        self._construct_via_currency = construct_via_currency

    def generate_key(self):
        from findatapy.market.ioengine import SpeedCache

        # Don't include any "large" objects in the key
        return SpeedCache().generate_key(self, ['_market_data_generator', '_calculations'])

    def fetch_continuous_time_series(self, md_request, market_data_generator, construct_via_currency=None):

        if market_data_generator is None:
            market_data_generator = self._market_data_generator

        if construct_via_currency is None:
            construct_via_currency = self._construct_via_currency

        # Eg. we construct AUDJPY via AUDJPY directly
        if construct_via_currency == 'no':
            base_depo_tickers = [x[0:3] + self._depo_tenor for x in md_request.tickers]
            terms_depo_tickers = [x[3:6] + self._depo_tenor for x in md_request.tickers]

            depo_tickers = list(set(base_depo_tickers + terms_depo_tickers))

            market = Market(market_data_generator=market_data_generator)

            # Deposit data for base and terms currency
            md_request_download = MarketDataRequest(md_request=md_request)

            md_request_download.tickers = depo_tickers
            md_request_download.category = 'base-depos'
            md_request_download.fields = 'close'
            md_request_download.abstract_curve = None

            depo_df = market.fetch_market(md_request_download)

            # Spot data
            md_request_download.tickers = md_request.tickers
            md_request_download.category = 'fx'

            spot_df = market.fetch_market(md_request_download)

            return self.construct_total_return_index(md_request.tickers, self._depo_tenor, spot_df, depo_df)
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

                base_vals = self.fetch_continuous_time_series(md_request_base, market_data_generator, construct_via_currency='no')
                terms_vals = self.fetch_continuous_time_series(md_request_terms, market_data_generator, construct_via_currency='no')

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

    def hedged_asset_fx(self, assets_df, asset_currency, home_curr, start_date, finish_date, spot_df=None, total_return_indices_df=None):
        pass

    def get_day_count_conv(self, currency):
        if currency in ['AUD', 'CAD', 'GBP', 'NZD']:
            return 365.0

        return 360.0

    def construct_total_return_index(self, cross_fx, tenor, spot_df, deposit_df):
        """Creates total return index for selected FX crosses from spot and deposit data

        Parameters
        ----------
        cross_fx : String
            Crosses to construct total return indices (can be a list)
        tenor : String
            Tenor of deposit rates to use to compute carry (typically ON for spot)
        spot_df : pd.DataFrame
            Spot data (must include crosses we select)
        deposit_df : pd.DataFrame
            Deposit data

        Returns
        -------
        pd.DataFrame
        """
        if not (isinstance(cross_fx, list)):
            cross_fx = [cross_fx]

        total_return_index_agg = []

        for cross in cross_fx:
            # Get the spot series, base deposit
            base_deposit = deposit_df[cross[0:3] + tenor + ".close"].to_frame()
            terms_deposit = deposit_df[cross[3:6] + tenor + ".close"].to_frame()

            # Eg. if we specify USDUSD
            if cross[0:3] == cross[3:6]:
                total_return_index_agg.append(pd.DataFrame(100, index=base_deposit.index, columns=[cross + "-tot.close"]))
            else:
                carry = base_deposit.join(terms_deposit, how='inner')

                spot = spot_df[cross + ".close"].to_frame()

                base_daycount = self.get_day_count_conv(cross[0:3])
                terms_daycount = self.get_day_count_conv(cross[4:6])

                # Align the base & terms deposits series to spot
                spot, carry = spot.align(carry, join='left', axis=0)

                # Sometimes depo data can be patchy, ok to fill down, given not very volatile (don't do this with spot!)
                carry = carry.fillna(method='ffill') / 100.0

                # In case there are values missing at start of list (fudge for old data!)
                carry = carry.fillna(method='bfill')

                spot = spot[cross + ".close"].to_frame()
                base_deposit = carry[base_deposit.columns]
                terms_deposit = carry[terms_deposit.columns]

                # Calculate the time difference between each data point
                spot['index_col'] = spot.index
                time = spot['index_col'].diff()
                spot = spot.drop('index_col', 1)

                total_return_index = pd.DataFrame(index=spot.index, columns=[cross + "-tot.close"])
                total_return_index.iloc[0] = 100

                time_diff = time.values.astype(float) / 86400000000000.0  # get time difference in days

                for i in range(1, len(total_return_index.index)):

                    # TODO vectorise this formulae or use Numba
                    # Calculate total return index as product of yesterday, changes in spot and carry accrued
                    total_return_index.values[i] = total_return_index.values[i - 1] * \
                                                   (1 + (1 + base_deposit.values[i] * time_diff[i] / base_daycount) *
                                                    (spot.values[i] / spot.values[i - 1]) \
                                                    - (1 + terms_deposit.values[i] * time_diff[i] / terms_daycount))

                total_return_index_agg.append(total_return_index)

        return self._calculations.pandas_outer_join(total_return_index_agg)
