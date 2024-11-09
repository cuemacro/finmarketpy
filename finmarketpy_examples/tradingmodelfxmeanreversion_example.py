from findatapy.market import Market, MarketDataGenerator, MarketDataRequest
from finmarketpy.backtest import TradingModel, BacktestRequest
from finmarketpy.economics import TechIndicator
from findatapy.util.dataconstants import DataConstants
import datetime

fred_api_key = DataConstants().fred_api_key

class TradingModelFXMeanReversion(TradingModel):
    def __init__(self):
        super(TradingModel, self).__init__()
        
        self.market = Market(market_data_generator=MarketDataGenerator())
        self.DUMP_PATH = ""
        self.FINAL_STRATEGY = "FX mean reversion"
        self.SCALE_FACTOR = 1
        self.DEFAULT_PLOT_ENGINE = "matplotlib"
        
        self.br = self.load_parameters()
    
    def load_parameters(self, br=None):
        if br is not None: 
            return br
        
        br = BacktestRequest()
        
        # Trading parameters
        br.start_date = "04 Jan 2010"  # More recent start date for mean reversion
        br.finish_date = datetime.datetime.utcnow().date()
        br.spot_tc_bp = 0.5
        br.ann_factor = 252

        # Risk parameters
        br.signal_vol_target = 0.05  # Lower vol target for mean reversion
        br.portfolio_vol_target = 0.05
        br.signal_vol_max_leverage = 3  # Lower leverage
        br.portfolio_vol_max_leverage = 3
        
        # Technical parameters
        br.tech_params.rsi_period = 14  # RSI lookback
        br.tech_params.rsi_overbought = 70  # RSI thresholds
        br.tech_params.rsi_oversold = 30
        
        return br

    def load_assets(self, br=None):
        # Major pairs only for mean reversion
        pairs = ["EURUSD", "USDJPY", "GBPUSD", "AUDUSD"]
        vendor_tickers = ["DEXUSEU", "DEXJPUS", "DEXUSUK", "DEXUSAL"]
        
        basket_dict = {}
        for pair in pairs:
            basket_dict[pair] = [pair]
        basket_dict["FX mean reversion"] = pairs
        
        market_data_request = MarketDataRequest(
            start_date=br.start_date,
            finish_date=br.finish_date,
            freq="daily",
            data_source="alfred",
            tickers=pairs,
            fields=["close"],
            vendor_tickers=vendor_tickers,
            vendor_fields=["close"],
            cache_algo="cache_algo_return",
            fred_api_key=DataConstants().fred_api_key)
            
        asset_df = self.market.fetch_market(market_data_request)
        return asset_df, asset_df, None, basket_dict

    def construct_signal(self, spot_df, spot_df2, tech_params, br, run_in_parallel=False):
        tech_ind = TechIndicator()
        
        # Calculate RSI
        tech_ind.create_tech_ind(spot_df, "RSI", tech_params)
        rsi = tech_ind.get_signal()
        
        # Generate mean reversion signals
        signal_df = rsi.copy()
        signal_df[rsi > tech_params.rsi_overbought] = -1  # Overbought = Short
        signal_df[rsi < tech_params.rsi_oversold] = 1     # Oversold = Long
        signal_df[(rsi >= tech_params.rsi_oversold) & 
                 (rsi <= tech_params.rsi_overbought)] = 0  # Neutral zone = No position
        
        return signal_df

if __name__ == "__main__":
    model = TradingModelFXMeanReversion()
    model.construct_strategy()
    
    # Analysis
    model.plot_strategy_pnl()
    model.plot_strategy_leverage()
    
    from finmarketpy.backtest import TradeAnalysis
    ta = TradeAnalysis()
    ta.run_strategy_returns_stats(model, engine="finmarketpy")