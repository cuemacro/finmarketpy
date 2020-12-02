__author__ = 'saeedamen' # Saeed Amen

#
# Copyright 2020 Cuemacro
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the
# License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the License for the specific language governing permissions and limitations under the License.
#

from financepy.market.curves.FinDiscountCurveFlat import FinDiscountCurveFlat
from financepy.market.volatility.FinFXVolSurface import FinFXVolSurface
from financepy.market.volatility.FinFXVolSurface import FinFXATMMethod
from financepy.market.volatility.FinFXVolSurface import FinFXDeltaMethod

from finmarketpy.volatility.abstractvolsurface import AbstractVolSurface
from finmarketpy.util.marketutil import MarketUtil

class FXVolSurface(AbstractVolSurface):
    """Holds data for an FX vol surface and also interpolates vol surface, converts strikes to implied vols etc.

    """

    def __init__(self, market_df=None, tenors=['ON', '1W', '2W', '3W', '1M', '2M', '3M', '4M', '6M', '9M', '1Y', '2Y', '3Y', '5Y']):
        self._market_df = market_df
        self._tenors = tenors
        self._market_util = MarketUtil()

        self._value_date = None
        self._fin_fx_vol_surface = None

    def build_vol_surface(self, value_date, asset=None, depo_tenor='1M', field='close', atm_method=FinFXATMMethod.FWD_DELTA_NEUTRAL,
        delta_method=FinFXDeltaMethod.SPOT_DELTA):
        """Builds the implied volatility for a particular value date and calculates the benchmark strikes etc.

        Before we do any sort of interpolation later, we need to build the implied vol surface.

        Parameters
        ----------
        value_date : str
            Value data (need to have market data for this date)

        asset : str
            Asset name

        depo_tenor : str
            Depo tenor to use

            default - '1M'

        field : str
            Market data field to use

            default - 'close'

        atm_method : FinFXATMMethod
            How is the ATM quoted? Eg. delta neutral, ATMF etc.

            default - FinFXATMMethod.FWD_DELTA_NEUTRAL

        delta_method : FinFXDeltaMethod
            Spot delta, forward delta etc.

            default - FinFXDeltaMethod.SPOT_DELTA
        """

        value_date = self._market_util.parse_date(value_date)

        self._value_date = value_date

        value_fin_date = self._findate(self._market_util.parse_date(value_date))

        tenors = self._tenors

        # Change ON (overnight) to 1D (convention for financepy)
        # tenors_financepy = list(map(lambda b: b.replace("ON", "1D"), self._tenors.copy()))
        tenors_financepy = self._tenors.copy()
        market_df = self._market_df

        field = '.' + field

        for_name_base = asset[0:3]
        dom_name_terms = asset[3:6]

        date_index = market_df.index == value_date

        # CAREFUL: need to divide by 100 for depo rate, ie. 0.0346 = 3.46%
        forCCRate = market_df[for_name_base + depo_tenor + field][date_index].values[0] / 100.0 # 0.03460  # EUR
        domCCRate = market_df[dom_name_terms + depo_tenor + field][date_index].values[0] / 100.0 # 0.02940  # USD

        dom_discount_curve = FinDiscountCurveFlat(value_fin_date, domCCRate)
        for_discount_curve = FinDiscountCurveFlat(value_fin_date, forCCRate)

        currency_pair = for_name_base + dom_name_terms
        spot_fx_rate = market_df[currency_pair + field][date_index].values[0]

        # For vols we do NOT need to divide by 100 (financepy does that internally)
        atm_vols = market_df[[currency_pair + "V" + t + field for t in tenors]][date_index].values[0]
        market_strangle25DeltaVols = market_df[[currency_pair + "25B" + t + field for t in tenors]][date_index].values[0] #[0.65, 0.75, 0.85, 0.90, 0.95, 0.85]
        risk_reversal25DeltaVols = market_df[[currency_pair + "25R" + t + field for t in tenors]][date_index].values[0] #[-0.20, -0.25, -0.30, -0.50, -0.60, -0.562]

        notional_currency = for_name_base

        # Construct financepy vol surface (uses polynomial interpolation for determining vol between strikes)
        self._fin_fx_vol_surface = FinFXVolSurface(value_fin_date,
                                   spot_fx_rate,
                                   currency_pair,
                                   notional_currency,
                                   dom_discount_curve,
                                   for_discount_curve,
                                   tenors_financepy,
                                   atm_vols,
                                   market_strangle25DeltaVols,
                                   risk_reversal25DeltaVols,
                                   atm_method,
                                   delta_method)

    def calculate_vol_for_strike_expiry(self, K, expiry_date=None, tenor='1M'):
        """Calculates the implied volatility for a given strike

        Parameters
        ----------
        K : float
            Strike for which to find implied volatility

        expiry_date : str (optional)
            Expiry date of option (TODO not implemented)

        tenor : str (optional)
            Tenor of option

            default - '1M'

        Returns
        -------

        """
        # TODO interpolate for broken dates, not just quoted tenors
        if tenor is not None:
            try:
                tenor_index = self._get_tenor_index(tenor)
                return self._fin_fx_vol_surface.volFunction(K, tenor_index)
            except:
                pass

        return None

    def extract_vol_surface(self, num_strike_intervals=60):
        """Creates an interpolated implied vol surface which can be plotted (in strike space), and also in delta
        space for key strikes (ATM, 25d call and put). Also for key strikes converts from delta to strike space.

        Parameters
        ----------
        num_strike_intervals : int
            Number of points to interpolate

        Returns
        -------
        dict
        """
        ## Modified from FinancePy code for plotting vol curves

        # columns = tenors
        df_vol_surface_strike_space = pd.DataFrame(columns=self._fin_fx_vol_surface._tenors)
        df_vol_surface_delta_space = pd.DataFrame(columns=self._fin_fx_vol_surface._tenors)

        # Conversion between main deltas and strikes
        df_deltas_vs_strikes = pd.DataFrame(columns=self._fin_fx_vol_surface._tenors)

        # ATM, 25d market strangle and 25d risk reversals
        df_vol_surface_quoted_points = pd.DataFrame(columns=self._fin_fx_vol_surface._tenors)

        # Note, at present we're not using 10d strikes
        quoted_strikes_names = ['ATM', 'STR_25_D_MS', 'RR_25_D_P']
        key_strikes_names = ['K_25_D_P', 'K_25_D_P_MS', 'ATM', 'K_25_D_C', 'K_25_D_C_MS']

        # Get max/min strikes to interpolate (from the longest dated tenor)
        low_K = self._fin_fx_vol_surface._K_25_D_P[-1] * 0.95
        high_K = self._fin_fx_vol_surface._K_25_D_C[-1] * 1.05

        for tenor_index in range(0, self._fin_fx_vol_surface._numVolCurves):

            # Get the quoted vol points
            tenor_label = self._fin_fx_vol_surface._tenors[tenor_index]

            atm_vol = self._fin_fx_vol_surface._atmVols[tenor_index] * 100
            ms_vol = self._fin_fx_vol_surface._mktStrangle25DeltaVols[tenor_index] * 100
            rr_vol = self._fin_fx_vol_surface._riskReversal25DeltaVols[tenor_index] * 100

            df_vol_surface_quoted_points[tenor_label] = pd.Series(index=quoted_strikes_names, data=[atm_vol, ms_vol, rr_vol])

            # Do interpolation in strike space for the implied vols
            strikes = []
            vols = []

            K = low_K
            dK = (high_K - low_K) / num_strike_intervals

            for i in range(0, num_strike_intervals):
                sigma = self._fin_fx_vol_surface.volFunction(K, tenor_index) * 100.0
                strikes.append(K)
                vols.append(sigma)
                K = K + dK

            df_vol_surface_strike_space[tenor_label] = pd.Series(index=strikes, data=vols)

            # Extract strikes for the quoted points (ie. 25d and ATM)
            key_strikes = []
            key_strikes.append(self._fin_fx_vol_surface._K_25_D_P[tenor_index])
            key_strikes.append(self._fin_fx_vol_surface._K_25_D_P_MS[tenor_index])
            key_strikes.append(self._fin_fx_vol_surface._K_ATM[tenor_index])
            key_strikes.append(self._fin_fx_vol_surface._K_25_D_C[tenor_index])
            key_strikes.append(self._fin_fx_vol_surface._K_25_D_C_MS[tenor_index])

            df_deltas_vs_strikes[tenor_label] = pd.Series(index=key_strikes_names, data=key_strikes)

            # Put a conversion between quoted deltas and strikes (eg. which is ATM in strike space, 25d call/put strikes)
            key_vols = []

            for K, name in zip(key_strikes, key_strikes_names):
                sigma = self._fin_fx_vol_surface.volFunction(K, tenor_index) * 100.0
                key_vols.append(sigma)

            df_vol_surface_delta_space[tenor_label] = pd.Series(index=key_strikes_names, data=key_vols)

        df_vol_dict = {}
        df_vol_dict['vol_surface_strike_space'] = df_vol_surface_strike_space
        df_vol_dict['vol_surface_delta_space'] = df_vol_surface_delta_space
        df_vol_dict['vol_surface_quoted_points'] = df_vol_surface_quoted_points
        df_vol_dict['deltas_vs_strikes'] = df_deltas_vs_strikes

        return df_vol_dict

    def get_atm_strike(self, tenor=None):
        return self._fin_fx_vol_surface._K_ATM[self._get_tenor_index(tenor)]

    def get_25d_call_strike(self, tenor=None):
        return self._fin_fx_vol_surface._K_25_D_C[self._get_tenor_index(tenor)]

    def get_25d_put_strike(self, tenor=None):
        return self._fin_fx_vol_surface._K_25_D_P[self._get_tenor_index(tenor)]

    def get_10d_call_strike(self, tenor=None):
        pass

    def get_10d_put_strike(self, tenor=None):
        pass

    def get_25d_call_ms_strike(self, tenor=None):
        return self._fin_fx_vol_surface._K_25_D_C_MS[self._get_tenor_index(tenor)]

    def get_25d_put_ms_strike(self, tenor=None):
        return self._fin_fx_vol_surface._K_25_D_P_MS[self._get_tenor_index(tenor)]

    def get_10d_call_ms_strike(self, expiry_date=None, tenor=None):
        pass

    def get_10d_put_ms_strike(self, expiry_date=None, tenor=None):
        pass

    def get_atm_vol(self, expiry_date=None, tenor=None):
        pass

    def get_25d_call_vol(self, expiry_date=None, tenor=None):
        pass

    def get_25d_put_vol(self, expiry_date=None, tenor=None):
        pass

    def get_10d_call_vol(self, expiry_date=None, tenor=None):
        pass

    def get_10d_put_vol(self, expiry_date=None, tenor=None):
        pass

    def plot_vol_curves(self):
        if self._fin_fx_vol_surface is not None:
            self._fin_fx_vol_surface.plotVolCurves()

if __name__ == '__main__':
    from findatapy.market import Market, MarketDataRequest, MarketDataGenerator

    ticker = 'EURUSD'
    start_date = '06 Oct 2020'
    md_request = MarketDataRequest(start_date=start_date, finish_date=start_date, data_source='bloomberg', cut='LDN', category='fx-vol-market',
                                   tickers=ticker)

    import os
    import pandas as pd

    if os.path.exists(ticker + '.parquet'):
        market_df = pd.read_parquet(ticker + '.parquet')
    else:
        market_df = Market(market_data_generator=MarketDataGenerator()).fetch_market(md_request)

        market_df.to_parquet(ticker + '.parquet')

    fx_vol_surface = FXVolSurface(market_df=market_df)

    fx_vol_surface.build_vol_surface(start_date, asset='EURUSD')