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
TimeSeriesTimezone

Various functions wrapping onto pandas and pytz for quickly converting timezones for dataframes.

"""

import numpy
import pytz
import pandas.tseries.offsets

class TimeSeriesTimezone:

    def convert_index_from_UTC_to_new_york_time(self, data_frame):
        new_york = pytz.timezone('America/New_York')

        try:
            data_frame = data_frame.tz_localize(pytz.utc)
        except:
            pass

        data_frame = data_frame.tz_convert(new_york)

        return data_frame

    def convert_index_from_UTC_to_london_time(self, data_frame):
        london = pytz.timezone('Europe/London')

        try:
            data_frame = data_frame.tz_localize(pytz.utc)
        except:
            pass

        data_frame = data_frame.tz_convert(london)

        return data_frame

    def convert_index_time_zone(self, data_frame, from_tz, to_tz):
        data_frame = data_frame.tz_localize(pytz.timezone(from_tz))\
            .tz_convert(pytz.timezone(to_tz))

        return data_frame

    def convert_index_from_UTC_to_alt(self, data_frame, time_zone):
        alt = pytz.timezone(time_zone)
        data_frame = data_frame.tz_localize(pytz.utc).tz_convert(alt)

        return data_frame

    def convert_index_aware_to_UTC_time(self, data_frame):
        utc = pytz.timezone('UTC')
        data_frame = data_frame.tz_convert(utc)

        return data_frame

    def convert_index_aware_to_new_york_time(self, data_frame):
        new_york = pytz.timezone('America/New_York')
        data_frame = data_frame.tz_convert(new_york)

        return data_frame

    def convert_index_aware_to_london_time(self, data_frame):
        london = pytz.timezone('Europe/London')
        data_frame = data_frame.tz_convert(london)

        return data_frame

    def convert_index_aware_to_alt(self, data_frame, time_zone):
        alt = pytz.timezone(time_zone)
        data_frame = data_frame.tz_convert(alt)

        return data_frame

    def localise_index_as_UTC(self, data_frame):
        data_frame = data_frame.tz_localize(pytz.utc)

        return data_frame

    def localise_index_as_new_york_time(self, data_frame):
        new_york = pytz.timezone('America/New_York')
        data_frame = data_frame.tz_localize(new_york)

        return data_frame

    def set_as_no_timezone(self, data_frame):
        data_frame.index.tz = None
        return data_frame

    def tz_UTC_to_naive(self, data_frame):
        """
        tz_UTC_to_naive - Converts a tz-aware DatetimeIndex into a tz-naive DatetimeIndex,
        effectively baking the timezone into the internal representation.

        Parameters
        ----------
        datetime_index : pandas.DatetimeIndex, tz-aware

        Returns
        -------
        pandas.DatetimeIndex, tz-naive
        """

        # data_frame = tsc.convert_index_aware_to_UTC_time(data_frame)

        datetime_index = data_frame.index

        # Calculate timezone offset relative to UTC
        timestamp = datetime_index[0]

        tz_offset = (timestamp.replace(tzinfo=None) -
                     timestamp.tz_convert('UTC').replace(tzinfo=None))

        tz_offset_td64 = numpy.timedelta64(tz_offset)

        # Now convert to naive DatetimeIndex
        data_frame.index = pandas.DatetimeIndex(datetime_index.values + tz_offset_td64)

        return -1 #data_frame #(doesn't work)

    def tz_strip(self, data_frame):
        """
        tz_strip - Converts a tz-aware DatetimeIndex into a tz-naive DatetimeIndex,
        effectively baking the timezone into the internal representation.

        Parameters
        ----------
        datetime_index : pandas.DatetimeIndex, tz-aware

        Returns
        -------
        pandas.DatetimeIndex, tz-naive
        """

        # data_frame = tsc.convert_index_aware_to_UTC_time(data_frame)

        datetime_index = data_frame.index

        # Now convert to naive DatetimeIndex
        data_frame.index = pandas.DatetimeIndex(datetime_index.values)

        return None #(TODO fix as doesn't work)


