__author__ = 'saeedamen'

from pythalesians.util.loggermanager import LoggerManager
from pythalesians.market.requests.timeseriesrequest import TimeSeriesRequest


class BacktestRequest(TimeSeriesRequest):

    def __init__(self):
        super(TimeSeriesRequest, self).__init__()
        self.logger = LoggerManager().getLogger(__name__)

    @property
    def opt_tc_bp(self):
        return self.__opt_tc_bp

    @opt_tc_bp.setter
    def opt_tc_bp(self, opt_tc_bp):
        self.__opt_tc_bp = opt_tc_bp / (2.0 * 100.0 * 100.0)

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

    @property
    def tenor(self):
        return self.__tenor

    @tenor.setter
    def tenor(self, tenor):
        self.__tenor = tenor

    @property
    def strike(self):
        return self.__strike

    @tenor.setter
    def strike(self, strike):
        self.__strike = strike

    @property
    def delta_threshold(self):
        return self.__delta_threshold

    @delta_threshold.setter
    def delta_threshold(self, delta_threshold):
        self.__delta_threshold = delta_threshold

