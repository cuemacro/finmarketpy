__author__ = 'saeedamen'

from findatapy.market import MarketDataRequest

from finmarketpy.economics import TechParams
from findatapy.util.loggermanager import LoggerManager

class BacktestRequest(MarketDataRequest):
    """Contains parameters necessary to define a backtest, including start date, finish date, transaction cost, etc

    Used by TradingModel and Backtest to construct backtested returns for trading strategies

    """

    def __init__(self):
        super(MarketDataRequest, self).__init__()
        self.logger = LoggerManager().getLogger(__name__)

        self.__signal_name = None
        self.__tech_params = TechParams()

        # default parameters for portfolio level vol adjustment
        # TODO add all parameters for vol adjustment
        self.__portfolio_vol_adjust = False
        self.__portfolio_vol_period_shift = 0
        self.__portfolio_vol_resample_freq = None
        self.__portfolio_vol_resample_type = 'mean'

        # default parameters for signal level vol adjustment
        self.__signal_vol_adjust = False
        self.__signal_vol_period_shift = 0
        self.__signal_vol_resample_freq = None
        self.__signal_vol_resample_type = 'mean'

        # portfolio notional size
        self.__portfolio_notional_size = None
        self.__portfolio_combination = None
        
        # parameters for maximum position limits (expressed as whole portfolio)
        self.__max_net_exposure = None
        self.__max_abs_exposure = None

        # take profit and stop loss parameters
        self.__take_profit = None
        self.__stop_loss = None

    ##### properties for portfolio level volatility adjustment
    @property
    def portfolio_vol_adjust(self): return self.__portfolio_vol_adjust

    @portfolio_vol_adjust.setter
    def portfolio_vol_adjust(self, portfolio_vol_adjust): self.__portfolio_vol_adjust = portfolio_vol_adjust
    
    @property
    def portfolio_vol_resample_type(self): return self.__portfolio_vol_resample_type

    @portfolio_vol_resample_type.setter
    def portfolio_vol_resample_type(self, portfolio_vol_resample_type): self.__portfolio_vol_resample_type = portfolio_vol_resample_type

    @property
    def portfolio_vol_resample_freq(self): return self.__portfolio_vol_resample_freq

    @portfolio_vol_resample_freq.setter
    def portfolio_vol_resample_freq(self, portfolio_vol_resample_freq): self.__portfolio_vol_resample_freq = portfolio_vol_resample_freq

    @property
    def portfolio_vol_period_shift(self): return self.__portfolio_vol_period_shift

    @portfolio_vol_period_shift.setter
    def portfolio_vol_period_shift(self, portfolio_vol_period_shift): self.__portfolio_vol_period_shift = portfolio_vol_period_shift

    ##### properties for signal level vol adjustment
    @property
    def signal_vol_adjust(self): return self.__signal_vol_adjust

    @signal_vol_adjust.setter
    def signal_vol_adjust(self, signal_vol_adjust): self.__signal_vol_adjust = signal_vol_adjust
    
    @property
    def signal_vol_resample_type(self): return self.__signal_vol_resample_type

    @signal_vol_resample_type.setter
    def signal_vol_resample_type(self, signal_vol_resample_type): self.__signal_vol_resample_type = signal_vol_resample_type

    @property
    def signal_vol_resample_freq(self): return self.__signal_vol_resample_freq

    @signal_vol_resample_freq.setter
    def signal_vol_resample_freq(self, signal_vol_resample_freq): self.__signal_vol_resample_freq = signal_vol_resample_freq

    @property
    def signal_vol_period_shift(self): return self.__signal_vol_period_shift

    @signal_vol_period_shift.setter
    def signal_vol_period_shift(self, signal_vol_period_shift): self.__signal_vol_period_shift = signal_vol_period_shift
    
    ##### portfolio notional size
    @property
    def portfolio_notional_size(self): return self.__portfolio_notional_size

    @portfolio_notional_size.setter
    def portfolio_notional_size(self, portfolio_notional_size): self.__portfolio_notional_size = portfolio_notional_size

    ##### portfolio weights (sum, mean or dictionary of weights)
    @property
    def portfolio_combination(self): return self.__portfolio_combination

    @portfolio_combination.setter
    def portfolio_combination(self, portfolio_combination): self.__portfolio_combination = portfolio_combination
    
    ##### properties for maximum position constraints
    @property
    def max_net_exposure(self): return self.__max_net_exposure

    @max_net_exposure.setter
    def max_net_exposure(self, max_net_exposure): self.__max_net_exposure = max_net_exposure
    
    @property
    def max_abs_exposure(self): return self.__max_abs_exposure

    @max_abs_exposure.setter
    def max_abs_exposure(self, max_abs_exposure): self.__max_abs_exposure = max_abs_exposure
    
    ##### stop loss and take profit
    @property
    def stop_loss(self): return self.__stop_loss

    @stop_loss.setter
    def stop_loss(self, stop_loss): self.__stop_loss = stop_loss
    
    @property
    def take_profit(self): return self.__take_profit

    @take_profit.setter
    def take_profit(self, take_profit): self.__take_profit = take_profit

    ##### tech indicators and spot bp tc
    @property
    def tech_params(self): return self.__tech_params

    @tech_params.setter
    def tech_params(self, tech_params): self.__tech_params = tech_params

    @property
    def spot_tc_bp(self): return self.__spot_tc_bp

    @spot_tc_bp.setter
    def spot_tc_bp(self, spot_tc_bp): self.__spot_tc_bp = spot_tc_bp / (2.0 * 100.0 * 100.0)

    #### FOR FUTURE USE ###

    @property
    def signal_name(self): return self.__signal_name

    @signal_name.setter
    def signal_name(self, signal_name): self.__signal_name = signal_name

    @property
    def asset(self): return self.__asset

    @asset.setter
    def asset(self, asset):
        valid_asset = ['fx', 'multi-asset']

        if not asset in valid_asset: self.logger.warning(asset & " is not a defined asset.")

        self.__asset = asset

    @property
    def instrument(self): return self.__instrument

    @instrument.setter
    def instrument(self, instrument):
        valid_instrument = ['spot', 'futures', 'options']

        if not instrument in valid_instrument: self.logger.warning(instrument & " is not a defined trading instrument.")

        self.__instrument = instrument

