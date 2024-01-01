__author__ = "saeedamen"  # Saeed Amen

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


import datetime

from findatapy.market import Market, MarketDataGenerator, MarketDataRequest
from finmarketpy.backtest import TradingModel, BacktestRequest
from finmarketpy.economics import TechIndicator

from chartpy import Style

from findatapy.util.dataconstants import DataConstants

# You will likely need to change this!
quandl_api_key = DataConstants().quandl_api_key

class TradingModelFXTrend_Example(TradingModel):
    """Shows how to create a simple FX CTA style strategy, using the TradingModel abstract class (backtest_examples.py
    is a lower level way of doing this).
    """

    def __init__(self):
        super(TradingModel, self).__init__()

        ##### FILL IN WITH YOUR OWN PARAMETERS FOR display, dumping, TSF etc.
        self.market = Market(market_data_generator=MarketDataGenerator())
        self.DUMP_PATH = ""
        self.FINAL_STRATEGY = "FX trend"
        self.SCALE_FACTOR = 1
        self.DEFAULT_PLOT_ENGINE = "matplotlib"
        # self.CHART_STYLE = Style(plotly_plot_mode="offline_jupyter")

        self.br = self.load_parameters()
        return

    ###### Parameters and signal generations (need to be customised for every model)
    def load_parameters(self, br=None):

        if br is not None: return br

        ##### FILL IN WITH YOUR OWN BACKTESTING PARAMETERS
        br = BacktestRequest()

        # get all asset data
        br.start_date = "04 Jan 1989"
        br.finish_date = datetime.datetime.utcnow().date()
        br.spot_tc_bp = 0.5
        br.ann_factor = 252

        br.plot_start = "01 Apr 2015"
        br.calc_stats = True
        br.write_csv = False
        br.plot_interim = True
        br.include_benchmark = True

        # Have vol target for each signal
        br.signal_vol_adjust = True
        br.signal_vol_target = 0.1
        br.signal_vol_max_leverage = 5
        br.signal_vol_periods = 20
        br.signal_vol_obs_in_year = 252
        br.signal_vol_rebalance_freq = "BM"
        br.signal_vol_resample_freq = None

        # Have vol target for portfolio
        br.portfolio_vol_adjust = True
        br.portfolio_vol_target = 0.1
        br.portfolio_vol_max_leverage = 5
        br.portfolio_vol_periods = 20
        br.portfolio_vol_obs_in_year = 252
        br.portfolio_vol_rebalance_freq = "BM"
        br.portfolio_vol_resample_freq = None

        # Tech params
        br.tech_params.sma_period = 200

        # To make additive indices
        # br.cum_index = "add"

        return br

    def load_assets(self, br = None):
        ##### FILL IN WITH YOUR ASSET DATA
        from findatapy.util.loggermanager import  LoggerManager
        logger = LoggerManager().getLogger(__name__)

        # For FX basket
        full_bkt    = ["EURUSD", "USDJPY", "GBPUSD", "AUDUSD", "USDCAD",
                       "NZDUSD", "USDCHF", "USDNOK", "USDSEK"]

        basket_dict = {}

        for i in range(0, len(full_bkt)):
            basket_dict[full_bkt[i]] = [full_bkt[i]]

        basket_dict["FX trend"] = full_bkt

        br = self.load_parameters(br = br)

        logger.info("Loading asset data...")

        vendor_tickers = ["FRED/DEXUSEU", "FRED/DEXJPUS",
                          "FRED/DEXUSUK", "FRED/DEXUSAL",
                          "FRED/DEXCAUS",
                          "FRED/DEXUSNZ", "FRED/DEXSZUS",
                          "FRED/DEXNOUS", "FRED/DEXSDUS"]

        market_data_request = MarketDataRequest(
                    start_date=br.start_date,                     # start date
                    finish_date=br.finish_date,                   # finish date
                    freq="daily",                                 # daily data
                    data_source="quandl",                         # use Quandl as data source
                    tickers=full_bkt,                             # ticker (Cuemacro)
                    fields=["close"],                             # which fields to download
                    vendor_tickers=vendor_tickers,                # ticker (Quandl)
                    vendor_fields=["close"],                      # which Quandl fields to download
                    cache_algo="cache_algo_return",               # how to return data
                    quandl_api_key=quandl_api_key)

        asset_df = self.market.fetch_market(market_data_request)

        # If web connection fails read from CSV
        if asset_df is None:
            import pandas

            asset_df = pandas.read_csv(
                "fxcta.csv", index_col=0, parse_dates=["Date"],
                date_parser=lambda x: pandas.datetime.strptime(x, "%Y-%m-%d"))

        # Signalling variables
        spot_df = asset_df
        spot_df2 = None

        # asset_df

        return asset_df, spot_df, spot_df2, basket_dict

    def construct_signal(self, spot_df, spot_df2, tech_params, br, run_in_parallel=False):

        ##### FILL IN WITH YOUR OWN SIGNALS

        # Use technical indicator to create signals
        # (we could obviously create whatever function we wanted for generating the signal dataframe)
        tech_ind = TechIndicator()
        tech_ind.create_tech_ind(spot_df, "SMA", tech_params);
        signal_df = tech_ind.get_signal()

        return signal_df

    def construct_strategy_benchmark(self):

        ###### FILL IN WITH YOUR OWN BENCHMARK

        tsr_indices = MarketDataRequest(
            start_date=self.br.start_date,                # start date
            finish_date=self.br.finish_date,              # finish date
            freq="daily",                                 # daily frequen
            data_source="quandl",                         # use Bloomberg as data source
            tickers=["EURUSD"],                           # tickers to download
            vendor_tickers=["FRED/DEXUSEU"],
            fields=["close"],                             # which fields to download
            vendor_fields =["close"],
            cache_algo="cache_algo_return",               # how to return data
            quandl_api_key=quandl_api_key)

        df = self.market.fetch_market(tsr_indices)

        df.columns = [x.split(".")[0] for x in df.columns]

        return df

