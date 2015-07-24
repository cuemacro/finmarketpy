__author__ = 'saeedamen'

import pandas
import numpy

from pythalesians.util.configmanager import ConfigManager
from pythalesians.util.loggermanager import LoggerManager
from pythalesians.timeseries.calcs.timeseriescalcs import TimeSeriesCalcs
from pythalesians.timeseries.calcs.timeseriesfilter import TimeSeriesFilter
from pythalesians.util.commonman import CommonMan

class Seasonality:

    def __init__(self):
        self.config = ConfigManager()
        self.logger = LoggerManager().getLogger(__name__)
        return

    def time_of_day_seasonality(self, data_frame, years = False):

        tsc = TimeSeriesCalcs()

        if years is False:
            return tsc.average_by_hour_min_of_day_pretty_output(data_frame)

        set_year = set(data_frame.index.year)
        year = sorted(list(set_year))

        intraday_seasonality = None

        commonman = CommonMan()

        for i in year:
            temp_seasonality = tsc.average_by_hour_min_of_day_pretty_output(data_frame[data_frame.index.year == i])

            temp_seasonality.columns = commonman.postfix_list(temp_seasonality.columns.values, " " + str(i))

            if intraday_seasonality is None:
                intraday_seasonality = temp_seasonality
            else:
                intraday_seasonality = intraday_seasonality.join(temp_seasonality)

        return intraday_seasonality

    def bus_day_of_month_seasonality(self, data_frame,
                                 month_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], cum = True,
                                     cal = "FX", partition_by_month = True):

        tsc = TimeSeriesCalcs()
        tsf = TimeSeriesFilter()

        data_frame.index = pandas.to_datetime(data_frame.index)
        data_frame = tsf.filter_time_series_by_holidays(data_frame, cal)

        monthly_seasonality = tsc.average_by_month_day_by_bus_day(data_frame, cal)
        monthly_seasonality = monthly_seasonality.loc[month_list]

        if partition_by_month:
            monthly_seasonality = monthly_seasonality.unstack(level=0)

        if cum is True:
            monthly_seasonality.ix[0] = numpy.zeros(len(monthly_seasonality.columns))

            if partition_by_month:
                monthly_seasonality.index = monthly_seasonality.index + 1   # shifting index
                monthly_seasonality = monthly_seasonality.sort()            # sorting by index

            monthly_seasonality = tsc.create_mult_index(monthly_seasonality)

        return monthly_seasonality

if __name__ == '__main__':
    # see seasonality_examples
    pass
