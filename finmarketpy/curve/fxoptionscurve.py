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

from finmarketpy.curve.volatility.fxoptionspricer import FXOptionsPricer
from finmarketpy.curve.volatility.fxvolsurface import FXVolSurface
from finmarketpy.util.marketconstants import MarketConstants

data_constants = DataConstants()
market_constants = MarketConstants()

class FXOptionsCurve(object):
    """Constructs continuous forwards time series total return indices from underlying forwards contracts.

    """

    def __init__(self, market_data_generator=None,
                 fx_vol_surface=None,
                 enter_trading_dates=None,
                 fx_options_trading_tenor=market_constants.fx_options_trading_tenor,
                 roll_days_before=market_constants.fx_options_roll_days_before,
                 roll_event=market_constants.fx_options_roll_event, construct_via_currency='no',
                 fx_options_tenor_for_interpolation=market_constants.fx_options_tenor_for_interpolation,
                 base_depos_tenor=data_constants.base_depos_tenor,
                 roll_months=market_constants.fx_options_roll_months,
                 cum_index=market_constants.fx_options_cum_index,
                 strike=market_constants.fx_options_index_strike,
                 contract_type=market_constants.fx_options_index_contract_type,
                 premium_output=market_constants.fx_options_index_premium_output,
                 position_multiplier=1,
                 depo_tenor_for_option=market_constants.fx_options_depo_tenor,
                 freeze_implied_vol=market_constants.fx_options_freeze_implied_vol,
                 tot_label='',
                 cal=None,
                 output_calculation_fields=market_constants.output_calculation_fields):
        """Initializes FXForwardsCurve

        Parameters
        ----------
        market_data_generator : MarketDataGenerator
            Used for downloading market data

        fx_vol_surface : FXVolSurface
            We can specify the FX vol surface beforehand if we want

        fx_options_trading_tenor : str
            What is primary forward contract being used to trade (default - '1M')

        roll_days_before : int
            Number of days before roll event to enter into a new forwards contract

        roll_event : str
            What constitutes a roll event? ('month-end', 'quarter-end', 'year-end', 'expiry')

        cum_index : str
            In total return index, do we compute in additive or multiplicative way ('add' or 'mult')

        construct_via_currency : str
            What currency should we construct the forward via? Eg. if we asked for AUDJPY we can construct it via
            AUDUSD & JPYUSD forwards, as opposed to AUDJPY forwards (default - 'no')

        fx_options_tenor_for_interpolation : str(list)
            Which forwards should we use for interpolation

        base_depos_tenor : str(list)
            Which base deposits tenors do we need (this is only necessary if we want to start inferring depos)

        roll_months : int
            After how many months should we initiate a roll. Typically for trading 1M this should 1, 3M this should be 3
            etc.

        tot_label : str
            Postfix for the total returns field

        cal : str
            Calendar to use for expiry (if None, uses that of FX pair)

        output_calculation_fields : bool
            Also output additional data should forward expiries etc. alongside total returns indices
        """

        self._market_data_generator = market_data_generator
        self._calculations = Calculations()
        self._calendar = Calendar()
        self._filter = Filter()

        self._fx_vol_surface = fx_vol_surface

        self._enter_trading_dates = enter_trading_dates
        self._fx_options_trading_tenor = fx_options_trading_tenor
        self._roll_days_before = roll_days_before
        self._roll_event = roll_event

        self._construct_via_currency = construct_via_currency
        self._fx_options_tenor_for_interpolation = fx_options_tenor_for_interpolation
        self._base_depos_tenor = base_depos_tenor

        self._roll_months = roll_months
        self._cum_index = cum_index
        self._contact_type = contract_type
        self._strike = strike
        self._premium_output = premium_output

        self._position_multiplier = position_multiplier

        self._depo_tenor_for_option = depo_tenor_for_option

        self._freeze_implied_vol = freeze_implied_vol

        self._tot_label = tot_label
        self._cal = cal

        self._output_calculation_fields = output_calculation_fields

    def generate_key(self):
        from findatapy.market.ioengine import SpeedCache

        # Don't include any "large" objects in the key
        return SpeedCache().generate_key(self, ['_market_data_generator', '_calculations', '_calendar', '_filter'])

    def fetch_continuous_time_series(self, md_request, market_data_generator, fx_vol_surface=None, enter_trading_dates=None,
                                     fx_options_trading_tenor=None,
                                     roll_days_before=None, roll_event=None,
                                     construct_via_currency=None, fx_options_tenor_for_interpolation=None, base_depos_tenor=None,
                                     roll_months=None, cum_index=None,
                                     strike=None, contract_type=None, premium_output=None,
                                     position_multiplier=None,
                                     depo_tenor_for_option=None,
                                     freeze_implied_vol=None,
                                     tot_label=None, cal=None,
                                     output_calculation_fields=None):

        if fx_vol_surface is None: fx_vol_surface = self._fx_vol_surface
        if enter_trading_dates is None: enter_trading_dates = self._enter_trading_dates
        if market_data_generator is None: market_data_generator = self._market_data_generator
        if fx_options_trading_tenor is None: fx_options_trading_tenor = self._fx_options_trading_tenor
        if roll_days_before is None: roll_days_before = self._roll_days_before
        if roll_event is None: roll_event = self._roll_event
        if construct_via_currency is None: construct_via_currency = self._construct_via_currency
        if fx_options_tenor_for_interpolation is None: fx_options_tenor_for_interpolation = self._fx_options_tenor_for_interpolation
        if base_depos_tenor is None: base_depos_tenor = self._base_depos_tenor
        if roll_months is None: roll_months = self._roll_months
        if strike is None: strike = self._strike
        if contract_type is None: contract_type = self._contact_type
        if premium_output is None: premium_output = self._premium_output

        if position_multiplier is None: position_multiplier = self._position_multiplier

        if depo_tenor_for_option is None: depo_tenor_for_option = self._depo_tenor_for_option

        if freeze_implied_vol is None: freeze_implied_vol = self._freeze_implied_vol

        if tot_label is None: tot_label = self._tot_label
        if cal is None: cal = self._cal

        if output_calculation_fields is None: output_calculation_fields = self._output_calculation_fields

        # Eg. we construct EURJPY via EURJPY directly (note: would need to have sufficient options/forward data for this)
        if construct_via_currency == 'no':

            if fx_vol_surface is None:
                # Download FX spot, FX forwards points and base depos etc.
                market = Market(market_data_generator=market_data_generator)

                md_request_download = MarketDataRequest(md_request=md_request)

                fx_conv = FXConv()

                # CAREFUL: convert the tickers to correct notation, eg. USDEUR => EURUSD, because our data
                # should be fetched in correct convention
                md_request_download.tickers = [fx_conv.correct_notation(x) for x in md_request.tickers]
                md_request_download.category = 'fx-vol-market'
                md_request_download.fields = 'close'
                md_request_download.abstract_curve = None
                md_request_download.fx_options_tenor = fx_options_tenor_for_interpolation
                md_request_download.base_depos_tenor = base_depos_tenor
                # md_request_download.base_depos_currencies = []

                forwards_market_df = market.fetch_market(md_request_download)
            else:
                forwards_market_df = None

            # Now use the original tickers
            return self.construct_total_return_index(md_request.tickers, forwards_market_df,
                                                     fx_vol_surface=fx_vol_surface,
                                                     enter_trading_dates=enter_trading_dates,
                                                     fx_options_trading_tenor=fx_options_trading_tenor,
                                                     roll_days_before=roll_days_before, roll_event=roll_event,
                                                     fx_options_tenor_for_interpolation=fx_options_tenor_for_interpolation,
                                                     roll_months=roll_months, cum_index=cum_index,
                                                     strike=strike, contract_type=contract_type,
                                                     premium_output=premium_output,
                                                     position_multiplier=position_multiplier,
                                                     freeze_implied_vol=freeze_implied_vol,
                                                     depo_tenor_for_option=depo_tenor_for_option,
                                                     tot_label=tot_label, cal=cal,
                                                     output_calculation_fields=output_calculation_fields)
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
                                     fx_vol_surface=fx_vol_surface,
                                     enter_trading_dates=enter_trading_dates,
                                     fx_options_trading_tenor=fx_options_trading_tenor,
                                     roll_days_before=roll_days_before, roll_event=roll_event,
                                     fx_options_tenor_for_interpolation=fx_options_tenor_for_interpolation,
                                     base_depos_tenor=base_depos_tenor,
                                     roll_months=roll_months, cum_index=cum_index,
                                     strike=strike, contract_type=contract_type,
                                     premium_output=premium_output,
                                     position_multiplier=position_multiplier,
                                     depo_tenor_for_option=depo_tenor_for_option,
                                     freeze_implied_vol=freeze_implied_vol,
                                     tot_label=tot_label, cal=cal,
                                     output_calculation_fields=output_calculation_fields,
                                     construct_via_currency='no')

                terms_vals = self.fetch_continuous_time_series(md_request_terms, market_data_generator,
                                     fx_vol_surface=fx_vol_surface,
                                     enter_trading_dates=enter_trading_dates,
                                     fx_options_trading_tenor=fx_options_trading_tenor,
                                     roll_days_before=roll_days_before, roll_event=roll_event,
                                     fx_options_tenor_for_interpolation=fx_options_tenor_for_interpolation,
                                     base_depos_tenor=base_depos_tenor,
                                     roll_months=roll_months, cum_index=cum_index,
                                     strike=strike, contract_type=contract_type,
                                     position_multiplier=position_multiplier,
                                     depo_tenor_for_option=depo_tenor_for_option,
                                     freeze_implied_vol=freeze_implied_vol,
                                     tot_label=tot_label, cal=cal,
                                     output_calculation_fields=output_calculation_fields,
                                     construct_via_currency='no')

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
                cross_vals.columns = [tick + '-option-tot.close']

                total_return_indices.append(cross_vals)

            return self._calculations.pandas_outer_join(total_return_indices)

    def unhedged_asset_fx(self, assets_df, asset_currency, home_curr, start_date, finish_date, spot_df=None):
        pass

    def hedged_asset_fx(self, assets_df, asset_currency, home_curr, start_date, finish_date, spot_df=None,
                        total_return_indices_df=None):
        pass

    def get_day_count_conv(self, currency):
        if currency in market_constants.currencies_with_365_basis:
            return 365.0

        return 360.0

    def construct_total_return_index(self, cross_fx, market_df,
                                     fx_vol_surface=None,
                                     enter_trading_dates=None,
                                     fx_options_trading_tenor=None,
                                     roll_days_before=None,
                                     roll_event=None,
                                     roll_months=None,
                                     cum_index=None,
                                     strike=None,
                                     contract_type=None,
                                     premium_output=None,
                                     position_multiplier=None,
                                     fx_options_tenor_for_interpolation=None,
                                     freeze_implied_vol=None,
                                     depo_tenor_for_option=None,
                                     tot_label=None,
                                     cal=None,
                                     output_calculation_fields=None):

        if fx_vol_surface is None: fx_vol_surface = self._fx_vol_surface
        if enter_trading_dates is None: enter_trading_dates = self._enter_trading_dates
        if fx_options_trading_tenor is None: fx_options_trading_tenor = self._fx_options_trading_tenor
        if roll_days_before is None: roll_days_before = self._roll_days_before
        if roll_event is None: roll_event = self._roll_event
        if roll_months is None: roll_months = self._roll_months
        if cum_index is None: cum_index = self._cum_index
        if strike is None: strike = self._strike
        if contract_type is None: contract_type = self._contact_type
        if premium_output is None: premium_output = self._premium_output
        if position_multiplier is None: position_multiplier = self._position_multiplier
        if fx_options_tenor_for_interpolation is None: fx_options_tenor_for_interpolation = self._fx_options_tenor_for_interpolation

        if freeze_implied_vol is None: freeze_implied_vol = self._freeze_implied_vol

        if depo_tenor_for_option is None: depo_tenor_for_option = self._depo_tenor_for_option
        if tot_label is None: tot_label = self._tot_label
        if cal is None: cal = self._cal

        if output_calculation_fields is None: output_calculation_fields = self._output_calculation_fields

        if not (isinstance(cross_fx, list)):
            cross_fx = [cross_fx]

        total_return_index_df_agg = []

        # Remove columns where there is no data (because these vols typically aren't quoted)
        if market_df is not None:
            market_df = market_df.dropna(how='all', axis=1)

        fx_options_pricer = FXOptionsPricer(premium_output=premium_output)

        def get_roll_date(horizon_d, expiry_d, asset_hols, month_adj=0):
            if roll_event == 'month-end':
                roll_d = horizon_d + CustomBusinessMonthEnd(roll_months + month_adj, holidays=asset_hols)

                # Special case so always rolls on month end date, if specify 0 days
                if roll_days_before > 0:
                    return (roll_d - CustomBusinessDay(n=roll_days_before, holidays=asset_hols))

            elif roll_event == 'expiry-date':
                roll_d = expiry_d

                # Special case so always rolls on expiry date, if specify 0 days
                if roll_days_before > 0:
                    return (roll_d - CustomBusinessDay(n=roll_days_before, holidays=asset_hols))

            return roll_d

        for cross in cross_fx:

            if cal is None:
                cal = cross

            # Eg. if we specify USDUSD
            if cross[0:3] == cross[3:6]:
                total_return_index_df_agg.append(
                    pd.DataFrame(100, index=market_df.index, columns=[cross + "-option-tot.close"]))
            else:
                # Is the FX cross in the correct convention
                old_cross = cross

                cross = FXConv().correct_notation(cross)

                # TODO also specification of non-standard crosses like USDGBP
                if old_cross != cross:
                    pass

                if fx_vol_surface is None:
                    fx_vol_surface = FXVolSurface(market_df=market_df, asset=cross,
                                                  tenors=fx_options_tenor_for_interpolation,
                                                  depo_tenor=depo_tenor_for_option)

                    market_df = fx_vol_surface.get_all_market_data()

                horizon_date = market_df.index

                expiry_date = np.zeros(len(horizon_date), dtype=object)
                roll_date = np.zeros(len(horizon_date), dtype=object)

                new_trade = np.full(len(horizon_date), False, dtype=bool)
                exit_trade = np.full(len(horizon_date), False, dtype=bool)
                has_position = np.full(len(horizon_date), False, dtype=bool)

                asset_holidays = self._calendar.get_holidays(cal=cross)

                # If no entry dates specified, assume we just keep rolling
                if enter_trading_dates is None:
                    # Get first expiry date
                    expiry_date[0] = self._calendar.get_expiry_date_from_horizon_date(pd.DatetimeIndex([horizon_date[0]]),
                                                                fx_options_trading_tenor, cal=cal, asset_class='fx-vol')[0]

                    # For first month want it to expire within that month (for consistency), hence month_adj=0 ONLY here
                    roll_date[0] = get_roll_date(horizon_date[0], expiry_date[0], asset_holidays, month_adj=0)

                    # New trade => entry at beginning AND on every roll
                    new_trade[0] = True
                    exit_trade[0] = False
                    has_position[0] = True

                    # Get all the expiry dates and roll dates
                    # At each "roll/trade" day we need to reset them for the new contract
                    for i in range(1, len(horizon_date)):
                        has_position[i] = True

                        # If the horizon date has reached the roll date (from yesterday), we're done, and we have a
                        # new roll/trade
                        if (horizon_date[i] - roll_date[i - 1]).days >= 0:
                            new_trade[i] = True
                        else:
                            new_trade[i] = False

                        # If we're entering a new trade/contract (and exiting an old trade) we need to get new expiry and roll dates
                        if new_trade[i]:
                            exp = self._calendar.get_expiry_date_from_horizon_date(pd.DatetimeIndex([horizon_date[i]]),
                                fx_options_trading_tenor, cal=cal, asset_class='fx-vol')[0]

                            # Make sure we don't expire on a date in the history where there isn't market data
                            # It is ok for future values to expire after market data (just not in the backtest!)
                            if exp not in market_df.index:
                                exp_index = market_df.index.searchsorted(exp)

                                if exp_index < len(market_df.index):
                                    exp_index = min(exp_index, len(market_df.index))

                                    exp = market_df.index[exp_index]

                            expiry_date[i] = exp

                            roll_date[i] = get_roll_date(horizon_date[i], expiry_date[i], asset_holidays)
                            exit_trade[i] = True
                        else:
                            if horizon_date[i] <= expiry_date[i-1]:
                                # Otherwise use previous expiry and roll dates, because we're still holding same contract
                                expiry_date[i] = expiry_date[i-1]
                                roll_date[i] = roll_date[i-1]
                                exit_trade[i] = False
                            else:
                                exit_trade[i] = True
                else:
                    new_trade[horizon_date.searchsorted(enter_trading_dates)] = True
                    has_position[horizon_date.searchsorted(enter_trading_dates)] = True

                    # Get first expiry date
                    #expiry_date[0] = \
                    #    self._calendar.get_expiry_date_from_horizon_date(pd.DatetimeIndex([horizon_date[0]]),
                    #                                                     fx_options_trading_tenor, cal=cal,
                    #                                                     asset_class='fx-vol')[0]

                    # For first month want it to expire within that month (for consistency), hence month_adj=0 ONLY here
                    #roll_date[0] = get_roll_date(horizon_date[0], expiry_date[0], asset_holidays, month_adj=0)

                    # New trade => entry at beginning AND on every roll
                    #new_trade[0] = True
                    #exit_trade[0] = False
                    #has_position[0] = True

                    # Get all the expiry dates and roll dates
                    # At each "roll/trade" day we need to reset them for the new contract
                    for i in range(0, len(horizon_date)):

                        # If we're entering a new trade/contract (and exiting an old trade) we need to get new expiry and roll dates
                        if new_trade[i]:
                            exp = \
                                self._calendar.get_expiry_date_from_horizon_date(pd.DatetimeIndex([horizon_date[i]]),
                                                                                 fx_options_trading_tenor, cal=cal,
                                                                                 asset_class='fx-vol')[0]

                            # Make sure we don't expire on a date in the history where there isn't market data
                            # It is ok for future values to expire after market data (just not in the backtest!)
                            if exp not in market_df.index:
                                exp_index = market_df.index.searchsorted(exp)

                                if exp_index < len(market_df.index):
                                    exp_index = min(exp_index, len(market_df.index))

                                    exp = market_df.index[exp_index]

                            expiry_date[i] = exp

                            # roll_date[i] = get_roll_date(horizon_date[i], expiry_date[i], asset_holidays)
                            # if i > 0:
                            # Makes the assumption we aren't rolling contracts
                            exit_trade[i] = False
                        else:
                            if i > 0:
                                # Check there's valid expiry on previous day (if not then we're not in an option trade here!)
                                if expiry_date[i-1] == 0:
                                    has_position[i] = False
                                else:
                                    if horizon_date[i] <= expiry_date[i - 1]:
                                        # Otherwise use previous expiry and roll dates, because we're still holding same contract
                                        expiry_date[i] = expiry_date[i - 1]
                                        # roll_date[i] = roll_date[i - 1]
                                        has_position[i] = True

                                    if horizon_date[i] == expiry_date[i]:
                                        exit_trade[i] = True
                                    else:
                                        exit_trade[i] = False

                # Note: may need to add discount factor when marking to market option

                mtm = np.zeros(len(horizon_date))
                calculated_strike = np.zeros(len(horizon_date))
                interpolated_option = np.zeros(len(horizon_date))
                implied_vol = np.zeros(len(horizon_date))
                delta = np.zeros(len(horizon_date))

                # For debugging
                df_temp = pd.DataFrame()

                df_temp['expiry-date'] = expiry_date
                df_temp['horizon-date'] = horizon_date
                df_temp['roll-date'] = roll_date
                df_temp['new-trade'] = new_trade
                df_temp['exit-trade'] = exit_trade
                df_temp['has-position'] = has_position

                if has_position[0]:
                    # Special case: for first day of history (given have no previous positions)
                    option_values_, spot_, strike_, vol_, delta_, expiry_date_, intrinsic_values_  = \
                        fx_options_pricer.price_instrument(cross, horizon_date[0], strike, expiry_date[0],
                            contract_type=contract_type,
                            tenor=fx_options_trading_tenor,
                            fx_vol_surface=fx_vol_surface,
                            return_as_df=False)

                    interpolated_option[0] = option_values_
                    calculated_strike[0] = strike_
                    implied_vol[0] = vol_

                mtm[0] = 0

                # Now price options for rest of history
                # On rolling dates: MTM will be the previous option contract (interpolated)
                # On non-rolling dates: it will be the current option contract
                for i in range(1, len(horizon_date)):
                    if exit_trade[i]:
                        # Price option trade being exited
                        option_values_, spot_, strike_, vol_, delta_, expiry_date_, intrinsic_values_ = \
                            fx_options_pricer.price_instrument(cross, horizon_date[i], calculated_strike[i-1], expiry_date[i-1],
                            contract_type=contract_type,
                            tenor=fx_options_trading_tenor,
                            fx_vol_surface=fx_vol_surface,
                            return_as_df=False)

                        # Store as MTM
                        mtm[i] = option_values_
                        delta[i] = 0 # Note: this will get overwritten if there's a new trade
                        calculated_strike[i] = calculated_strike[i-1] # Note: this will get overwritten if there's a new trade

                    if new_trade[i]:
                        # Price new option trade being entered
                        option_values_, spot_, strike_, vol_, delta_, expiry_date_, intrinsic_values_ = \
                            fx_options_pricer.price_instrument(cross, horizon_date[i], strike, expiry_date[i],
                            contract_type=contract_type,
                            tenor=fx_options_trading_tenor,
                            fx_vol_surface=fx_vol_surface,
                            return_as_df=False)

                        calculated_strike[i] = strike_ # option_output[cross + '-strike.close'].values
                        implied_vol[i] = vol_
                        interpolated_option[i] = option_values_
                        delta[i] = delta_

                    elif has_position[i] and not(exit_trade[i]):
                        # Price current option trade
                        # - strike/expiry the same as yesterday
                        # - other market inputs taken live, closer to expiry
                        calculated_strike[i] = calculated_strike[i-1]

                        if freeze_implied_vol:
                            frozen_vol = implied_vol[i-1]
                        else:
                            frozen_vol = None

                        option_values_, spot_, strike_, vol_, delta_, expiry_date_, intrinsic_values_ = \
                            fx_options_pricer.price_instrument(cross, horizon_date[i], calculated_strike[i],
                                expiry_date[i],
                                vol=frozen_vol,
                                contract_type=contract_type,
                                tenor=fx_options_trading_tenor,
                                fx_vol_surface=fx_vol_surface,
                                return_as_df=False)

                        interpolated_option[i] = option_values_
                        implied_vol[i] = vol_
                        mtm[i] = interpolated_option[i]
                        delta[i] = delta_

                # Calculate delta hedging P&L
                spot_rets = (market_df[cross + ".close"] / market_df[cross + ".close"].shift(1) - 1).values

                if tot_label == '':
                    tot_rets = spot_rets
                else:
                    tot_rets = (market_df[cross + "-" + tot_label + ".close"]
                                 / market_df[cross + "-" + tot_label + ".close"].shift(1) - 1).values

                # Remember to take the inverted sign, eg. if call is +20%, we need to -20% of spot to flatten delta
                # Also invest for whether we are long or short the option
                delta_hedging_pnl = -np.roll(delta, 1) * tot_rets * position_multiplier
                delta_hedging_pnl[0] = 0

                # Calculate options P&L (given option premium is already percentage, only need to subtract)
                # Again need to invert if we are short option
                option_rets = (mtm - np.roll(interpolated_option, 1)) * position_multiplier
                option_rets[0] = 0

                # Calculate option + delta hedging P&L
                option_delta_rets = delta_hedging_pnl + option_rets

                if cum_index == 'mult':
                    cum_rets = 100 * np.cumprod(1.0 + option_rets)
                    cum_delta_rets = 100 * np.cumprod(1.0 + delta_hedging_pnl)
                    cum_option_delta_rets = 100 * np.cumprod(1.0 + option_delta_rets)

                elif cum_index == 'add':
                    cum_rets = 100 + 100 * np.cumsum(option_rets)
                    cum_delta_rets = 100 + 100 * np.cumsum(delta_hedging_pnl)
                    cum_option_delta_rets = 100 + 100 * np.cumsum(option_delta_rets)

                total_return_index_df = pd.DataFrame(index=horizon_date, columns=[cross + "-option-tot.close"])
                total_return_index_df[cross + "-option-tot.close"] = cum_rets

                if output_calculation_fields:
                    total_return_index_df[cross + '-interpolated-option.close'] = interpolated_option
                    total_return_index_df[cross + '-mtm.close'] = mtm
                    total_return_index_df[cross + ".close"] = market_df[cross + ".close"].values
                    total_return_index_df[cross + '-implied-vol.close'] = implied_vol
                    total_return_index_df[cross + '-new-trade.close'] = new_trade
                    total_return_index_df[cross + '.roll-date'] = roll_date
                    total_return_index_df[cross + '-exit-trade.close'] = exit_trade
                    total_return_index_df[cross + '.expiry-date'] = expiry_date
                    total_return_index_df[cross + '-calculated-strike.close'] = calculated_strike
                    total_return_index_df[cross + '-option-return.close'] = option_rets
                    total_return_index_df[cross + '-spot-return.close'] = spot_rets
                    total_return_index_df[cross + '-tot-return.close'] = tot_rets
                    total_return_index_df[cross + '-delta.close'] = delta
                    total_return_index_df[cross + '-delta-pnl-return.close'] = delta_hedging_pnl
                    total_return_index_df[cross + '-delta-pnl-index.close'] = cum_delta_rets
                    total_return_index_df[cross + '-option-delta-return.close'] = option_delta_rets
                    total_return_index_df[cross + '-option-delta-tot.close'] = cum_option_delta_rets

                total_return_index_df_agg.append(total_return_index_df)

        return self._calculations.pandas_outer_join(total_return_index_df_agg)

    def apply_tc_to_total_return_index(self, cross_fx, total_return_index_orig_df, option_tc_bp, spot_tc_bp, cum_index=None):

        if cum_index is None: cum_index = self._cum_index

        total_return_index_df_agg = []

        if not (isinstance(cross_fx, list)):
            cross_fx = [cross_fx]

        option_tc = option_tc_bp / (2 * 100 * 100)
        spot_tc = spot_tc_bp / (2 * 100 * 100)

        total_return_index_df = total_return_index_orig_df.copy()

        for cross in cross_fx:

            # p = abs(total_return_index_df[cross + '-roll.close'].shift(1)) * option_tc
            # q = abs(total_return_index_df[cross + '-delta.close'] - total_return_index_df[cross + '-delta.close'].shift(1)) * spot_tc

            # Additional columns to include P&L with transaction costs
            total_return_index_df[cross + '-option-return-with-tc.close'] = \
                total_return_index_df[cross + '-option-return.close'] - abs(total_return_index_df[cross + '-new-trade.close'].shift(1)) * option_tc
            total_return_index_df[cross + '-delta-pnl-return-with-tc.close'] = \
                total_return_index_df[cross + '-delta-pnl-return.close'] \
                - abs(total_return_index_df[cross + '-delta.close'] - total_return_index_df[cross + '-delta.close'].shift(1)) * spot_tc

            total_return_index_df[cross + '-option-return-with-tc.close'][0] = 0
            total_return_index_df[cross + '-delta-pnl-return-with-tc.close'][0] = 0
            total_return_index_df[cross + '-option-delta-return-with-tc.close'] = \
                total_return_index_df[cross + '-option-return-with-tc.close'] + total_return_index_df[cross + '-delta-pnl-return-with-tc.close']

            if cum_index == 'mult':
                cum_rets = 100 * np.cumprod(1.0 + total_return_index_df[cross + '-option-return-with-tc.close'].values)
                cum_delta_rets = 100 * np.cumprod(1.0 + total_return_index_df[cross + '-delta-pnl-return-with-tc.close'].values)
                cum_option_delta_rets = 100 * np.cumprod(
                    1.0 + total_return_index_df[cross + '-option-delta-return-with-tc.close'].values)

            elif cum_index == 'add':
                cum_rets = 100 + 100 * np.cumsum(total_return_index_df[cross + '-option-return-with-tc.close'].values)
                cum_delta_rets = 100 + 100 * np.cumsum(
                    total_return_index_df[cross + '-delta-pnl-return-with-tc.close'].values)
                cum_option_delta_rets = 100 + 100 * np.cumsum(
                    total_return_index_df[cross + '-option-delta-return-with-tc.close'].values)

            total_return_index_df[cross + "-option-tot-with-tc.close"] = cum_rets
            total_return_index_df[cross + '-delta-pnl-index-with-tc.close'] = cum_delta_rets
            total_return_index_df[cross + '-option-delta-tot-with-tc.close'] = cum_option_delta_rets

            total_return_index_df_agg.append(total_return_index_df)

        return self._calculations.pandas_outer_join(total_return_index_df_agg)





