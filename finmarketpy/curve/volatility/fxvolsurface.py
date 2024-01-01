__author__ = "saeedamen"

#
# Copyright 2020 Cuemacro
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.
#


import pandas as pd
import numpy as np

from financepy.market.curves.discount_curve_flat import DiscountCurveFlat
from financepy.utils.date import Date

# Tested with financepy 0.310 only

from financepy.market.volatility.fx_vol_surface_plus import \
    FXVolSurfacePlus \
        as FinFXVolSurface  # So there is no clash with FXVolSurface from finmarketpy
from financepy.market.volatility.fx_vol_surface_plus import FinFXATMMethod
from financepy.market.volatility.fx_vol_surface_plus import \
    FinFXDeltaMethod
from financepy.market.volatility.fx_vol_surface_plus import vol_function
from financepy.market.volatility.fx_vol_surface_plus import \
    VolFunctionTypes

from financepy.utils.global_types import FinSolverTypes

from findatapy.util.dataconstants import DataConstants

from finmarketpy.curve.volatility.abstractvolsurface import AbstractVolSurface
from finmarketpy.util.marketconstants import MarketConstants
from finmarketpy.util.marketutil import MarketUtil

data_constants = DataConstants()
market_constants = MarketConstants()


class FXVolSurface(AbstractVolSurface):
    """Holds data for an FX vol surface and also interpolates vol surface,
    converts strikes to implied vols etc.

    """

    def __init__(self, market_df=None, asset=None, field="close",
                 tenors=market_constants.fx_options_tenor_for_interpolation,
                 vol_function_type=market_constants.fx_options_vol_function_type,
                 atm_method=market_constants.fx_options_atm_method,
                 delta_method=market_constants.fx_options_delta_method,
                 depo_tenor=market_constants.fx_options_depo_tenor,
                 solver=market_constants.fx_options_solver,
                 alpha=market_constants.fx_options_alpha,
                 tol=market_constants.fx_options_tol):
        """Initialises object, with market data and various market conventions

        Parameters
        ----------
        market_df : DataFrame
            Market data with spot, FX volatility surface, FX forwards and base depos

        asset : str
            Eg. "EURUSD"

        field : str
            Market data field to use

            default - "close"

        tenors : str(list)
            Tenors to be used (we need to avoid tenors, where there might be NaNs)

        vol_function_type : str
            What type of interpolation scheme to use
            default - "CLARK5" (also "CLARK", "BBG" and "SABR")

        atm_method : str
            How is the ATM quoted? Eg. delta neutral, ATMF etc.

            default - "fwd-delta-neutral-premium-adj"

        delta_method : str
            Spot delta, forward delta etc.

            default - "spot-delta"

        solver : str
            Which solver to use in FX vol surface calibration?

            default - "nelmer-mead"

        alpha : float
            Between 0 and 1 (default 0.5)
        """
        self._market_df = market_df
        self._tenors = tenors
        self._asset = asset
        self._field = field
        self._depo_tenor = depo_tenor
        self._market_util = MarketUtil()

        self._dom_discount_curve = None
        self._for_discount_curve = None
        self._spot = None

        self._value_date = None
        self._fin_fx_vol_surface = None
        self._df_vol_dict = None

        for_name_base = asset[0:3]
        dom_name_terms = asset[3:6]

        field = "." + field

        # CAREFUL: need to divide by 100 for depo rate, ie. 0.0346 = 3.46%
        self._forCCRate = market_df[
                              for_name_base + depo_tenor + field].values / 100.0  # 0.03460  # EUR
        self._domCCRate = market_df[
                              dom_name_terms + depo_tenor + field].values / 100.0  # 0.02940  # USD

        self._spot_history = market_df[asset + field].values
        self._atm_vols = market_df[
            [asset + "V" + t + field for t in tenors]].values
        self._market_strangle25DeltaVols = market_df[
            [asset + "25B" + t + field for t in tenors]].values
        self._risk_reversal25DeltaVols = market_df[
            [asset + "25R" + t + field for t in tenors]].values
        self._market_strangle10DeltaVols = market_df[
            [asset + "10B" + t + field for t in tenors]].values
        self._risk_reversal10DeltaVols = market_df[
            [asset + "10R" + t + field for t in tenors]].values

        if vol_function_type == "CLARK":
            self._vol_function_type = VolFunctionTypes.CLARK
        elif vol_function_type == "CLARK5":
            self._vol_function_type = VolFunctionTypes.CLARK5
        elif vol_function_type == "BBG":
            self._vol_function_type = VolFunctionTypes.BBG

        # Note: currently SABR isn"t fully implemented in FinancePy
        elif vol_function_type == "SABR":
            self._vol_function_type = VolFunctionTypes.SABR
        elif vol_function_type == "SABR3":
            self._vol_function_type = VolFunctionTypes.SABR3

        # What does ATM mean? (for most
        if atm_method == "fwd-delta-neutral":  # ie. strike such that a straddle would be delta neutral
            self._atm_method = FinFXATMMethod.FWD_DELTA_NEUTRAL
        elif atm_method == "fwd-delta-neutral-premium-adj":
            self._atm_method = FinFXATMMethod.FWD_DELTA_NEUTRAL_PREM_ADJ
        elif atm_method == "spot":  # ATM is spot
            self._atm_method = FinFXATMMethod.SPOT
        elif atm_method == "fwd":  # ATM is forward
            self._atm_method = FinFXATMMethod.FWD

        # How are the deltas quoted?
        if delta_method == "spot-delta":
            self._delta_method = FinFXDeltaMethod.SPOT_DELTA
        elif delta_method == "fwd-delta":
            self._delta_method = FinFXDeltaMethod.FORWARD_DELTA
        elif delta_method == "spot-delta-prem-adj":
            self._delta_method = FinFXDeltaMethod.SPOT_DELTA_PREM_ADJ
        elif delta_method == "fwd-delta-prem-adj":
            self._delta_method = FinFXDeltaMethod.FORWARD_DELTA_PREM_ADJ

        # Which solver to use in FX vol surface calibration
        if solver == "nelmer-mead":
            self._solver = FinSolverTypes.NELDER_MEAD
        elif solver == "nelmer-mead-numba":
            self._solver = FinSolverTypes.NELDER_MEAD_NUMBA
        elif solver == "cg":
            self._solver = FinSolverTypes.CONJUGATE_GRADIENT

        self._alpha = alpha
        self._tol = tol

    def build_vol_surface(self, value_date):
        """Builds the implied volatility surface for a particular value date and calculates the benchmark strikes etc.

        Before we do any sort of interpolation later, we need to build the implied_vol vol surface.

        Parameters
        ----------
        value_date : str
            Value date (need to have market data for this date)

        asset : str
            Asset name

        depo_tenor : str
            Depo tenor to use

            default - "1M"

        field : str
            Market data field to use

            default - "close"
        """

        self._value_date = self._market_util.parse_date(value_date)

        value_fin_date = self._findate(self._value_date)

        date_index = self._market_df.index == value_date

        # TODO: add whole rates curve
        dom_discount_curve = DiscountCurveFlat(value_fin_date,
                                               self._domCCRate[date_index])
        for_discount_curve = DiscountCurveFlat(value_fin_date,
                                               self._forCCRate[date_index])

        self._dom_discount_curve = dom_discount_curve
        self._for_discount_curve = for_discount_curve

        self._spot = float(self._spot_history[date_index][0])

        # New implementation in FinancePy also uses 10d for interpolation
        self._fin_fx_vol_surface = FinFXVolSurface(
            value_fin_date,
            self._spot,
            self._asset,
            self._asset[0:3],
            dom_discount_curve,
            for_discount_curve,
            self._tenors.copy(),
            self._atm_vols[date_index][
                0],
            self._market_strangle25DeltaVols[
                date_index][0],
            self._risk_reversal25DeltaVols[
                date_index][0],
            self._market_strangle10DeltaVols[
                date_index][0],
            self._risk_reversal10DeltaVols[
                date_index][0],
            self._alpha,
            atmMethod=self._atm_method,
            deltaMethod=self._delta_method,
            volatility_function_type=self._vol_function_type,
            finSolverType=self._solver,
            tol=self._tol)  # TODO add tol

    def calculate_vol_for_strike_expiry(self, K, expiry_date=None, tenor="1M"):
        """Calculates the implied_vol volatility for a given strike and tenor (or expiry date, if specified). The
        expiry date/broken dates are intepolated linearly in variance space.

        Parameters
        ----------
        K : float
            Strike for which to find implied_vol volatility

        expiry_date : str (optional)
            Expiry date of option

        tenor : str (optional)
            Tenor of option

            default - "1M"

        Returns
        -------
        float
        """

        if expiry_date is not None:
            expiry_date = self._findate(
                self._market_util.parse_date(expiry_date))
            try:
                return self._fin_fx_vol_surface.vol_from_strike_dt(
                    K, expiry_date)
            except:
                return self._fin_fx_vol_surface.volatility_from_strike_date(
                    K, expiry_date)
        else:
            try:
                tenor_index = self._get_tenor_index(tenor)
                return self.get_vol_from_quoted_tenor(K, tenor_index)
            except:
                pass

        return None

    def calculate_vol_for_delta_expiry(self, delta_call, expiry_date=None):
        """Calculates the implied_vol volatility for a given delta call and expiry date. The
        expiry date/broken dates are intepolated linearly in variance space.

        Parameters
        ----------
        delta_call : float
            Delta for the strike for which to find implied volatility

        expiry_date : str (optional)
            Expiry date of option

        Returns
        -------
        float
        """
        if expiry_date is not None:
            expiry_date = self._findate(
                self._market_util.parse_date(expiry_date))
            return self._fin_fx_vol_surface.volatilityFromDeltaDate(delta_call,
                                                                    expiry_date)

        return None

    def extract_vol_surface(self, num_strike_intervals=60, low_K_pc=0.95,
                            high_K_pc=1.05):
        """Creates an interpolated implied vol surface which can be plotted 
        (in strike space), and also in delta space for key strikes (ATM, 25d 
        call and put). Also for key strikes converts from delta to strike space.

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
        df_vol_surface_strike_space = pd.DataFrame(
            columns=self._fin_fx_vol_surface._tenors)
        df_vol_surface_delta_space = pd.DataFrame(
            columns=self._fin_fx_vol_surface._tenors)

        # columns = tenors
        df_vol_surface_implied_pdf = pd.DataFrame(
            columns=self._fin_fx_vol_surface._tenors)

        # Conversion between main deltas and strikes
        df_deltas_vs_strikes = pd.DataFrame(
            columns=self._fin_fx_vol_surface._tenors)

        # ATM, 10d + 25d market strangle and 25d risk reversals
        df_vol_surface_quoted_points = pd.DataFrame(
            columns=self._fin_fx_vol_surface._tenors)

        # Note, at present we"re not using 10d strikes
        quoted_strikes_names = ["ATM", "STR_25D_MS", "RR_25D_P", "STR_10D_MS",
                                "RR_10D_P"]
        key_strikes_names = ["K_10D_P", "K_10D_P_MS", "K_25D_P", "K_25D_P_MS",
                             "ATM", "K_25D_C", "K_25D_C_MS", "K_10D_C",
                             "K_10D_C_MS"]

        # Get max/min strikes to interpolate (from the longest dated tenor)
        low_K = self._fin_fx_vol_surface._K_25D_P[-1] * low_K_pc
        high_K = self._fin_fx_vol_surface._K_25D_C[-1] * high_K_pc

        if num_strike_intervals is not None:
            # In case using old version of FinancePy
            try:
                implied_pdf_fin_distribution = self._fin_fx_vol_surface.implied_dbns(
                    low_K, high_K, num_strike_intervals)
            except:
                pass

        for tenor_index in range(0, self._fin_fx_vol_surface._num_vol_curves):

            # Get the quoted vol points
            tenor_label = self._fin_fx_vol_surface._tenors[tenor_index]

            atm_vol = self._fin_fx_vol_surface._atm_vols[tenor_index] * 100
            ms_25d_vol = self._fin_fx_vol_surface._mktStrangle25DeltaVols[
                             tenor_index] * 100
            rr_25d_vol = self._fin_fx_vol_surface._riskReversal25DeltaVols[
                             tenor_index] * 100
            ms_10d_vol = self._fin_fx_vol_surface._mktStrangle10DeltaVols[
                             tenor_index] * 100
            rr_10d_vol = self._fin_fx_vol_surface._riskReversal10DeltaVols[
                             tenor_index] * 100

            df_vol_surface_quoted_points[tenor_label] = pd.Series(
                index=quoted_strikes_names,
                data=[atm_vol, ms_25d_vol, rr_25d_vol, ms_10d_vol, rr_10d_vol])

            # Do interpolation in strike space for the implied vols (if intervals have been specified)
            strikes = []
            vols = []

            if num_strike_intervals is not None:
                K = low_K
                dK = (high_K - low_K) / num_strike_intervals

                for i in range(0, num_strike_intervals):
                    sigma = self.get_vol_from_quoted_tenor(K,
                                                           tenor_index) * 100.0
                    strikes.append(K)
                    vols.append(sigma)
                    K = K + dK

                df_vol_surface_strike_space[tenor_label] = pd.Series(
                    index=strikes, data=vols)

            try:
                df_vol_surface_implied_pdf[tenor_label] = pd.Series(
                    index=implied_pdf_fin_distribution[tenor_index]._x,
                    data=implied_pdf_fin_distribution[tenor_index]._densitydx)
            except:
                pass

            # Extract strikes for the quoted points (ie. 10d, 25d and ATM)
            key_strikes = []
            key_strikes.append(self._fin_fx_vol_surface._K_10D_P[tenor_index])
            key_strikes.append(
                self._fin_fx_vol_surface._K_10D_P_MS[tenor_index])
            key_strikes.append(self._fin_fx_vol_surface._K_25D_P[tenor_index])
            key_strikes.append(
                self._fin_fx_vol_surface._K_25D_P_MS[tenor_index])
            key_strikes.append(self._fin_fx_vol_surface._K_ATM[tenor_index])
            key_strikes.append(self._fin_fx_vol_surface._K_25D_C[tenor_index])
            key_strikes.append(
                self._fin_fx_vol_surface._K_25D_C_MS[tenor_index])
            key_strikes.append(self._fin_fx_vol_surface._K_10D_C[tenor_index])
            key_strikes.append(
                self._fin_fx_vol_surface._K_10D_C_MS[tenor_index])

            df_deltas_vs_strikes[tenor_label] = pd.Series(
                index=key_strikes_names, data=key_strikes)

            # Put a conversion between quoted deltas and strikes (eg. which is ATM in strike space, 25d call/put strikes)
            key_vols = []

            for K, name in zip(key_strikes, key_strikes_names):
                sigma = self.get_vol_from_quoted_tenor(K, tenor_index) * 100.0
                key_vols.append(sigma)

            df_vol_surface_delta_space[tenor_label] = pd.Series(
                index=key_strikes_names, data=key_vols)

        df_vol_dict = {}
        df_vol_dict["vol_surface_implied_pdf"] = df_vol_surface_implied_pdf
        df_vol_dict["vol_surface_strike_space"] = df_vol_surface_strike_space
        df_vol_dict["vol_surface_delta_space"] = df_vol_surface_delta_space
        df_vol_dict["vol_surface_delta_space_exc_ms"] = \
            df_vol_surface_delta_space[
                ~df_vol_surface_delta_space.index.str.contains("_MS")]
        df_vol_dict["vol_surface_quoted_points"] = df_vol_surface_quoted_points
        df_vol_dict["deltas_vs_strikes"] = df_deltas_vs_strikes

        self._df_vol_dict = df_vol_dict

        return df_vol_dict

    def get_vol_from_quoted_tenor(self, K, tenor, gaps=None):

        if not (isinstance(tenor, int)):
            tenor_index = self._get_tenor_index(tenor)
        else:
            tenor_index = tenor

        if gaps is None:
            gaps = np.array([0.1])

        params = self._fin_fx_vol_surface._parameters[tenor_index]
        t = self._fin_fx_vol_surface._texp[tenor_index]
        f = self._fin_fx_vol_surface._F0T[tenor_index]

        return vol_function(self._vol_function_type.value, params,
                            np.array([K]), gaps, f, K, t)

    def get_vol_strike_from_delta_tenor(self, call_delta, tenor=None,
                                        expiry_date=None):

        if tenor is not None:
            if not (isinstance(tenor, int)):
                tenor_index = self._get_tenor_index(tenor)
            else:
                tenor_index = tenor

            expiry_date = self._fin_fx_vol_surface._expiryDates[tenor_index]

        return self._fin_fx_vol_surface.volatilityFromDeltaDate(call_delta,
                                                                expiryDate=expiry_date)

    def get_atm_method(self):
        return self._atm_method

    def get_delta_method(self):
        return self._delta_method

    def get_all_market_data(self):
        return self._market_df

    def get_spot(self):
        return self._spot

    def get_atm_strike(self, tenor=None):
        return self._df_vol_dict["deltas_vs_strikes"][tenor]["ATM"]

    def get_25d_call_strike(self, tenor=None):
        return self._df_vol_dict["deltas_vs_strikes"][tenor]["K_25D_C"]

    def get_25d_put_strike(self, tenor=None):
        return self._df_vol_dict["deltas_vs_strikes"][tenor]["K_25D_P"]

    def get_10d_call_strike(self, tenor=None):
        return self._df_vol_dict["deltas_vs_strikes"][tenor]["K_10D_C"]

    def get_10d_put_strike(self, tenor=None):
        return self._df_vol_dict["deltas_vs_strikes"][tenor]["K_10D_P"]

    def get_25d_call_ms_strike(self, tenor=None):
        return self._df_vol_dict["deltas_vs_strikes"][tenor]["K_25D_C_MS"]

    def get_25d_put_ms_strike(self, tenor=None):
        return self._df_vol_dict["deltas_vs_strikes"][tenor]["K_25D_P_MS"]

    def get_10d_call_ms_strike(self, expiry_date=None, tenor=None):
        return self._df_vol_dict["deltas_vs_strikes"][tenor]["K_10D_C_MS"]

    def get_10d_put_ms_strike(self, expiry_date=None, tenor=None):
        return self._df_vol_dict["deltas_vs_strikes"][tenor]["K_10D_P_MS"]

    def get_atm_quoted_vol(self, tenor):
        """The quoted ATM vol from the market (ie. which has NOT been obtained from build vol surface)

        Parameters
        ----------
        tenor : str
            Tenor

        Returns
        -------
        float
        """
        return self._atm_vols[self._market_df.index == self._value_date][0][
            self._get_tenor_index(tenor)]

    def get_atm_vol(self, tenor=None):
        return self._df_vol_dict["vol_surface_delta_space"][tenor]["ATM"]

    def get_25d_call_vol(self, tenor=None):
        return self._df_vol_dict["vol_surface_delta_space"][tenor]["K_25D_C"]

    def get_25d_put_vol(self, tenor=None):
        return self._df_vol_dict["vol_surface_delta_space"][tenor]["K_25D_P"]

    def get_25d_call_ms_vol(self, tenor=None):
        return self._df_vol_dict["vol_surface_delta_space"][tenor][
            "K_25D_C_MS"]

    def get_25d_put_ms_vol(self, tenor=None):
        return self._df_vol_dict["vol_surface_delta_space"][tenor][
            "K_25D_P_MS"]

    def get_10d_call_vol(self, tenor=None):
        return self._df_vol_dict["vol_surface_delta_space"][tenor]["K_10D_C"]

    def get_10d_put_vol(self, tenor=None):
        return self._df_vol_dict["vol_surface_delta_space"][tenor]["K_10D_P"]

    def get_10d_call_ms_vol(self, tenor=None):
        return self._df_vol_dict["vol_surface_delta_space"][tenor][
            "K_10D_C_MS"]

    def get_10d_put_ms_vol(self, tenor=None):
        return self._df_vol_dict["vol_surface_delta_space"][tenor][
            "K_10D_P_MS"]

    def get_dom_discount_curve(self):
        return self._dom_discount_curve

    def get_for_discount_curve(self):
        return self._for_discount_curve

    def plot_vol_curves(self):
        if self._fin_fx_vol_surface is not None:
            self._fin_fx_vol_surface.plotVolCurves()

    def _findate(self, timestamp):

        return Date(timestamp.day, timestamp.month, timestamp.year,
                    hh=timestamp.hour, mm=timestamp.minute,
                    ss=timestamp.second)
