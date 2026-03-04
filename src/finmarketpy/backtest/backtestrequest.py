"""Backtest request module defining parameters for running a trading strategy backtest."""

__author__ = "saeedamen"  # Saeed Amen

#
# Copyright 2016-2020 Cuemacro - https://www.cuemacro.com / @cuemacro
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.
#

from findatapy.market import MarketDataRequest
from findatapy.util.loggermanager import LoggerManager
from pandas import DataFrame

from finmarketpy.economics import TechParams


class BacktestRequest(MarketDataRequest):
    """Contains parameters necessary to define a backtest, including start date, finish date, transaction cost, etc.

    Used by TradingModel and Backtest to construct backtested returns for trading strategies

    """

    def __init__(self):
        """Initialise BacktestRequest with default backtest parameters."""
        super(MarketDataRequest, self).__init__()

        self.__signal_name = None

        # Output parameters for backtest (should we add returns statistics on legends, write CSVs with returns etc.)
        self.__plot_start = None
        self.__plot_finish = None
        self.__calc_stats = True
        self.__write_csv = False
        self.__write_csv_pnl = False
        self.__plot_interim = False
        self.__include_benchmark = False

        self.__trading_field = "close"

        self.__tech_params = TechParams()

        self.__portfolio_weight_construction = None

        # Default parameters for portfolio level vol adjustment
        self.__portfolio_vol_adjust = False
        self.__portfolio_vol_period_shift = 0
        self.__portfolio_vol_rebalance_freq = None
        self.__portfolio_vol_resample_freq = None
        self.__portfolio_vol_resample_type = "mean"
        self.__portfolio_vol_target = 0.1  # 10% vol target
        self.__portfolio_vol_max_leverage = None
        self.__portfolio_vol_periods = 20
        self.__portfolio_vol_obs_in_year = 252

        # Default parameters for signal level vol adjustment
        self.__signal_vol_adjust = False
        self.__signal_vol_period_shift = 0
        self.__signal_vol_rebalance_freq = None
        self.__signal_vol_resample_freq = None
        self.__signal_vol_resample_type = "mean"
        self.__signal_vol_target = 0.1  # 10% vol target
        self.__signal_vol_max_leverage = None
        self.__signal_vol_periods = 20
        self.__signal_vol_obs_in_year = 252

        # Portfolio notional size
        self.__portfolio_notional_size = None
        self.__portfolio_combination = None
        self.__portfolio_combination_weights = None

        # Parameters for maximum position limits (expressed as whole portfolio)
        self.__max_net_exposure = None
        self.__max_abs_exposure = None

        self.__position_clip_rebalance_freq = None
        self.__position_clip_resample_freq = (
            None  # by default apply max position criterion on last business day of month
        )
        self.__position_clip_resample_type = "mean"
        self.__position_clip_period_shift = 0

        # Take profit and stop loss parameters
        self.__take_profit = None
        self.__stop_loss = None

        # Should we delay the signal?
        self.__signal_delay = 0

        # Annualization factor for return stats (and should we resample data first before calculating it?)
        self.__ann_factor = 252
        self.__resample_ann_factor = None

        self.__spot_rc_bp = None

        # How do we create a cumulative index of strategy returns
        # either multiplicative starting a 100
        # or additive starting at 0
        self.__cum_index = "mult"  # 'mult' or 'add'

    ##### properties for output of the backtest
    @property
    def plot_start(self):
        """Return the plot start."""
        return self.__plot_start

    @plot_start.setter
    def plot_start(self, plot_start):
        """Set the plot start."""
        self.__plot_start = plot_start

    @property
    def plot_finish(self):
        """Return the plot finish."""
        return self.__plot_finish

    @plot_finish.setter
    def plot_finish(self, plot_finish):
        """Set the plot finish."""
        self.__plot_finish = plot_finish

    @property
    def calc_stats(self):
        """Return the calc stats."""
        return self.__calc_stats

    @calc_stats.setter
    def calc_stats(self, calc_stats):
        """Set the calc stats."""
        self.__calc_stats = calc_stats

    @property
    def write_csv(self):
        """Return the write csv."""
        return self.__write_csv

    @write_csv.setter
    def write_csv(self, write_csv):
        """Set the write csv."""
        self.__write_csv = write_csv

    @property
    def write_csv_pnl(self):
        """Return the write csv pnl."""
        return self.__write_csv_pnl

    @write_csv_pnl.setter
    def write_csv_pnl(self, write_csv_pnl):
        """Set the write csv pnl."""
        self.__write_csv_pnl = write_csv_pnl

    @property
    def plot_interim(self):
        """Return the plot interim."""
        return self.__plot_interim

    @plot_interim.setter
    def plot_interim(self, plot_interim):
        """Set the plot interim."""
        self.__plot_interim = plot_interim

    @property
    def include_benchmark(self):
        """Return the include benchmark."""
        return self.__include_benchmark

    @include_benchmark.setter
    def include_benchmark(self, include_benchmark):
        """Set the include benchmark."""
        self.__include_benchmark = include_benchmark

    @property
    def trading_field(self):
        """Return the trading field."""
        return self.__trading_field

    @trading_field.setter
    def trading_field(self, trading_field):
        """Set the trading field."""
        self.__trading_field = trading_field

    @property
    def portfolio_weight_construction(self):
        """Return the portfolio weight construction."""
        return self.__portfolio_weight_construction

    @portfolio_weight_construction.setter
    def portfolio_weight_construction(self, portfolio_weight_construction):
        """Set the portfolio weight construction."""
        self.__portfolio_weight_construction = portfolio_weight_construction

    ##### Properties for portfolio level volatility adjustment

    @property
    def portfolio_vol_adjust(self):
        """Return the portfolio vol adjust."""
        return self.__portfolio_vol_adjust

    @portfolio_vol_adjust.setter
    def portfolio_vol_adjust(self, portfolio_vol_adjust):
        """Set the portfolio vol adjust."""
        self.__portfolio_vol_adjust = portfolio_vol_adjust

    @property
    def portfolio_vol_rebalance_freq(self):
        """Return the portfolio vol rebalance freq."""
        return self.__portfolio_vol_rebalance_freq

    @portfolio_vol_rebalance_freq.setter
    def portfolio_vol_rebalance_freq(self, portfolio_vol_rebalance_freq):
        """Set the portfolio vol rebalance freq."""
        self.__portfolio_vol_rebalance_freq = portfolio_vol_rebalance_freq

    @property
    def portfolio_vol_resample_type(self):
        """Return the portfolio vol resample type."""
        return self.__portfolio_vol_resample_type

    @portfolio_vol_resample_type.setter
    def portfolio_vol_resample_type(self, portfolio_vol_resample_type):
        """Set the portfolio vol resample type."""
        self.__portfolio_vol_resample_type = portfolio_vol_resample_type

    @property
    def portfolio_vol_resample_freq(self):
        """Return the portfolio vol resample freq."""
        return self.__portfolio_vol_resample_freq

    @portfolio_vol_resample_freq.setter
    def portfolio_vol_resample_freq(self, portfolio_vol_resample_freq):
        """Set the portfolio vol resample freq."""
        self.__portfolio_vol_resample_freq = portfolio_vol_resample_freq

    @property
    def portfolio_vol_period_shift(self):
        """Return the portfolio vol period shift."""
        return self.__portfolio_vol_period_shift

    @portfolio_vol_period_shift.setter
    def portfolio_vol_period_shift(self, portfolio_vol_period_shift):
        """Set the portfolio vol period shift."""
        self.__portfolio_vol_period_shift = portfolio_vol_period_shift

    @property
    def portfolio_vol_target(self):
        """Return the portfolio vol target."""
        return self.__portfolio_vol_target

    @portfolio_vol_target.setter
    def portfolio_vol_target(self, portfolio_vol_target):
        """Set the portfolio vol target."""
        self.__portfolio_vol_target = portfolio_vol_target

    @property
    def portfolio_vol_max_leverage(self):
        """Return the portfolio vol max leverage."""
        return self.__portfolio_vol_max_leverage

    @portfolio_vol_max_leverage.setter
    def portfolio_vol_max_leverage(self, portfolio_vol_max_leverage):
        """Set the portfolio vol max leverage."""
        self.__portfolio_vol_max_leverage = portfolio_vol_max_leverage

    @property
    def portfolio_vol_periods(self):
        """Return the portfolio vol periods."""
        return self.__portfolio_vol_periods

    @portfolio_vol_periods.setter
    def portfolio_vol_periods(self, portfolio_vol_periods):
        """Set the portfolio vol periods."""
        self.__portfolio_vol_periods = portfolio_vol_periods

    @property
    def portfolio_vol_obs_in_year(self):
        """Return the portfolio vol obs in year."""
        return self.__portfolio_vol_obs_in_year

    @portfolio_vol_obs_in_year.setter
    def portfolio_vol_obs_in_year(self, portfolio_vol_obs_in_year):
        """Set the portfolio vol obs in year."""
        self.__portfolio_vol_obs_in_year = portfolio_vol_obs_in_year

    ##### properties for signal level vol adjustment
    @property
    def signal_vol_adjust(self):
        """Return the signal vol adjust."""
        return self.__signal_vol_adjust

    @signal_vol_adjust.setter
    def signal_vol_adjust(self, signal_vol_adjust):
        """Set the signal vol adjust."""
        self.__signal_vol_adjust = signal_vol_adjust

    @property
    def signal_vol_rebalance_freq(self):
        """Return the signal vol rebalance freq."""
        return self.__signal_vol_rebalance_freq

    @signal_vol_rebalance_freq.setter
    def signal_vol_rebalance_freq(self, signal_vol_rebalance_freq):
        """Set the signal vol rebalance freq."""
        self.__signal_vol_rebalance_freq = signal_vol_rebalance_freq

    @property
    def signal_vol_resample_type(self):
        """Return the signal vol resample type."""
        return self.__signal_vol_resample_type

    @signal_vol_resample_type.setter
    def signal_vol_resample_type(self, signal_vol_resample_type):
        """Set the signal vol resample type."""
        self.__signal_vol_resample_type = signal_vol_resample_type

    @property
    def signal_vol_resample_freq(self):
        """Return the signal vol resample freq."""
        return self.__signal_vol_resample_freq

    @signal_vol_resample_freq.setter
    def signal_vol_resample_freq(self, signal_vol_resample_freq):
        """Set the signal vol resample freq."""
        self.__signal_vol_resample_freq = signal_vol_resample_freq

    @property
    def signal_vol_period_shift(self):
        """Return the signal vol period shift."""
        return self.__signal_vol_period_shift

    @signal_vol_period_shift.setter
    def signal_vol_period_shift(self, signal_vol_period_shift):
        """Set the signal vol period shift."""
        self.__signal_vol_period_shift = signal_vol_period_shift

    @property
    def signal_vol_target(self):
        """Return the signal vol target."""
        return self.__signal_vol_target

    @signal_vol_target.setter
    def signal_vol_target(self, signal_vol_target):
        """Set the signal vol target."""
        self.__signal_vol_target = signal_vol_target

    @property
    def signal_vol_max_leverage(self):
        """Return the signal vol max leverage."""
        return self.__signal_vol_max_leverage

    @signal_vol_max_leverage.setter
    def signal_vol_max_leverage(self, signal_vol_max_leverage):
        """Set the signal vol max leverage."""
        self.__signal_vol_max_leverage = signal_vol_max_leverage

    @property
    def signal_vol_periods(self):
        """Return the signal vol periods."""
        return self.__signal_vol_periods

    @signal_vol_periods.setter
    def signal_vol_periods(self, signal_vol_periods):
        """Set the signal vol periods."""
        self.__signal_vol_periods = signal_vol_periods

    @property
    def signal_vol_obs_in_year(self):
        """Return the signal vol obs in year."""
        return self.__signal_vol_obs_in_year

    @signal_vol_obs_in_year.setter
    def signal_vol_obs_in_year(self, signal_vol_obs_in_year):
        """Set the signal vol obs in year."""
        self.__signal_vol_obs_in_year = signal_vol_obs_in_year

    ##### portfolio notional size
    @property
    def portfolio_notional_size(self):
        """Return the portfolio notional size."""
        return self.__portfolio_notional_size

    @portfolio_notional_size.setter
    def portfolio_notional_size(self, portfolio_notional_size):
        """Set the portfolio notional size."""
        self.__portfolio_notional_size = float(portfolio_notional_size)

    ##### portfolio combination style (sum, mean, weighted, weighted-sum)
    @property
    def portfolio_combination(self):
        """Return the portfolio combination."""
        return self.__portfolio_combination

    @portfolio_combination.setter
    def portfolio_combination(self, portfolio_combination):
        """Set the portfolio combination."""
        self.__portfolio_combination = portfolio_combination

    ##### portfolio weights (sum, mean)
    @property
    def portfolio_combination_weights(self):
        """Return the portfolio combination weights."""
        return self.__portfolio_combination_weights

    @portfolio_combination_weights.setter
    def portfolio_combination_weights(self, portfolio_combination_weights):
        """Set the portfolio combination weights."""
        self.__portfolio_combination_weights = portfolio_combination_weights

    ##### properties for maximum position constraints
    @property
    def max_net_exposure(self):
        """Return the max net exposure."""
        return self.__max_net_exposure

    @max_net_exposure.setter
    def max_net_exposure(self, max_net_exposure):
        """Set the max net exposure."""
        self.__max_net_exposure = max_net_exposure

    @property
    def max_abs_exposure(self):
        """Return the max abs exposure."""
        return self.__max_abs_exposure

    @max_abs_exposure.setter
    def max_abs_exposure(self, max_abs_exposure):
        """Set the max abs exposure."""
        self.__max_abs_exposure = max_abs_exposure

    @property
    def position_clip_rebalance_freq(self):
        """Return the position clip rebalance freq."""
        return self.__position_clip_rebalance_freq

    @position_clip_rebalance_freq.setter
    def position_clip_rebalance_freq(self, position_clip_rebalance_freq):
        """Set the position clip rebalance freq."""
        self.__position_clip_rebalance_freq = position_clip_rebalance_freq

    @property
    def position_clip_resample_type(self):
        """Return the position clip resample type."""
        return self.__position_clip_resample_type

    @position_clip_resample_type.setter
    def position_clip_resample_type(self, position_clip_resample_type):
        """Set the position clip resample type."""
        self.__position_clip_resample_type = position_clip_resample_type

    @property
    def position_clip_resample_freq(self):
        """Return the position clip resample freq."""
        return self.__position_clip_resample_freq

    @position_clip_resample_freq.setter
    def position_clip_resample_freq(self, position_clip_resample_freq):
        """Set the position clip resample freq."""
        self.__position_clip_resample_freq = position_clip_resample_freq

    @property
    def position_clip_period_shift(self):
        """Return the position clip period shift."""
        return self.__position_clip_period_shift

    @position_clip_period_shift.setter
    def position_clip_period_shift(self, position_clip_period_shift):
        """Set the position clip period shift."""
        self.__position_clip_period_shift = position_clip_period_shift

    ##### stop loss and take profit
    @property
    def stop_loss(self):
        """Return the stop loss."""
        return self.__stop_loss

    @stop_loss.setter
    def stop_loss(self, stop_loss):
        """Set the stop loss."""
        self.__stop_loss = stop_loss

    @property
    def take_profit(self):
        """Return the take profit."""
        return self.__take_profit

    @take_profit.setter
    def take_profit(self, take_profit):
        """Set the take profit."""
        self.__take_profit = take_profit

    ##### tech indicators and spot bp tc
    @property
    def tech_params(self):
        """Return the tech params."""
        return self.__tech_params

    @tech_params.setter
    def tech_params(self, tech_params):
        """Set the tech params."""
        self.__tech_params = tech_params

    @property
    def spot_tc_bp(self):
        """Return the spot tc bp."""
        return self.__spot_tc_bp

    @spot_tc_bp.setter
    def spot_tc_bp(self, spot_tc_bp):
        """Set the spot tc bp."""
        if isinstance(spot_tc_bp, dict):
            spot_tc_bp = spot_tc_bp.copy()

            for k in spot_tc_bp:
                spot_tc_bp[k] = float(spot_tc_bp[k]) / (2.0 * 100.0 * 100.0)

            self.__spot_tc_bp = spot_tc_bp

        elif isinstance(spot_tc_bp, DataFrame):
            self.__spot_tc_bp = spot_tc_bp  # assume that DataFrame is in the percentage form (bid to mid)
        else:
            self.__spot_tc_bp = float(spot_tc_bp) / (2.0 * 100.0 * 100.0)

    @property
    def spot_rc_bp(self):
        """Return the spot rc bp."""
        return self.__spot_rc_bp

    @spot_rc_bp.setter
    def spot_rc_bp(self, spot_rc_bp):
        """Set the spot rc bp."""
        if isinstance(spot_rc_bp, dict):
            spot_rc_bp = spot_rc_bp.copy()

            for k in spot_rc_bp:
                spot_rc_bp[k] = float(spot_rc_bp[k]) / (100.0 * 100.0)

            self.__spot_rc_bp = spot_rc_bp

        elif isinstance(spot_rc_bp, DataFrame):
            self.__spot_rc_bp = spot_rc_bp  # assume that DataFrame is in the percentage form (bid to mid)
        else:
            self.__spot_rc_bp = float(spot_rc_bp) / (100.0 * 100.0)

    #### FOR FUTURE USE ###

    @property
    def signal_name(self):
        """Return the signal name."""
        return self.__signal_name

    @signal_name.setter
    def signal_name(self, signal_name):
        """Set the signal name."""
        self.__signal_name = signal_name

    @property
    def asset(self):
        """Return the asset."""
        return self.__asset

    @asset.setter
    def asset(self, asset):
        """Set the asset."""
        valid_asset = ["fx", "multi-asset"]

        if asset not in valid_asset:
            LoggerManager().getLogger(__name__).warning(asset & " is not a defined asset.")

        self.__asset = asset

    @property
    def instrument(self):
        """Return the instrument."""
        return self.__instrument

    @instrument.setter
    def instrument(self, instrument):
        """Set the instrument."""
        valid_instrument = ["spot", "futures", "options"]

        if instrument not in valid_instrument:
            LoggerManager().getLogger(__name__).warning(instrument & " is not a defined trading instrument.")

        self.__instrument = instrument

    @property
    def signal_delay(self):
        """Return the signal delay."""
        return self.__signal_delay

    @signal_delay.setter
    def signal_delay(self, signal_delay):
        """Set the signal delay."""
        self.__signal_delay = signal_delay

    @property
    def ann_factor(self):
        """Return the ann factor."""
        return self.__ann_factor

    @ann_factor.setter
    def ann_factor(self, ann_factor):
        """Set the ann factor."""
        self.__ann_factor = ann_factor

    @property
    def resample_ann_factor(self):
        """Return the resample ann factor."""
        return self.__resample_ann_factor

    @resample_ann_factor.setter
    def resample_ann_factor(self, resample_ann_factor):
        """Set the resample ann factor."""
        self.__resample_ann_factor = resample_ann_factor

    @property
    def cum_index(self):
        """Return the cum index."""
        return self.__cum_index

    @cum_index.setter
    def cum_index(self, cum_index):
        """Set the cum index."""
        self.__cum_index = cum_index
