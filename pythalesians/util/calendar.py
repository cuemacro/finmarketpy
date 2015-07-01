__author__ = 'saeedamen' # Saeed Amen / saeed@thalesians.com

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
Calendar

Provides calendar based functions for working out options expiries. Note, that in practice, we would often take
into account market holidays.

"""

import pandas
from pandas.tseries.offsets import BDay

import numpy
import datetime
import pandas.tseries.offsets

from pythalesians.timeseries.calcs.timeseriesfilter import TimeSeriesFilter
from pythalesians.timeseries.calcs.timeseriestimezone import TimeSeriesTimezone

from datetime import timedelta
from pandas.tseries.offsets import CustomBusinessDay
from pandas.tseries.offsets import CustomBusinessMonthBegin

class Calendar:

    def get_business_days_tenor(self, tenor):
        if tenor == '1W':
            return 5
        elif tenor == 'ON':
            return 1
        elif tenor == '1M':
            return 20
        elif tenor == '3M':
            return 60
        elif tenor == '6M':
            return 120
        elif tenor == '1Y':
            return 252

    def get_dates_from_tenors(self, start, end, calendar, tenor):
        freq = str(self.get_business_days_tenor(tenor)) + "B"
        return pandas.DataFrame(index=pandas.bdate_range(start, end, freq=freq))

    def get_expiries_from_dates(self, date_time_index, calendar, tenor):
        freq = self.get_business_days_tenor(tenor)

        return pandas.DatetimeIndex(date_time_index + BDay(freq))

    def align_to_NY_cut_in_UTC(self, date_time):

        tstz = TimeSeriesTimezone()
        date_time = tstz.localise_index_as_new_york_time(date_time)
        date_time.index = date_time.index + timedelta(hours=10)

        return tstz.convert_index_aware_to_UTC_time(date_time)

    def floor_date(self, data_frame):
        data_frame.index = data_frame.index.normalize()

        return data_frame

    def create_bus_day(self, start, end):
        return pandas.date_range(start, end, freq='B')

    def get_bus_day_of_month(self, date, cal = 'FX'):
        """ get_bus_day_of_month(date = list of dates, cal = calendar name)

            returns the business day of the month (ie. 3rd Jan, on a Monday,
            would be the 1st business day of the month
        """
        tsf = TimeSeriesFilter()

        try:
            date = date.normalize() # strip times off the dates - for business dates just want dates!
        except: pass

        start = pandas.to_datetime(datetime.datetime(date.year[0], date.month[0], 1))
        end = datetime.datetime.today()#pandas.to_datetime(datetime.datetime(date.year[-1], date.month[-1], date.day[-1]))

        holidays = tsf.get_holidays(start, end, cal)

        bday = CustomBusinessDay(holidays=holidays, weekmask='Mon Tue Wed Thu Fri')

        bus_dates = pandas.date_range(start, end, freq=bday)

        month = bus_dates.month

        work_day_index = numpy.zeros(len(bus_dates))
        work_day_index[0] = 1

        for i in range(1, len(bus_dates)):
            if month[i] == month[i-1]:
                work_day_index[i] = work_day_index[i-1] + 1
            else:
                work_day_index[i] = 1

        bus_day_of_month = work_day_index[bus_dates.searchsorted(date)]

        # bus_day_of_month = numpy.zeros(len(date))
        # for i in range(0, len(date)):
        #     index = bus_dates.searchsorted(date[i])
        #     bus_day_of_month[i] = work_day_index[index]

        #
        # holidays = tsf.get_holidays(start, end, cal)
        #
        # bday = CustomBusinessDay(holidays=holidays, weekmask='Mon Tue Wed Thu Fri')
        # bmth_begin = CustomBusinessMonthBegin(holidays=holidays)

        # tsf = TimeSeriesFilter()
        #
        # # floored_dates = datetime.date(date.year, date.month, date.day[0])
        # start = pandas.to_datetime(datetime.datetime(date.year[0], date.month[0], 1))
        # end = pandas.to_datetime(datetime.datetime(date.year[-1], date.month[-1], date.day[-1]))
        #
        # holidays = tsf.get_holidays(start, end, cal)
        #
        # bday = CustomBusinessDay(holidays=holidays, weekmask='Mon Tue Wed Thu Fri')
        # bmth_begin = CustomBusinessMonthBegin(holidays=holidays)
        #
        # bus_day_dict = {}
        # first_day_of_month = []
        # first_day_of_month.append(start - bmth_begin)
        #
        # i = 0
        #
        # while(first_day_of_month[i-1] <= end):
        #     first_day_of_month.append(first_day_of_month[i-1] + bmth_begin)
        #     i = i + 1
        #
        # # create a dictionary of dates and business day of the month
        # # fill every day with NaN to begin with (to be overwritten)
        # # will fail if our data contains weekends
        # last_date = first_day_of_month[0]
        #
        # while(last_date <= end):
        #     bus_day_dict[last_date.year * 10000 + last_date.month * 100 + last_date.day] = numpy.NaN
        #     last_date = last_date + pandas.DateOffset(1)
        #
        # # for the business days
        # # create a dictionary of dates and business day of the month
        # for first in first_day_of_month:
        #     curr_month = first.month
        #     last_date = first
        #
        #     bus_day_offset = 1
        #
        #     while(curr_month == last_date.month):
        #         bus_day_dict[last_date.year * 10000 + last_date.month * 100 + last_date.day] = bus_day_offset
        #         last_date = last_date + bday
        #         bus_day_offset = bus_day_offset + 1
        #
        # date_key = date.year * 10000 + date.month * 100 + date.day
        #
        # date_key_unique = numpy.unicode(date_key)
        #
        # # if the day doesn't appear in the calendar assign -1
        # #bus_day_of_month = map(lambda x: bus_day_dict[x], date_key)
        # find_bus_ordinal = numpy.vectorize(lambda x: bus_day_dict[x])
        # bus_day_of_month = find_bus_ordinal(date_key_unique)
        # #[lambda x: bus_day_dict[x] for x in date]

        return bus_day_of_month

