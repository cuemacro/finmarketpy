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


"""
IndicesFX

Construct total return (spot) indices for FX. In future will also convert assets from local currency to foreign currency
denomination and construct indices from forwards series.

"""

from pythalesians.timeseries.calcs.timeseriescalcs import TimeSeriesCalcs

import pandas

class IndicesFX:

    def create_total_return_indices(self, crosses, spot, deposit, start_date, finish_date, home_curr = "USD"):
        pass

    def unhedged_asset_fx(self, assets, spot, asset_currency, home_curr, start_date, finish_date):
        pass

    def hedged_asset_fx(self, assets, total_return_indices, spot, asset_currency, home_curr, start_date, finish_date):
        pass

    def get_day_count_conv(self, currency):
        if currency in ['AUD', 'CAD', 'GBP', 'NZD']:
            return 365.0

        return 360.0

    def create_total_return_index(self, cross_fx, tenor, spot_df, deposit_df):
        """
        create_total_return_index - Creates total return index for selected FX crosses from spot and deposit data

        Parameters
        ----------
        cross_fx : String
            Crosses to construct total return indices (can be a list)

        tenor : String
            Tenor of deposit rates to use to compute carry (typically ON for spot)

        spot_df : pandas.DataFrame
            Spot data (must include crosses we select)

        deposit_df : pandas.DataFrame
            Deposit data
        """
        if not(isinstance(cross_fx, list)):
            cross_fx = [cross_fx]

        total_return_index_agg = None

        for cross in cross_fx:
            # get the spot series, base deposit
            spot = spot_df[cross + ".close"].to_frame()
            base_deposit = deposit_df[cross[0:3] + tenor + ".close"].to_frame()
            terms_deposit = deposit_df[cross[3:6] + tenor + ".close"].to_frame()
            carry = base_deposit.join(terms_deposit, how='inner')


            base_daycount = self.get_day_count_conv(cross[0:3])
            terms_daycount = self.get_day_count_conv(cross[4:6])

            # align the base & terms deposits series to spot
            spot, carry = spot.align(carry, join='left', axis = 0)
            carry = carry.fillna(method = 'ffill') / 100.0
            spot = spot[cross + ".close"].to_frame()
            base_deposit = carry[base_deposit.columns]
            terms_deposit = carry[terms_deposit.columns]

            # calculate the time difference between each data point
            spot['index_col'] = spot.index
            time = spot['index_col'].diff()
            spot = spot.drop('index_col', 1)

            total_return_index = pandas.DataFrame(index = spot.index, columns = spot.columns)
            total_return_index.iloc[0] = 100

            for i in range(1, len(total_return_index.index)):
                time_diff = time.values[i].astype(float) / 86400000000000.0 # get time difference in days

                # TODO vectorise this formulae
                # calculate total return index as product of yesterday, changes in spot and carry accrued
                total_return_index.values[i] = total_return_index.values[i-1] * \
                                        (1 + (1 + base_deposit.values[i] * time_diff/base_daycount)*
                                              (spot.values[i]/spot.values[i-1]) \
                                        - (1+ terms_deposit.values[i]*time_diff/terms_daycount))

            if total_return_index_agg is None:
                total_return_index_agg = total_return_index
            else:
                total_return_index_agg = total_return_index_agg.join(total_return_index, how = 'outer')

        return total_return_index_agg

if __name__ == '__main__':
    pass
    # see pythalesians_examples/markets/indicesfx_examples.py