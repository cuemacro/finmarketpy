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
EventStudy

Provides functions for doing event studies on price action on an intraday basis and daily basis.

"""

from datetime import timedelta
import math

from pandas.tseries.offsets import CustomBusinessDay
import pandas
import numpy

from pythalesians.util.loggermanager import LoggerManager
from pythalesians.timeseries.calcs.timeseriesfilter import TimeSeriesFilter
from pythalesians.timeseries.calcs.timeseriescalcs import TimeSeriesCalcs
from pythalesians.timeseries.calcs.timeseriestimezone import TimeSeriesTimezone
from pythalesians.util.calendar import Calendar

class EventStudy:

    def __init__(self):
        self.logger = LoggerManager().getLogger(__name__)
        return

    def get_economic_event_ret_over_custom_event_day(self, data_frame_in, event_dates, name, event, start, end, lagged = False,
                                              NYC_cutoff = 10):

        time_series_filter = TimeSeriesFilter()
        event_dates = time_series_filter.filter_time_series_by_date(start, end, event_dates)

        data_frame = data_frame_in.copy(deep=True) # because we change the dates!

        time_series_tz = TimeSeriesTimezone()
        calendar = Calendar()

        bday = CustomBusinessDay(weekmask='Mon Tue Wed Thu Fri')

        event_dates_nyc = time_series_tz.convert_index_from_UTC_to_new_york_time(event_dates)
        average_hour_nyc = numpy.average(event_dates_nyc.index.hour)

        event_dates = calendar.floor_date(event_dates)

        # realised is traditionally on later day eg. 3rd Jan realised ON is 2nd-3rd Jan realised
        # so if Fed meeting is on 2nd Jan later, then we need realised labelled on 3rd (so minus a day)
        # implied expires on next day eg. 3rd Jan implied ON is 3rd-4th Jan implied

        # TODO smarter way of adjusting dates, as sometimes events can be before/after 10am NY cut
        if (lagged and average_hour_nyc >= NYC_cutoff):
            data_frame.index = data_frame.index - bday
        elif (not lagged and average_hour_nyc < NYC_cutoff): # ie. implied
            data_frame.index = data_frame.index + bday

        # set as New York time and select only those ON vols at the 10am NY cut just before the event
        data_frame_events = data_frame.ix[event_dates.index]
        data_frame_events.columns = data_frame.columns.values + '-' + name + ' ' + event

        return data_frame_events

    def get_intraday_moves_over_custom_event(self, data_frame_rets, ef_time_frame, vol=False,
                                             minute_start = 5, mins = 3 * 60, min_offset = 0 , create_index = False,
                                             resample = False, freq = 'minutes'):

        tsf = TimeSeriesFilter()
        ef_time_frame = tsf.filter_time_series_by_date(data_frame_rets.index[0], data_frame_rets.index[-1], ef_time_frame)
        ef_time = ef_time_frame.index

        if freq == 'minutes':
            ef_time_start = ef_time - timedelta(minutes = minute_start)
            ef_time_end = ef_time + timedelta(minutes = mins)
            ann_factor = 252 * 1440
        elif freq == 'days':
            ef_time = ef_time_frame.index.normalize()
            ef_time_start = ef_time - timedelta(days = minute_start)
            ef_time_end = ef_time + timedelta(days = mins)
            ann_factor = 252

        ords = range(-minute_start + min_offset, mins + min_offset)

        # all data needs to be equally spaced
        if resample:
            tsf = TimeSeriesFilter()

            # make sure time series is properly sampled at 1 min intervals
            data_frame_rets = data_frame_rets.resample('1min')
            data_frame_rets = data_frame_rets.fillna(value = 0)
            data_frame_rets = tsf.remove_out_FX_out_of_hours(data_frame_rets)

        data_frame_rets['Ind'] = numpy.nan

        start_index = data_frame_rets.index.searchsorted(ef_time_start)
        finish_index = data_frame_rets.index.searchsorted(ef_time_end)

        # not all observation windows will be same length (eg. last one?)

        # fill the indices which represent minutes
        # TODO vectorise this!
        for i in range(0, len(ef_time_frame.index)):
            try:
                data_frame_rets.ix[start_index[i]:finish_index[i], 'Ind'] = ords
            except:
                data_frame_rets.ix[start_index[i]:finish_index[i], 'Ind'] = ords[0:(finish_index[i] - start_index[i])]

        # set the release dates
        data_frame_rets.ix[start_index,'Rel'] = ef_time                                         # set entry points
        data_frame_rets.ix[finish_index + 1,'Rel'] = numpy.zeros(len(start_index))              # set exit points
        data_frame_rets['Rel'] = data_frame_rets['Rel'].fillna(method = 'pad')                  # fill down signals

        data_frame_rets = data_frame_rets[pandas.notnull(data_frame_rets['Ind'])]               # get rid of other

        data_frame = data_frame_rets.pivot(index='Ind',
                                           columns='Rel', values=data_frame_rets.columns[0])

        data_frame.index.names = [None]

        if create_index:
            tsc = TimeSeriesCalcs()
            data_frame.ix[-minute_start + min_offset,:] = numpy.nan
            data_frame = tsc.create_mult_index(data_frame)
        else:
            if vol is True:
                # annualise (if vol)
                data_frame = pandas.rolling_std(data_frame, window=5) * math.sqrt(ann_factor)
            else:
                data_frame = data_frame.cumsum()

        return data_frame

    def get_surprise_against_intraday_moves_over_custom_event(
            self, data_frame_cross_orig, ef_time_frame, cross, event_fx, event_name, start, end,
            offset_list = [1, 5, 30, 60], add_surprise = False, surprise_field = 'survey-average', freq = 'minutes'):

        ticker = event_fx + "-" + event_name + ".release-date-time-full"

        data_frame_agg = None
        data_frame_cross_orig = data_frame_cross_orig.resample('T')         # resample to minute freq - in case there are missing values

        ef_time_start = ef_time_frame[ticker] - timedelta(minutes=1)        # start time
        indices_start = data_frame_cross_orig.index.isin(ef_time_start)

        for offset in offset_list:
            data_frame_cross = data_frame_cross_orig

            ef_time = ef_time_frame[ticker] + timedelta(minutes=offset - 1)     # end time

            # calculate returns over the x min event
            indices = data_frame_cross.index.isin(ef_time)
            col_dates = data_frame_cross.index[indices]

            col_rets = (data_frame_cross.iloc[indices].values) \
                       / (data_frame_cross.iloc[indices_start].values) - 1

            mkt_moves = pandas.DataFrame(index=col_dates)
            mkt_moves[cross + " " + str(offset) + "m move"] = col_rets
            mkt_moves.index.name = ticker
            mkt_moves.index = col_dates - timedelta(minutes=offset - 1)

            data_frame = ef_time_frame.join(mkt_moves, on=ticker, how="inner")
            temp_index = data_frame[ticker]

            spot_moves_list = []

            if data_frame_agg is None:
                data_frame_agg = data_frame
            else:
                label = cross + " " + str(offset) + "m move"
                spot_moves_list.append(label)
                data_frame = data_frame[label]
                data_frame.index = temp_index
                data_frame_agg = data_frame_agg.join(data_frame, on=ticker, how="inner")

        if add_surprise == True:
            data_frame_agg[event_fx + "-" + event_name + ".surprise"] = data_frame_agg[event_fx + "-" + event_name + ".actual-release"] \
                               - data_frame_agg[event_fx + "-" + event_name + "." + surprise_field]

        return data_frame_agg