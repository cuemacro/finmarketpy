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

import numpy as np
import pandas as pd

from numba import guvectorize

from findatapy.timeseries import Calendar
from finmarketpy.util.marketconstants import MarketConstants
from finmarketpy.curve.abstractpricer import AbstractPricer

market_constants = MarketConstants()

@guvectorize(['void(f8[:], f8[:], f8[:,:], f8[:,:], intp, f8[:])'],
             '(n),(n),(n,m),(n,m),()->(n)', cache=True, target="cpu", nopython=True)
def _forwards_interpolate_numba(spot_arr, spot_delivery_days_arr, quoted_delivery_days_arr,
                          forwards_points_arr, no_of_tenors, out):

    for i, delivery_day in enumerate(spot_delivery_days_arr):
        for j in range(no_of_tenors):

            # curr_forward_pts = forwards_points_arr[i, j]
            # curr_delivery_days = quoted_delivery_days_arr[i, j]
            # next_forward_pts = forwards_points_arr[i, j+1]
            # next_delivery_days = quoted_delivery_days_arr[i, j+1]

            # In other words, SP (Spot)
            if delivery_day == 0:
                out[i] = spot_arr[i]

                break

            # Say if we're in between SP and 1W
            elif delivery_day <= quoted_delivery_days_arr[i, j]:
                out[i] = spot_arr[i] + (forwards_points_arr[i, j] / quoted_delivery_days_arr[i, j]) * delivery_day

                break
            # Eg. if we're in between 1W and 2W
            elif delivery_day >= quoted_delivery_days_arr[i, j] and delivery_day <= quoted_delivery_days_arr[i, j + 1]:

                # Alternative interpolation
                # interpolated_forwards_arr[i] = spot_arr[i] + \
                #                                delivery_day * (forwards_points_arr[i, j+1] - forwards_points_arr[i, j]) \
                #                                / (quoted_delivery_days_arr[i, j+1] - quoted_delivery_days_arr[i, j])

                forward_points_per_day = (forwards_points_arr[i, j + 1] - forwards_points_arr[i, j]) \
                                         / (quoted_delivery_days_arr[i, j + 1] - quoted_delivery_days_arr[i, j])

                out[i] = spot_arr[i] + forward_points_per_day * delivery_day \
                                     + forwards_points_arr[i, j] - (forward_points_per_day * quoted_delivery_days_arr[i, j])

                break


@guvectorize(['void(f8[:], f8[:,:], f8[:,:], f8[:,:], f8, f8, intp, f8[:,:])'],
             '(n),(n,m),(n,m),(n,m),(),(),()->(n,m)', cache=True, target="cpu", nopython=True)
def _infer_base_currency_depo_numba(spot_arr, outright_forwards_arr, depo_arr, quoted_delivery_days_arr,
                                    base_conv, terms_conv, no_of_tenors, out):
    for i in range(len(out)):
        for j in range(no_of_tenors):
            out[i, j] = (((1 + depo_arr[i, j] * (quoted_delivery_days_arr[i, j] / terms_conv))
                                       / (outright_forwards_arr[i, j] / spot_arr[i])) - 1) \
                                     / (quoted_delivery_days_arr[i, j] / base_conv)

@guvectorize(['void(f8[:], f8[:,:], f8[:,:], f8[:,:], f8, f8, intp, f8[:,:])'],
             '(n),(n,m),(n,m),(n,m),(),(),()->(n,m)', cache=True, target="cpu", nopython=True)
def _infer_terms_currency_depo_numba(spot_arr, outright_forwards_arr, depo_arr, quoted_delivery_days_arr,
                                    base_conv, terms_conv, no_of_tenors, out):

    for i in range(len(out)):
         for j in range(no_of_tenors):
             out[i,j] = ((outright_forwards_arr[i,j] / spot_arr[i]) *
                                      (1 + depo_arr[i,j] * (quoted_delivery_days_arr[i,j] / base_conv)) - 1) \
                                     / (quoted_delivery_days_arr[i,j] / terms_conv)

