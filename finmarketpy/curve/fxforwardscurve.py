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

from pandas.tseries.offsets import CustomBusinessDay, CustomBusinessMonthEnd

from findatapy.market import Market, MarketDataRequest
from findatapy.timeseries import Calculations, Calendar, Filter
from findatapy.util.dataconstants import DataConstants
from findatapy.util.fxconv import FXConv

from finmarketpy.curve.rates.fxforwardspricer import FXForwardsPricer
from finmarketpy.util.marketconstants import MarketConstants

data_constants = DataConstants()
market_constants = MarketConstants()

class FXForwardsCurve(object):
    """Constructs continuous forwards time series total return indices from underlying forwards contracts.

    """

    def __init__(self, market_data_generator=None, fx_forwards_trading_tenor=market_constants.fx_forwards_trading_tenor,
                 roll_days_before=market_constants.fx_forwards_roll_days_before,
                 roll_event=market_constants.fx_forwards_roll_event, construct_via_currency='no',
                 fx_forwards_tenor_for_interpolation=market_constants.fx_forwards_tenor_for_interpolation,
                 base_depos_tenor=data_constants.base_depos_tenor,
                 roll_months=market_constants.fx_forwards_roll_months,
                 cum_index=market_constants.fx_forwards_cum_index,
                 output_calculation_fields=market_constants.output_calculation_fields,
                 field='close'):
        """Initializes FXForwardsCurve

        Parameters
        ----------
        market_data_generator : MarketDataGenerator
            Used for downloading market data

        fx_forwards_trading_tenor : str
            What is primary forward contract being used to trade (default - '1M')

        roll_days_before : int
            Number of days before roll event to enter into a new forwards contract

        roll_event : str
            What constitutes a roll event? ('month-end', 'quarter-end', 'year-end', 'expiry')

        construct_via_currency : str
            What currency should we construct the forward via? Eg. if we asked for AUDJPY we can construct it via
            AUDUSD & JPYUSD forwards, as opposed to AUDJPY forwards (default - 'no')

        fx_forwards_tenor_for_interpolation : str(list)
            Which forwards should we use for interpolation

        base_depos_tenor : str(list)
            Which base deposits tenors do we need (this is only necessary if we want to start inferring depos)

        roll_months : int
            After how many months should we initiate a roll. Typically for trading 1M this should 1, 3M this should be 3
            etc.

        cum_index : str
            In total return index, do we compute in additive or multiplicative way ('add' or 'mult')

        output_calculation_fields : bool
            Also output additional data should forward expiries etc. alongside total returns indices
        """

        self._market_data_generator = market_data_generator
        self._calculations = Calculations()
        self._calendar = Calendar()
        self._filter = Filter()

        self._fx_forwards_trading_tenor = fx_forwards_trading_tenor
        self._roll_days_before = roll_days_before
        self._roll_event = roll_event

        self._construct_via_currency = construct_via_currency
        self._fx_forwards_tenor_for_interpolation = fx_forwards_tenor_for_interpolation
        self._base_depos_tenor = base_depos_tenor

        self._roll_months = roll_months
        self._cum_index = cum_index
        self._output_calcultion_fields = output_calculation_fields

        self._field = field

    def generate_key(self):
        from findatapy.market.ioengine import SpeedCache

        # Don't include any "large" objects in the key
        return SpeedCache().generate_key(self, ['_market_data_generator', '_calculations', '_calendar', '_filter'])

    def fetch_continuous_time_series(self, md_request, market_data_generator, fx_forwards_trading_tenor=None,
                                     roll_days_before=None, roll_event=None,
                                     construct_via_currency=None, fx_forwards_tenor_for_interpolation=None, base_depos_tenor=None,
                                     roll_months=None, cum_index=None, output_calculation_fields=False, field=None):

        if market_data_generator is None: market_data_generator = self._market_data_generator
        if fx_forwards_trading_tenor is None: fx_forwards_trading_tenor = self._fx_forwards_trading_tenor
        if roll_days_before is None: roll_days_before = self._roll_days_before
        if roll_event is None: roll_event = self._roll_event
        if construct_via_currency is None: construct_via_currency = self._construct_via_currency
        if fx_forwards_tenor_for_interpolation is None: fx_forwards_tenor_for_interpolation = self._fx_forwards_tenor_for_interpolation
        if base_depos_tenor is None: base_depos_tenor = self._base_depos_tenor
        if roll_months is None: roll_months = self._roll_months
        if cum_index is None: cum_index = self._cum_index
        if output_calculation_fields is None: output_calculation_fields = self._output_calcultion_fields
        if field is None: field = self._field

        # Eg. we construct EURJPY via EURJPY directly (note: would need to have sufficient forward data for this)
        if construct_via_currency == 'no':
            # Download FX spot, FX forwards points and base depos etc.
            market = Market(market_data_generator=market_data_generator)

            md_request_download = MarketDataRequest(md_request=md_request)

            fx_conv = FXConv()

            # CAREFUL: convert the tickers to correct notation, eg. USDEUR => EURUSD, because our data
            # should be fetched in correct convention
            md_request_download.tickers = [fx_conv.correct_notation(x) for x in md_request.tickers]
            md_request_download.category = 'fx-forwards-market'
            md_request_download.fields = field
            md_request_download.abstract_curve = None
            md_request_download.fx_forwards_tenor = fx_forwards_tenor_for_interpolation
            md_request_download.base_depos_tenor = base_depos_tenor

            forwards_market_df = market.fetch_market(md_request_download)

            # Now use the original tickers
            return self.construct_total_return_index(md_request.tickers, forwards_market_df,
                                                     fx_forwards_trading_tenor=fx_forwards_trading_tenor,
                                                     roll_days_before=roll_days_before, roll_event=roll_event,
                                                     fx_forwards_tenor_for_interpolation=fx_forwards_tenor_for_interpolation,
                                                     roll_months=roll_months,
                                                     cum_index=cum_index,
                                                     output_calculation_fields=output_calculation_fields,
                                                     field=field)
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

                # Construct the base and terms separately (ie. AUDJPY => AUDUSD & JPYUSD)
                base_vals = self.fetch_continuous_time_series(md_request_base, market_data_generator,
                                     fx_forwards_trading_tenor=fx_forwards_trading_tenor,
                                     roll_days_before=roll_days_before, roll_event=roll_event,
                                     fx_forwards_tenor_for_interpolation=fx_forwards_tenor_for_interpolation,
                                     base_depos_tenor=base_depos_tenor,
                                     roll_months=roll_months, output_calculation_fields=False,
                                     cum_index=cum_index,
                                     construct_via_currency='no',
                                     field=field)

                terms_vals = self.fetch_continuous_time_series(md_request_terms, market_data_generator,
                                     fx_forwards_trading_tenor=fx_forwards_trading_tenor,
                                     roll_days_before=roll_days_before, roll_event=roll_event,
                                     fx_forwards_tenor_for_interpolation=fx_forwards_tenor_for_interpolation,
                                     base_depos_tenor=base_depos_tenor,
                                     roll_months=roll_months,
                                     cum_index=cum_index,
                                     output_calculation_fields=False,
                                     construct_via_currency='no',
                                     field=field)

                # Special case for USDUSD case (and if base or terms USD are USDUSD
                if base + terms == construct_via_currency + construct_via_currency:
                    base_rets = self._calculations.calculate_returns(base_vals)
                    cross_rets = pd.DataFrame(0, index=base_rets.index, columns=base_rets.columns)
                elif base + construct_via_currency == construct_via_currency + construct_via_currency:
                    cross_rets = -self._calculations.calculate_returns(terms_vals)
                elif terms + construct_via_currency == construct_via_currency + construct_via_currency:
                    cross_rets = self._calculations.calculate_returns(base_vals)
                else:
                    base_rets = self._calculations.calculate_returns(base_vals)
                    terms_rets = self._calculations.calculate_returns(terms_vals)

                    cross_rets = base_rets.sub(terms_rets.iloc[:, 0], axis=0)

                # First returns of a time series will by NaN, given we don't know previous point
                cross_rets.iloc[0] = 0

                cross_vals = self._calculations.create_mult_index(cross_rets)
                cross_vals.columns = [tick + '-forward-tot.' + field]

                total_return_indices.append(cross_vals)

            return self._calculations.join(total_return_indices, how='outer')

    def unhedged_asset_fx(self, assets_df, asset_currency, home_curr, start_date, finish_date, spot_df=None):
        pass

    def hedged_asset_fx(self, assets_df, asset_currency, home_curr, start_date, finish_date, spot_df=None,
                        total_return_indices_df=None):
        pass

    def get_day_count_conv(self, currency):
        if currency in market_constants.currencies_with_365_basis:
            return 365.0

        return 360.0

    def construct_total_return_index(self, cross_fx, forwards_market_df,
                                     fx_forwards_trading_tenor=None,
                                     roll_days_before=None,
                                     roll_event=None,
                                     roll_months=None,
                                     fx_forwards_tenor_for_interpolation=None,
                                     cum_index=None,
                                     output_calculation_fields=None,
                                     field=None):

        if not (isinstance(cross_fx, list)):
            cross_fx = [cross_fx]

        if fx_forwards_trading_tenor is None: fx_forwards_trading_tenor = self._fx_forwards_trading_tenor
        if roll_days_before is None: roll_days_before = self._roll_days_before
        if roll_event is None: roll_event = self._roll_event
        if roll_months is None: roll_months = self._roll_months
        if fx_forwards_tenor_for_interpolation is None: fx_forwards_tenor_for_interpolation = self._fx_forwards_tenor_for_interpolation
        if cum_index is None: cum_index = self._cum_index
        if field is None: field = self._field

        total_return_index_df_agg = []

        # Remove columns where there is no data (because these points typically aren't quoted)
        forwards_market_df = forwards_market_df.dropna(how='all', axis=1)

        fx_forwards_pricer = FXForwardsPricer()

        def get_roll_date(horizon_d, delivery_d, asset_hols, month_adj=1):
            if roll_event == 'month-end':
                roll_d = horizon_d + CustomBusinessMonthEnd(roll_months + month_adj, holidays=asset_hols)
            elif roll_event == 'delivery-date':
                roll_d = delivery_d

            return (roll_d - CustomBusinessDay(n=roll_days_before, holidays=asset_hols))

        for cross in cross_fx:

            # Eg. if we specify USDUSD
            if cross[0:3] == cross[3:6]:
                total_return_index_df_agg.append(
                    pd.DataFrame(100, index=forwards_market_df.index, columns=[cross + "-forward-tot.close"]))
            else:
                # Is the FX cross in the correct convention
                old_cross = cross
                cross = FXConv().correct_notation(cross)

                horizon_date = forwards_market_df.index

                delivery_date = []
                roll_date = []

                new_trade = np.full(len(horizon_date), False, dtype=bool)

                asset_holidays = self._calendar.get_holidays(cal=cross)

                # Get first delivery date
                delivery_date.append(
                    self._calendar.get_delivery_date_from_horizon_date(horizon_date[0],
                        fx_forwards_trading_tenor, cal=cross, asset_class='fx')[0])

                # For first month want it to expire within that month (for consistency), hence month_adj=0 ONLY here
                roll_date.append(get_roll_date(horizon_date[0], delivery_date[0], asset_holidays, month_adj=0))

                # New trade => entry at beginning AND on every roll
                new_trade[0] = True

                # Get all the delivery dates and roll dates
                # At each "roll/trade" day we need to reset them for the new contract
                for i in range(1, len(horizon_date)):

                    # If the horizon date has reached the roll date (from yesterday), we're done, and we have a
                    # new roll/trade
                    if (horizon_date[i] - roll_date[i-1]).days == 0:
                        new_trade[i] = True
                    # else:
                    #    new_trade[i] = False

                    # If we're entering a new trade/contract, we need to get new delivery and roll dates
                    if new_trade[i]:
                        delivery_date.append(self._calendar.get_delivery_date_from_horizon_date(horizon_date[i],
                            fx_forwards_trading_tenor, cal=cross, asset_class='fx')[0])

                        roll_date.append(get_roll_date(horizon_date[i], delivery_date[i], asset_holidays))
                    else:
                        # Otherwise use previous delivery and roll dates, because we're still holding same contract
                        delivery_date.append(delivery_date[i-1])
                        roll_date.append(roll_date[i-1])

                interpolated_forward = fx_forwards_pricer.price_instrument(cross, horizon_date, delivery_date, market_df=forwards_market_df,
                         fx_forwards_tenor_for_interpolation=fx_forwards_tenor_for_interpolation)[cross + '-interpolated-outright-forward.' + field].values

                # To record MTM prices
                mtm = np.copy(interpolated_forward)

                # Note: may need to add discount factor when marking to market forwards?

                # Special case: for very first trading day
                # mtm[0] = interpolated_forward[0]

                # On rolling dates, MTM will be the previous forward contract (interpolated)
                # otherwise it will be the current forward contract
                for i in range(1, len(horizon_date)):
                    if new_trade[i]:
                        mtm[i] = fx_forwards_pricer.price_instrument(cross, horizon_date[i], delivery_date[i-1],
                            market_df=forwards_market_df,
                            fx_forwards_tenor_for_interpolation=fx_forwards_tenor_for_interpolation) \
                                [cross + '-interpolated-outright-forward.' + field].values
                    # else:
                    #    mtm[i] = interpolated_forward[i]

                # Eg. if we asked for USDEUR, we first constructed spot/forwards for EURUSD
                # and then need to invert it
                if old_cross != cross:
                    mtm = 1.0 / mtm
                    interpolated_forward = 1.0 / interpolated_forward

                forward_rets = mtm / np.roll(interpolated_forward, 1) - 1.0
                forward_rets[0] = 0

                if cum_index == 'mult':
                    cum_rets = 100 * np.cumprod(1.0 + forward_rets)
                elif cum_index == 'add':
                    cum_rets = 100 + 100 * np.cumsum(forward_rets)

                total_return_index_df = pd.DataFrame(index=horizon_date, columns=[cross + "-forward-tot." + field])
                total_return_index_df[cross + "-forward-tot." + field] = cum_rets

                if output_calculation_fields:
                    total_return_index_df[cross + '-interpolated-outright-forward.' + field] = interpolated_forward
                    total_return_index_df[cross + '-mtm.close'] = mtm
                    total_return_index_df[cross + '-roll.close'] = new_trade
                    total_return_index_df[cross + '.roll-date'] = roll_date
                    total_return_index_df[cross + '.delivery-date'] = delivery_date
                    total_return_index_df[cross + '-forward-return.' + field] = forward_rets

                total_return_index_df_agg.append(total_return_index_df)

        return self._calculations.join(total_return_index_df_agg, how='outer')
