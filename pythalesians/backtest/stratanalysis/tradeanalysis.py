__author__ = 'saeedamen'

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
TradeAnalysis

Applies some basic trade analysis for a trading strategy (as defined by StrategyTemplate). Use PyFolio to create some
basic trading statistics. Also allows you test multiple parameters for a specific strategy (like TC).

"""

pf = None

try:
    import pyfolio as pf
except: pass

import datetime
import pandas

from pythalesians.util.loggermanager import LoggerManager
from pythalesians.timeseries.calcs.timeseriestimezone import TimeSeriesTimezone
from pythalesians.timeseries.calcs.timeseriescalcs import TimeSeriesCalcs
from pythalesians.util.constants import Constants

from pythalesians.backtest.cash.cashbacktest import CashBacktest
from pythalesians.graphics.graphs.plotfactory import PlotFactory
from pythalesians.graphics.graphs.graphproperties import GraphProperties

import matplotlib
import matplotlib.pyplot as plt

class TradeAnalysis:

    def __init__(self):
        self.logger = LoggerManager().getLogger(__name__)
        self.DUMP_PATH = 'output_data/' + datetime.date.today().strftime("%Y%m%d") + ' '
        self.scale_factor = 3
        return

    def run_strategy_returns_stats(self, strategy):
        """
        run_strategy_returns_stats - Plots useful statistics for the trading strategy (using PyFolio)

        Parameters
        ----------
        strategy : StrategyTemplate
            defining trading strategy

        """

        pnl = strategy.get_strategy_pnl()
        tz = TimeSeriesTimezone()
        tsc = TimeSeriesCalcs()

        # PyFolio assumes UTC time based DataFrames (so force this localisation)
        try:
            pnl = tz.localise_index_as_UTC(pnl)
        except: pass

        # set the matplotlib style sheet & defaults
        try:
            matplotlib.rcdefaults()
            plt.style.use(Constants().plotfactory_pythalesians_style_sheet['pythalesians'])
        except: pass

        # TODO for intraday strategies, make daily

        # convert DataFrame (assumed to have only one column) to Series
        pnl = tsc.calculate_returns(pnl)
        pnl = pnl[pnl.columns[0]]

        fig = pf.create_returns_tear_sheet(pnl, return_fig=True)

        try:
            plt.savefig (strategy.DUMP_PATH + "stats.png")
        except: pass

        plt.show()

    def run_tc_shock(self, strategy, tc = None):
        if tc is None: tc = [0, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2.0]

        parameter_list = [{'spot_tc_bp' : x } for x in tc]
        pretty_portfolio_names = [str(x) + 'bp' for x in tc]    # names of the portfolio
        parameter_type = 'TC analysis'                          # broad type of parameter name

        return self.run_arbitrary_sensitivity(strategy,
                                 parameter_list=parameter_list,
                                 pretty_portfolio_names=pretty_portfolio_names,
                                 parameter_type=parameter_type)

    ###### Parameters and signal generations (need to be customised for every model)
    def run_arbitrary_sensitivity(self, strat, parameter_list = None, parameter_names = None,
                                  pretty_portfolio_names = None, parameter_type = None):

        asset_df, spot_df, spot_df2, basket_dict = strat.fill_assets()

        port_list = None

        for i in range(0, len(parameter_list)):
            br = strat.fill_backtest_request()

            current_parameter = parameter_list[i]

            # for calculating P&L
            for k in current_parameter.keys():
                setattr(br, k, current_parameter[k])

            strat.br = br   # for calculating signals

            signal_df = strat.construct_signal(spot_df, spot_df2, br.tech_params, br)

            cash_backtest = CashBacktest()
            self.logger.info("Calculating... " + pretty_portfolio_names[i])

            cash_backtest.calculate_trading_PnL(br, asset_df, signal_df)
            stats = str(cash_backtest.get_portfolio_pnl_desc()[0])

            port = cash_backtest.get_cumportfolio().resample('B')
            port.columns = [pretty_portfolio_names[i] + ' ' + stats]

            if port_list is None:
                port_list = port
            else:
                port_list = port_list.join(port)

        # reset the parameters of the strategy
        strat.br = strat.fill_backtest_request()

        pf = PlotFactory()
        gp = GraphProperties()

        # gp.color = 'Blues'
        gp.resample = 'B'
        gp.file_output = self.DUMP_PATH + strat.FINAL_STRATEGY + ' ' + parameter_type + '.png'
        gp.scale_factor = self.scale_factor
        gp.title = strat.FINAL_STRATEGY + ' ' + parameter_type
        pf.plot_line_graph(port_list, adapter = 'pythalesians', gp = gp)

        return port_list

    ###### Parameters and signal generations (need to be customised for every model)
    ###### Plot all the output seperately
    def run_arbitrary_sensitivity_separately(self, strat, parameter_list = None,
                                  pretty_portfolio_names = None, strip = None):

        # asset_df, spot_df, spot_df2, basket_dict = strat.fill_assets()
        final_strategy = strat.FINAL_STRATEGY

        for i in range(0, len(parameter_list)):
            br = strat.fill_backtest_request()

            current_parameter = parameter_list[i]

            # for calculating P&L
            for k in current_parameter.keys():
                setattr(br, k, current_parameter[k])

            strat.FINAL_STRATEGY = final_strategy + " " + pretty_portfolio_names[i]

            self.logger.info("Calculating... " + pretty_portfolio_names[i])
            strat.br = br
            strat.construct_strategy(br = br)

            strat.plot_strategy_pnl()
            strat.plot_strategy_leverage()
            strat.plot_strategy_group_benchmark_pnl(strip = strip)

    def run_day_of_month_analysis(self, strat):
        from pythalesians.economics.seasonality.seasonality import Seasonality
        from pythalesians.timeseries.calcs.timeseriescalcs import TimeSeriesCalcs

        tsc = TimeSeriesCalcs()
        seas = Seasonality()
        strat.construct_strategy()
        pnl = strat.get_strategy_pnl()

        # get seasonality by day of the month
        pnl = pnl.resample('B')
        rets = tsc.calculate_returns(pnl)
        bus_day = seas.bus_day_of_month_seasonality(rets, add_average = True)

        # get seasonality by month
        pnl = pnl.resample('BM')
        rets = tsc.calculate_returns(pnl)
        month = seas.monthly_seasonality(rets)

        self.logger.info("About to plot seasonality...")
        gp = GraphProperties()
        pf = PlotFactory()

        # Plotting spot over day of month/month of year
        gp.color = 'Blues'
        gp.scale_factor = self.scale_factor
        gp.file_output = self.DUMP_PATH + strat.FINAL_STRATEGY + ' seasonality day of month.png'
        gp.title = strat.FINAL_STRATEGY + ' day of month seasonality'
        gp.display_legend = False
        gp.color_2_series = [bus_day.columns[-1]]
        gp.color_2 = ['red'] # red, pink
        gp.linewidth_2 = 4
        gp.linewidth_2_series = [bus_day.columns[-1]]
        gp.y_axis_2_series = [bus_day.columns[-1]]

        pf.plot_line_graph(bus_day, adapter = 'pythalesians', gp = gp)

        gp = GraphProperties()

        gp.scale_factor = self.scale_factor
        gp.file_output = self.DUMP_PATH + strat.FINAL_STRATEGY + ' seasonality month of year.png'
        gp.title = strat.FINAL_STRATEGY + ' month of year seasonality'

        pf.plot_line_graph(month, adapter = 'pythalesians', gp = gp)

        return month