def _forwards_interpolate(spot_arr, spot_delivery_days_arr, quoted_delivery_days_arr,
                          forwards_points_arr, no_of_tenors):

    out = np.zeros(len(quoted_delivery_days_arr)) * np.nan

    for i, delivery_day in enumerate(spot_delivery_days_arr):
        for j in range(no_of_tenors):

            # curr_forward_pts = forwards_points_arr[i, j]
            # curr_delivery_days = quoted_delivery_days_arr[i, j]
            # next_forward_pts = forwards_points_arr[i, j+1]
            # next_delivery_days = quoted_delivery_days_arr[i, j+1]

            # In other words, SP (Spot)
            if delivery_day == 0:
                out[i] = spot_arr[i]

                break

            # Say if we're in between SP and 1W
            elif delivery_day <= quoted_delivery_days_arr[i, j]:
                out[i] = spot_arr[i] + (forwards_points_arr[i, j] / quoted_delivery_days_arr[i, j]) * delivery_day

                break
            # Eg. if we're in between 1W and 2W
            elif delivery_day >= quoted_delivery_days_arr[i, j] and delivery_day <= quoted_delivery_days_arr[i, j + 1]:

                # Alternative interpolation
                # interpolated_forwards_arr[i] = spot_arr[i] + \
                #                                delivery_day * (forwards_points_arr[i, j+1] - forwards_points_arr[i, j]) \
                #                                / (quoted_delivery_days_arr[i, j+1] - quoted_delivery_days_arr[i, j])

                forward_points_per_day = (forwards_points_arr[i, j + 1] - forwards_points_arr[i, j]) \
                                         / (quoted_delivery_days_arr[i, j + 1] - quoted_delivery_days_arr[i, j])

                out[i] = spot_arr[i] + forward_points_per_day * delivery_day \
                                     + forwards_points_arr[i, j] - (forward_points_per_day * quoted_delivery_days_arr[i, j])

                break

    return out

