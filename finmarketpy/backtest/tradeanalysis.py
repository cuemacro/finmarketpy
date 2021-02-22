__author__ = 'saeedamen'

#
# Copyright 2016-2020 Cuemacro
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the
# License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied_.
#
# See the License for the specific language governing permissions and limitations under the License.
#

pf = None

try:
    import pyfolio as pf
except:
    pass

import datetime

# import matplotlib
# import matplotlib.pyplot as plt
import pandas
import copy

from chartpy import Chart, Style, ChartConstants
from findatapy.timeseries import Calculations, Timezone
from findatapy.util.loggermanager import LoggerManager
from finmarketpy.backtest import Backtest

from finmarketpy.util.marketconstants import MarketConstants
from findatapy.util.swimpool import SwimPool

market_constants = MarketConstants()


class TradeAnalysis(object):
    """Applies some basic trade analysis for a trading strategy (as defined by TradingModel). Use PyFolio to create some
    basic trading statistics. Also allows you test multiple parameters for a specific strategy (like TC).

    """

    def __init__(self, engine=ChartConstants().chartfactory_default_engine):
        # self.logger = LoggerManager().getLogger(__name__)
        self.DUMP_PATH = 'output_data/' + datetime.date.today().strftime("%Y%m%d") + ' '
        self.DEFAULT_PLOT_ENGINE = engine
        self.chart = Chart(engine=self.DEFAULT_PLOT_ENGINE)

        return

    def run_strategy_returns_stats(self, trading_model, index=None, engine='finmarketpy'):
        """Plots useful statistics for the trading strategy using various backends

        Parameters
        ----------
        trading_model : TradingModel
            defining trading strategy

        engine : str
            'pyfolio' - use PyFolio as a backend
            'finmarketpy' - use finmarketpy as a backend

        index: DataFrame
            define strategy by a time series

        """

        if index is None:
            pnl = trading_model.strategy_pnl()
        else:
            pnl = index

        tz = Timezone()
        calculations = Calculations()

        if engine == 'pyfolio':
            # PyFolio assumes UTC time based DataFrames (so force this localisation)
            try:
                pnl = tz.localize_index_as_UTC(pnl)
            except:
                pass

            # set the matplotlib style sheet & defaults
            # at present this only works in Matplotlib engine
            try:
                import matplotlib
                import matplotlib.pyplot as plt
                matplotlib.rcdefaults()
                plt.style.use(ChartConstants().chartfactory_style_sheet['chartpy-pyfolio'])
            except:
                pass

            # TODO for intraday strategies, make daily

            # convert DataFrame (assumed to have only one column) to Series
            pnl = calculations.calculate_returns(pnl)
            pnl = pnl.dropna()
            pnl = pnl[pnl.columns[0]]
            fig = pf.create_returns_tear_sheet(pnl, return_fig=True)

            try:
                plt.savefig(trading_model.DUMP_PATH + "stats.png")
            except:
                pass

            plt.show()
        elif engine == 'finmarketpy':

            # assume we have TradingModel
            # to do to take in a time series
            from chartpy import Canvas, Chart

            # temporarily make scale factor smaller so fits the window
            old_scale_factor = trading_model.SCALE_FACTOR
            trading_model.SCALE_FACTOR = 0.75

            pnl = trading_model.plot_strategy_pnl(silent_plot=True)  # plot the final strategy
            individual = trading_model.plot_strategy_group_pnl_trades(
                silent_plot=True)  # plot the individual trade P&Ls

            pnl_comp = trading_model.plot_strategy_group_benchmark_pnl(
                silent_plot=True)  # plot all the cumulative P&Ls of each component
            ir_comp = trading_model.plot_strategy_group_benchmark_pnl_ir(
                silent_plot=True)  # plot all the IR of each component

            leverage = trading_model.plot_strategy_leverage(silent_plot=True)  # plot the leverage of the portfolio
            ind_lev = trading_model.plot_strategy_group_leverage(silent_plot=True)  # plot all the individual leverages

            canvas = Canvas([[pnl, individual],
                             [pnl_comp, ir_comp],
                             [leverage, ind_lev]]
                            )

            canvas.generate_canvas(page_title=trading_model.FINAL_STRATEGY + ' Return Statistics',
                                   silent_display=False, canvas_plotter='plain',
                                   output_filename=trading_model.FINAL_STRATEGY + ".html", render_pdf=False)

            trading_model.SCALE_FACTOR = old_scale_factor

    def run_excel_trade_report(self, trading_model, excel_file='model.xlsx'):
        """
        run_excel_trade_report - Creates an Excel spreadsheet with model returns and latest trades

        Parameters
        ----------
        trading_model : TradingModel
            defining trading strategy (can be a list)

        """

        trading_model_list = trading_model

        if not (isinstance(trading_model_list, list)):
            trading_model_list = [trading_model]

        writer = pandas.ExcelWriter(excel_file, engine='xlsxwriter')

        for tm in trading_model_list:
            strategy_name = tm.FINAL_STRATEGY
            returns = tm.strategy_group_benchmark_pnl()

            returns.to_excel(writer, sheet_name=strategy_name + ' rets', engine='xlsxwriter')

            # write raw position/trade sizes
            self.save_positions_trades(tm, tm.strategy_signal(), tm.strategy_trade(),
                                       'pos', 'trades', writer)

            if hasattr(tm, '_strategy_signal_notional'):
                signal_notional = tm.strategy_signal_notional()
                trading_notional = tm.strategy_signal_notional()

                if signal_notional is not None and trading_notional is not None:
                    # write position/trade sizes scaled by notional
                    self.save_positions_trades(tm,
                                               signal_notional,
                                               trading_notional, 'pos - Not', 'trades - Not', writer)

            if hasattr(tm, '_strategy_signal_contracts'):
                signal_contracts = tm.strategy_signal_contracts()
                trade_contracts = tm.strategy_trade_contracts()

                if signal_contracts is not None and trade_contracts is not None:
                    # write position/trade sizes in terms of contract sizes
                    self.save_positions_trades(tm,
                                               signal_contracts,
                                               trade_contracts, 'pos - Cont', 'trades - Cont', writer)

        # TODO Add summary sheet comparing return statistics for all the different models in the list

        writer.save()
        writer.close()

    def save_positions_trades(self, tm, signals, trades, signal_caption, trade_caption, writer):
        signals.to_excel(writer, sheet_name=tm.FINAL_STRATEGY + ' hist ' + signal_caption, engine='xlsxwriter')

        if hasattr(tm, 'STRIP'):
            strip = tm.STRIP
        else:
            strip = ''

        recent_signals = tm._grab_signals(signals, date=[-1, -2, -5, -10, -20], strip=strip)
        recent_trades = tm._grab_signals(trades, date=[-1, -2, -5, -10, -20], strip=strip)

        recent_signals.to_excel(writer, sheet_name=tm.FINAL_STRATEGY + ' ' + signal_caption, engine='xlsxwriter')
        recent_trades.to_excel(writer, sheet_name=tm.FINAL_STRATEGY + ' ' + trade_caption, engine='xlsxwriter')

    def run_tc_shock(self, strategy, tc=None, run_in_parallel=False, reload_market_data=True):
        if tc is None: tc = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]

        parameter_list = [{'spot_tc_bp': x} for x in tc]
        pretty_portfolio_names = [str(x) + 'bp' for x in tc]  # names of the portfolio
        parameter_type = 'TC analysis'  # broad type of parameter name

        return self.run_arbitrary_sensitivity(strategy,
                                              parameter_list=parameter_list,
                                              pretty_portfolio_names=pretty_portfolio_names,
                                              parameter_type=parameter_type,
                                              run_in_parallel=run_in_parallel,
                                              reload_market_data=reload_market_data)

    ###### Parameters and signal generations (need to be customised for every model)
    def run_arbitrary_sensitivity(self, trading_model, parameter_list=None,
                                  pretty_portfolio_names=None, parameter_type=None, run_in_parallel=False,
                                  reload_market_data=True, plot=True):

        if not(reload_market_data):
            asset_df, spot_df, spot_df2, basket_dict, contract_value_df = self._load_assets(trading_model)

        port_list = []
        ret_stats_list = []

        if market_constants.backtest_thread_no[market_constants.generic_plat] > 1 and run_in_parallel:
            swim_pool = SwimPool(multiprocessing_library=market_constants.multiprocessing_library)

            pool = swim_pool.create_pool(thread_technique=market_constants.backtest_thread_technique,
                                         thread_no=market_constants.backtest_thread_no[market_constants.generic_plat])

            mult_results = []

            for i in range(0, len(parameter_list)):
                # br = copy.copy(trading_model.load_parameters())
                # reset all parameters
                br = copy.copy(trading_model.load_parameters())

                current_parameter = parameter_list[i]

                # for calculating P&L, change the assets
                for k in current_parameter.keys():
                    setattr(br, k, current_parameter[k])
                    setattr(br.tech_params, k, current_parameter[k])

                # should specify reloading the data, if our parameters impact which assets we are fetching
                if reload_market_data:
                    asset_df, spot_df, spot_df2, basket_dict, contract_value_df = self._load_assets(trading_model, br = br)

                mult_results.append(
                    pool.apply_async(self._run_strategy, args=(trading_model, asset_df, spot_df, spot_df2, br,
                                                               contract_value_df,
                                                               pretty_portfolio_names[i],)))

            for p in mult_results:
                port, ret_stats = p.get()

                port_list.append(port)
                ret_stats_list.append(ret_stats)

            try:
                swim_pool.close_pool(pool)
            except:
                pass

        else:
            for i in range(0, len(parameter_list)):
                # reset all parameters
                br = copy.copy(trading_model.load_parameters())

                current_parameter = parameter_list[i]

                # for calculating P&L
                for k in current_parameter.keys():
                    setattr(br, k, current_parameter[k])
                    setattr(br.tech_params, k, current_parameter[k])

                # should specify reloading the data, if our parameters impact which assets we are fetching
                if reload_market_data:
                    asset_df, spot_df, spot_df2, basket_dict, contract_value_df = self._load_assets(trading_model, br = br)

                # br = copy.copy(trading_model.br)

                port, ret_stats = self._run_strategy(trading_model, asset_df, spot_df, spot_df2, br, contract_value_df,
                                                     pretty_portfolio_names[i])

                port_list.append(port)
                ret_stats_list.append(ret_stats)

        port_list = Calculations().join(port_list, how='outer')

        # reset the parameters of the strategy
        trading_model.br = trading_model.load_parameters()

        style = Style()

        ir = [t.inforatio()[0] for t in ret_stats_list]
        rets = [t.ann_returns()[0] for t in ret_stats_list]

        # if we have too many combinations remove legend and use scaled shaded colour
        # if len(port_list) > 10:
        # style.color = 'Blues'
        # style.display_legend = False

        # careful with plotting labels, may need to convert to strings
        pretty_portfolio_names = [str(p) for p in pretty_portfolio_names]

        # plot all the variations
        style.resample = 'B'
        style.file_output = self.DUMP_PATH + trading_model.FINAL_STRATEGY + ' ' + parameter_type + '.png'
        style.html_file_output = self.DUMP_PATH + trading_model.FINAL_STRATEGY + ' ' + parameter_type + '.html'
        style.scale_factor = trading_model.SCALE_FACTOR
        style.title = trading_model.FINAL_STRATEGY + ' ' + parameter_type

        if plot:
            self.chart.plot(port_list, chart_type='line', style=style)

        # plot all the IR in a bar chart form (can be easier to read!)
        style = Style()
        style.file_output = self.DUMP_PATH + trading_model.FINAL_STRATEGY + ' ' + parameter_type + ' IR.png'
        style.html_file_output = self.DUMP_PATH + trading_model.FINAL_STRATEGY + ' ' + parameter_type + ' IR.html'
        style.scale_factor = trading_model.SCALE_FACTOR
        style.title = trading_model.FINAL_STRATEGY + ' ' + parameter_type
        summary_ir = pandas.DataFrame(index=pretty_portfolio_names, data=ir, columns=['IR'])

        if plot:
            self.chart.plot(summary_ir, chart_type='bar', style=style)

        # plot all the rets
        style.file_output = self.DUMP_PATH + trading_model.FINAL_STRATEGY + ' ' + parameter_type + ' Rets.png'
        style.html_file_output = self.DUMP_PATH + trading_model.FINAL_STRATEGY + ' ' + parameter_type + ' Rets.html'

        summary_rets = pandas.DataFrame(index=pretty_portfolio_names, data=rets, columns=['Rets (%)']) * 100

        if plot:
            self.chart.plot(summary_rets, chart_type='bar', style=style)

        return port_list, summary_ir, summary_rets

    def _load_assets(self, trading_model, br):
        assets = trading_model.load_assets(br=br)

        asset_df = assets[0]
        spot_df = assets[1]
        spot_df2 = assets[2]
        basket_dict = assets[3]

        if len(assets) == 5:  # for future use
            contract_value_df = assets[4]

        contract_value_df = None

        return asset_df, spot_df, spot_df2, basket_dict, contract_value_df

    def _run_strategy(self, trading_model, asset_df, spot_df, spot_df2, br, contract_value_df, pretty_portfolio_name):

        logger = LoggerManager().getLogger(__name__)

        logger.info("Calculating... " + str(pretty_portfolio_name))

        signal_df = trading_model.construct_signal(spot_df, spot_df2, br.tech_params, br, run_in_parallel=False)

        backtest = Backtest()

        backtest.calculate_trading_PnL(br, asset_df, signal_df, contract_value_df, False)
        ret_stats = backtest.portfolio_pnl_ret_stats()
        stats = str(backtest.portfolio_pnl_desc()[0])

        port = backtest.portfolio_cum().resample('B').mean()
        port.columns = [str(pretty_portfolio_name) + ' ' + stats]

        return port, ret_stats

    ###### Parameters and signal generations (need to be customised for every model)
    ###### Plot all the output seperately
    def run_arbitrary_sensitivity_separately(self, trading_model, parameter_list=None,
                                             pretty_portfolio_names=None, strip=None):

        # asset_df, spot_df, spot_df2, basket_dict = strat.fill_assets()
        final_strategy = trading_model.FINAL_STRATEGY

        for i in range(0, len(parameter_list)):
            br = trading_model.fill_backtest_request()

            current_parameter = parameter_list[i]

            # for calculating P&L
            for k in current_parameter.keys():
                setattr(br, k, current_parameter[k])

            trading_model.FINAL_STRATEGY = final_strategy + " " + pretty_portfolio_names[i]

            self.logger.info("Calculating... " + pretty_portfolio_names[i])
            trading_model.br = br
            trading_model.construct_strategy(br=br)

            trading_model.plot_strategy_pnl()
            trading_model.plot_strategy_leverage()
            trading_model.plot_strategy_group_benchmark_pnl(strip=strip)

        # reset the parameters of the strategy
        trading_model.br = trading_model.fill_backtest_request()
        trading_model.FINAL_STRATEGY = final_strategy

    def run_day_of_month_analysis(self, trading_model, resample_freq='B'):
        from finmarketpy.economics.seasonality import Seasonality

        logger = LoggerManager().getLogger(__name__)

        calculations = Calculations()
        seas = Seasonality()
        trading_model.construct_strategy()
        pnl = trading_model.strategy_pnl()

        # Get seasonality by day of the month
        pnl = pnl.resample('B').mean()
        rets = calculations.calculate_returns(pnl).tz_localize(None)

        bus_day = seas.bus_day_of_month_seasonality(rets, add_average=True, resample_freq=resample_freq)

        # Get seasonality by month
        pnl = pnl.resample('BM').mean()
        rets = calculations.calculate_returns(pnl).tz_localize(None)
        month = seas.monthly_seasonality(rets)

        logger.info("About to plot seasonality...")
        style = Style()

        # Plotting spot over day of month/month of year
        style.color = 'Blues'
        style.scale_factor = trading_model.SCALE_FACTOR
        style.file_output = self.DUMP_PATH + trading_model.FINAL_STRATEGY + ' seasonality day of month.png'
        style.html_file_output = self.DUMP_PATH + trading_model.FINAL_STRATEGY + ' seasonality day of month.html'
        style.title = trading_model.FINAL_STRATEGY + ' day of month seasonality'
        style.display_legend = False
        style.color_2_series = [bus_day.columns[-1]]
        style.color_2 = ['red']  # red, pink
        style.linewidth_2 = 4
        style.linewidth_2_series = [bus_day.columns[-1]]
        style.y_axis_2_series = [bus_day.columns[-1]]

        self.chart.plot(bus_day, chart_type='line', style=style)

        style = Style()

        style.scale_factor = trading_model.SCALE_FACTOR
        style.file_output = self.DUMP_PATH + trading_model.FINAL_STRATEGY + ' seasonality month of year.png'
        style.html_file_output = self.DUMP_PATH + trading_model.FINAL_STRATEGY + ' seasonality month of year.html'
        style.title = trading_model.FINAL_STRATEGY + ' month of year seasonality'

        self.chart.plot(month, chart_type='line', style=style)

        return month
