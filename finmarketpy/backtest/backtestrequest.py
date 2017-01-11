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

    @property
    def signal_name(self):
        return self.__signal_name

    @signal_name.setter
    def signal_name(self, signal_name):
        self.__signal_name = signal_name

    @property
    def tech_params(self):
        return self.__tech_params

    @tech_params.setter
    def tech_params(self, tech_params):
        self.__tech_params = tech_params

    @property
    def spot_tc_bp(self):
        return self.__spot_tc_bp

    @spot_tc_bp.setter
    def spot_tc_bp(self, spot_tc_bp):
        self.__spot_tc_bp = spot_tc_bp / (2.0 * 100.0 * 100.0)

    @property
    def asset(self):
        return self.__asset

    @asset.setter
    def asset(self, asset):
        valid_asset = ['fx', 'multi-asset']

        if not asset in valid_asset:
            self.logger.warning(asset & " is not a defined asset.")

        self.__asset = asset

    @property
    def instrument(self):
        return self.__instrument

    @instrument.setter
    def instrument(self, instrument):
        valid_instrument = ['spot', 'futures', 'options']

        if not instrument in valid_instrument:
            self.logger.warning(instrument & " is not a defined trading instrument.")

        self.__instrument = instrument