class FXForwardsPricer(AbstractPricer):
    """Prices forwards for odd dates which are not quoted using linear interpolation,
    eg. if we have forward points for 1W and 1M, and spot date but we want to price a 3W forward, or any arbitrary horizon
    date that lies in that interval

    Also calculates the implied deposit rate from FX spot, FX forward points and deposit rate.
    """

    def __init__(self, market_df=None, quoted_delivery_df=None):
        self._calendar = Calendar()
        self._market_df = market_df
        self._quoted_delivery_df = quoted_delivery_df

    def price_instrument(self, cross, horizon_date, delivery_date, option_expiry_date=None, market_df=None, quoted_delivery_df=None,
                         fx_forwards_tenor_for_interpolation=market_constants.fx_forwards_tenor_for_interpolation,
                         return_as_df=True):
        """Creates an interpolated outright FX forward (and the associated points), for horizon dates/delivery dates
        given by the user from FX spot rates and FX forward points. This can be useful when we have an odd/broken date
        which isn't quoted.

        Uses linear interpolation between quoted dates to calculate the appropriate interpolated forward. Eg. if we
        ask for a delivery date in between 1W and 1M, we will interpolate between those.

        Parameters
        ----------
        cross : str
            Currency pair

        horizon_date : DateTimeIndex
            Horizon dates for forward contracts

        delivery_date : DateTimeIndex
            Delivery dates for forward contracts

        market_df : DataFrame
            Contains FX spot and FX forward points data

        quoted_delivery_df : DataFrame (DateTimeIndex)
            Delivery dates for every quoted forward point

        fx_forwards_tenor_for_interpolation : str(list)
            Which forwards to use for interpolation

        Returns
        -------
        DataFrame
        """

        if market_df is None: market_df = self._market_df
        if quoted_delivery_df is None: quoted_delivery_df = self._quoted_delivery_df

        if quoted_delivery_df is None:
            quoted_delivery_df = self.generate_quoted_delivery(cross, market_df, quoted_delivery_df,
                                                               fx_forwards_tenor_for_interpolation, cross)

        # Make horizon date and delivery date pandas DatetimeIndex
        if isinstance(horizon_date, pd.Timestamp):
            horizon_date = pd.DatetimeIndex([horizon_date])
            delivery_date = pd.DatetimeIndex([delivery_date])
        else:
            horizon_date = pd.DatetimeIndex(horizon_date)
            delivery_date = pd.DatetimeIndex(delivery_date)

        # Truncate the market data so covers only the dates where we want to price the forwards
        market_df = market_df[market_df.index.isin(horizon_date)]
        quoted_delivery_df = quoted_delivery_df[quoted_delivery_df.index.isin(horizon_date)]

        cal = cross

        # Get the spot date (different currency pairs have different conventions for this!)
        spot_date = self._calendar.get_spot_date_from_horizon_date(horizon_date, cal)

        # How many days between spot date (typically T+1 or T+2) and delivery date
        spot_delivery_days_arr = (delivery_date - spot_date).days

        spot_arr = market_df[cross + '.close'].values

        quoted_delivery_df, quoted_delivery_days_arr, forwards_points_arr, divisor = \
            self._setup_forwards_calculation(cross, spot_date, market_df, quoted_delivery_df, fx_forwards_tenor_for_interpolation)

        interpolated_outright_forwards_arr = _forwards_interpolate_numba(spot_arr, spot_delivery_days_arr, quoted_delivery_days_arr,
                          forwards_points_arr, len(fx_forwards_tenor_for_interpolation))

        if return_as_df:
            interpolated_df = pd.DataFrame(index=market_df.index,
                                columns=[cross + '-interpolated-outright-forward.close', cross + "-interpolated-forward-points.close"])

            interpolated_df[cross + '-interpolated-outright-forward.close'] = interpolated_outright_forwards_arr
            interpolated_df[cross + "-interpolated-forward-points.close"] = (interpolated_outright_forwards_arr - spot_arr) * divisor

            return interpolated_df

        return interpolated_outright_forwards_arr

    def get_day_count_conv(self, currency):
        if currency in market_constants.currencies_with_365_basis:
            return 365.0

        return 360.0

    def get_forwards_divisor(self, currency):
        # Typically most divisors of forward points are 10000.0
        divisor = 10000.0

        if currency in market_constants.fx_forwards_points_divisor_100:
            divisor = 100.0

        if currency in market_constants.fx_forwards_points_divisor_1000:
            divisor = 1000.0

        return divisor

    def _setup_forwards_calculation(self, cross, spot_date, market_df, quoted_delivery_df, fx_forwards_tenor):

        cal = cross

        # Get the quoted delivery dates for every quoted tenor in our forwards market data
        # Eg. what's the delivery date for EURUSD SN, 1W etc.
        quoted_delivery_df = self.generate_quoted_delivery(cross, market_df, quoted_delivery_df,
                                                           fx_forwards_tenor, cal)

        # Typically most divisors of forward points are 10000.0 (but JPY is an exception)
        divisor = self.get_forwards_divisor(cross[3:6])

        forwards_points_arr = market_df[
                                  [cross + x + ".close" for x in fx_forwards_tenor]].values / divisor

        quoted_delivery_days_arr = np.zeros((len(quoted_delivery_df.index), len(fx_forwards_tenor)))

        # Get difference between each quoted point and the spot date (NOT horizon date)
        # eg. for 1W this is generally 7 days, for 2W it's 14 days etc.
        for i, tenor in enumerate(fx_forwards_tenor):
            quoted_delivery_days_arr[:, i] = (
                        pd.DatetimeIndex(quoted_delivery_df[cross + tenor + ".delivery"]) - spot_date).days

        return quoted_delivery_df, quoted_delivery_days_arr, forwards_points_arr, divisor

    def generate_quoted_delivery(self, cross, market_df, quoted_delivery_df, fx_forwards_tenor, cal):

        if not(isinstance(fx_forwards_tenor, list)):
            fx_forwards_tenor = [fx_forwards_tenor]

        # Get the quoted delivery dates for every quoted tenor in our forwards market data
        # Eg. what's the delivery date for EURUSD SN, 1W etc.
        if quoted_delivery_df is None:
            quoted_delivery_df = pd.DataFrame(index=market_df.index,
                                              columns=[cross + tenor + ".delivery" for tenor in
                                                       fx_forwards_tenor])


            for tenor in fx_forwards_tenor:
                quoted_delivery_df[cross + tenor + ".delivery"] = \
                    self._calendar.get_delivery_date_from_horizon_date(quoted_delivery_df.index, tenor, cal=cal)

        return quoted_delivery_df

    def calculate_implied_depo(self, cross, implied_currency, market_df=None, quoted_delivery_df=None,
                               fx_forwards_tenor=market_constants.fx_forwards_trading_tenor,
                               depo_tenor=None):
        """Calculates implied deposit rates for a particular currency from spot, forward points and deposit rate
        for the other currency. Uses the theory of covered interest rate parity.

        See BIS publication from 2016, Covered interest parity lost: understanding the cross-currency basis downloadable from
        https://www.bis.org/publ/qtrpdf/r_qt1609e.pdf for an explanation

        Eg. using EURUSD spot, EURUSD 1W forward points and USDON deposit rate, we can calculate the implied deposit
        for EUR 1W

        Parameters
        ----------
        cross : str
            Currency pair

        implied_currency : str
            Currency for which we want to imply deposit

        market_df : DataFrame
            With FX spot rate, FX forward points and deposit rates

        fx_forwards_tenor : str (list)
            Tenors of forwards where we want to imply deposit

        depo_tenor : str
            Deposit rate to use (default - ON)

        Returns
        -------
        DataFrame
        """

        if not(isinstance(fx_forwards_tenor, list)):
            fx_forwards_tenor = [fx_forwards_tenor]

        if market_df is None: market_df = self._market_df
        if quoted_delivery_df is None: quoted_delivery_df = self._quoted_delivery_df
        if depo_tenor is None: depo_tenor = fx_forwards_tenor

        if not(isinstance(depo_tenor, list)):
            depo_tenor = [depo_tenor] * len(fx_forwards_tenor)

        cal = cross

        # Get the spot date (different currency pairs have different conventions for this!)
        spot_date = self._calendar.get_spot_date_from_horizon_date(market_df.index, cal)

        quoted_delivery_df, quoted_delivery_days_arr, forwards_points_arr, divisor = \
            self._setup_forwards_calculation(cross, spot_date, market_df, quoted_delivery_df,
                                             fx_forwards_tenor)

        spot_arr = market_df[cross + '.close'].values

        outright_forwards_arr = np.vstack([spot_arr]*len(fx_forwards_tenor)).T + forwards_points_arr

        base_conv = self.get_day_count_conv(cross[0:3])
        terms_conv = self.get_day_count_conv(cross[3:6])

        # Infer base currency
        if implied_currency == cross[0:3]:
            original_currency = cross[3:6]

            depo_arr = market_df[[original_currency + d + '.close' for d in depo_tenor]].values / 100.0

            implied_depo_arr = _infer_base_currency_depo_numba(spot_arr, outright_forwards_arr, depo_arr, quoted_delivery_days_arr,
                                    base_conv, terms_conv, len(fx_forwards_tenor))

            # for i in range(len(implied_depo_arr)):
            #     for j, tenor in enumerate(fx_forwards_tenor):
            #         implied_depo_arr[i, j] = (((1 + depo_arr[i,j] * (quoted_delivery_days_arr[i, j] / terms_conv))
            #                                    / (outright_forwards_arr[i,j] / spot_arr[i])) - 1) \
            #                                  / (quoted_delivery_days_arr[i, j] / base_conv)

        # Infer terms currency
        if implied_currency == cross[3:6]:
            original_currency = cross[0:3]

            depo_arr = market_df[[original_currency + d + '.close' for d in depo_tenor]].values / 100.0

            implied_depo_arr = _infer_terms_currency_depo_numba(spot_arr, outright_forwards_arr, depo_arr, quoted_delivery_days_arr,
                                    base_conv, terms_conv, len(fx_forwards_tenor))

            # for i in range(len(implied_depo_arr)):
            #     for j, tenor in enumerate(fx_forwards_tenor):
            #         implied_depo_arr[i,j] = ((outright_forwards_arr[i,j] / spot_arr[i]) *
            #                                  (1 + depo_arr[i,j] * (quoted_delivery_days_arr[i,j] / base_conv)) - 1) \
            #                                 / (quoted_delivery_days_arr[i,j] / terms_conv)

        return pd.DataFrame(index=market_df.index,
                            columns=[implied_currency + x + "-implied-depo.close" for x in fx_forwards_tenor],
                            data=implied_depo_arr * 100.0)