if __name__ == "__main__":

# Just change "False" to "True" to run any of the below examples

    # Create a FX trend strategy then chart the returns, leverage over time
    if True:
        model = TradingModelFXTrend_Example()

        model.construct_strategy()

        model.plot_strategy_pnl()                        # plot the final strategy
        model.plot_strategy_leverage()                   # plot the leverage of the portfolio
        model.plot_strategy_group_pnl_trades()           # plot the individual trade P&Ls
        model.plot_strategy_group_benchmark_pnl()        # plot all the cumulative P&Ls of each component
        model.plot_strategy_group_benchmark_pnl_ir()     # plot all the IR of individual components
        model.plot_strategy_group_leverage()             # plot all the individual leverages

        from finmarketpy.backtest import TradeAnalysis

        ta = TradeAnalysis()

        # Create statistics for the model returns using both finmarketpy and pyfolio
        ta.run_strategy_returns_stats(model, engine="finmarketpy")
        # ta.run_strategy_returns_stats(model, engine="pyfolio")

        # model.plot_strategy_group_benchmark_annualised_pnl()

    # Create a FX CTA strategy, then examine how P&L changes with different vol targeting
    # and later transaction costs
    if True:
        strategy = TradingModelFXTrend_Example()

        from finmarketpy.backtest import TradeAnalysis

        ta = TradeAnalysis()
        ta.run_strategy_returns_stats(model, engine="finmarketpy")

        # Which backtesting parameters to change
        # names of the portfolio
        # broad type of parameter name
        parameter_list = [
            {"portfolio_vol_adjust": True, "signal_vol_adjust" : True},
            {"portfolio_vol_adjust": False, "signal_vol_adjust" : False}]

        pretty_portfolio_names = \
            ["Vol target",
             "No vol target"]

        parameter_type = "vol target"

        ta.run_arbitrary_sensitivity(strategy,
                                     parameter_list=parameter_list,
                                     pretty_portfolio_names=pretty_portfolio_names,
                                     parameter_type=parameter_type)

        # Now examine sensitivity to different transaction costs
        tc = [0, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2.0]
        ta.run_tc_shock(strategy, tc=tc)

        # How does P&L change on day of month
        ta.run_day_of_month_analysis(strategy)

    # Create a FX CTA strategy then use TradeAnalysis (via pyfolio) to analyse returns
    if False:
        from finmarketpy.backtest import TradeAnalysis
        model = TradingModelFXTrend_Example()
        model.construct_strategy()

        tradeanalysis = TradeAnalysis()
        tradeanalysis.run_strategy_returns_stats(strategy)
