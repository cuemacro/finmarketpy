__author__ = 'saeedamen'

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

LightEventsFactory

Provides methods to fetch data on economic data events and to perform basic event studies for market data around
these events. Note, requires a file of input of the following (transposed as columns!) - we give an example for
NFP released on 7 Feb 2003 (note, that release-date-time-full, need not be fully aligned by row).

USD-US Employees on Nonfarm Payrolls Total MoM Net Change SA.Date	                31/01/2003 00:00
USD-US Employees on Nonfarm Payrolls Total MoM Net Change SA.close	                xyz
USD-US Employees on Nonfarm Payrolls Total MoM Net Change SA.actual-release	        143
USD-US Employees on Nonfarm Payrolls Total MoM Net Change SA.survey-median	        xyz
USD-US Employees on Nonfarm Payrolls Total MoM Net Change SA.survey-average	        xyz
USD-US Employees on Nonfarm Payrolls Total MoM Net Change SA.survey-high	        xyz
USD-US Employees on Nonfarm Payrolls Total MoM Net Change SA.survey-low	            xyz
USD-US Employees on Nonfarm Payrolls Total MoM Net Change SA.survey-high.1	        xyz
USD-US Employees on Nonfarm Payrolls Total MoM Net Change SA.number-observations	xyz
USD-US Employees on Nonfarm Payrolls Total MoM Net Change SA.first-revision	        185
USD-US Employees on Nonfarm Payrolls Total MoM Net Change SA.first-revision-date	20030307
USD-US Employees on Nonfarm Payrolls Total MoM Net Change SA.release-dt	            20030207
USD-US Employees on Nonfarm Payrolls Total MoM Net Change SA.release-date-time-full	08/01/1999 13:30

"""

from datetime import timedelta
import datetime

import pandas
import numpy

from pythalesians.util.configmanager import ConfigManager
from pythalesians.util.loggermanager import LoggerManager
from pythalesians.market.loaders.timeseriesio import TimeSeriesIO
from pythalesians.timeseries.calcs.timeseriesfilter import TimeSeriesFilter
from pythalesians.economics.events.eventstudy import EventStudy

try:
    from numbapro import autojit
except: pass

class LightEventsFactory(EventStudy):

    _econ_data_frame = None

    # where your HDF5 file is stored with economic data MUST CHANGE!
    _hdf5_file_econ_file = "somefilnename.h5"

    ### manual offset for certain events where Bloomberg displays the wrong date (usually because of time differences)
    _offset_events = {'AUD-Australia Labor Force Employment Change SA.release-dt' : 1}

    def __init__(self):
        super(EventStudy, self).__init__()

        self.config = ConfigManager()
        self.logger = LoggerManager().getLogger(__name__)
        self.time_series_filter = TimeSeriesFilter()
        self.time_series_io = TimeSeriesIO()

        if (LightEventsFactory._econ_data_frame is None):
            self.load_economic_events()
        return

    def load_economic_events(self):
        LightEventsFactory._econ_data_frame = self.time_series_io.read_time_series_cache_from_disk(self._hdf5_file_econ_file)

    def harvest_category(self, category_name):
        cat = self.config.get_categories_from_tickers_selective_filter(category_name)

        for k in cat:
            time_series_request = self.time_series_factory.populate_time_series_request(k)
            data_frame = self.time_series_factory.harvest_time_series(time_series_request)

            # TODO allow merge of multiple sources

        return data_frame

    def get_economic_events(self):
        return LightEventsFactory._econ_data_frame

    def dump_economic_events_csv(self, path):
        LightEventsFactory._econ_data_frame.to_csv(path)

    def get_economic_event_date_time(self, name, event = None, csv = None):
        ticker = self.create_event_desciptor_field(name, event, "release-date-time-full")

        if csv is None:
            data_frame = LightEventsFactory._econ_data_frame[ticker]
            data_frame.index = LightEventsFactory._econ_data_frame[ticker]
        else:
            dateparse = lambda x: datetime.datetime.strptime(x, '%d/%m/%Y %H:%M')

            data_frame = pandas.read_csv(csv, index_col=0, parse_dates = True, date_parser=dateparse)

        data_frame = data_frame[pandas.notnull(data_frame.index)]

        start_date = datetime.datetime.strptime("01-Jan-1971", "%d-%b-%Y")
        self.time_series_filter.filter_time_series_by_date(start_date, None, data_frame)

        return data_frame

    def get_economic_event_date_time_dataframe(self, name, event = None, csv = None):
        series = self.get_economic_event_date_time(name, event, csv)

        data_frame = pandas.DataFrame(series.values, index=series.index)
        data_frame.columns.name = self.create_event_desciptor_field(name, event, "release-date-time-full")

        return data_frame

    def get_economic_event_date_time_fields(self, fields, name, event = None):
        ### acceptible fields
        # actual-release
        # survey-median
        # survey-average
        # survey-high
        # survey-low
        # survey-high
        # number-observations
        # release-dt
        # release-date-time-full
        # first-revision
        # first-revision-date

        ticker = []

        # construct tickers of the form USD-US Employees on Nonfarm Payrolls Total MoM Net Change SA.actual-release
        for i in range(0, len(fields)):
            ticker.append(self.create_event_desciptor_field(name, event, fields[i]))

        # index on the release-dt field eg. 20101230 (we shall convert this later)
        ticker_index = self.create_event_desciptor_field(name, event, "release-dt")

        ######## grab event date/times
        event_date_time = self.get_economic_event_date_time(name, event)
        date_time_fore = event_date_time.index

        # create dates for join later
        date_time_dt = [datetime.datetime(
                                date_time_fore[x].year,
                                date_time_fore[x].month,
                                date_time_fore[x].day)
                                for x in range(len(date_time_fore))]

        event_date_time_frame = pandas.DataFrame(event_date_time.index, date_time_dt)
        event_date_time_frame.index = date_time_dt

        ######## grab event date/fields
        data_frame = LightEventsFactory._econ_data_frame[ticker]
        data_frame.index = LightEventsFactory._econ_data_frame[ticker_index]

        data_frame = data_frame[data_frame.index != 0]              # eliminate any 0 dates (artifact of Excel)
        data_frame = data_frame[pandas.notnull(data_frame.index)]   # eliminate any NaN dates (artifact of Excel)
        ind_dt = data_frame.index

        # convert yyyymmdd format to datetime
        data_frame.index = [datetime.datetime(
                               int((ind_dt[x] - (ind_dt[x] % 10000))/10000),
                               int(((ind_dt[x] % 10000) - (ind_dt[x] % 100))/100),
                               int(ind_dt[x] % 100)) for x in range(len(ind_dt))]

        # HACK! certain events need an offset because BBG have invalid dates
        if ticker_index in self._offset_events:
             data_frame.index = data_frame.index + timedelta(days=self._offset_events[ticker_index])

        ######## join together event dates/date-time/fields in one data frame
        data_frame = event_date_time_frame.join(data_frame, how='inner')
        data_frame.index = pandas.to_datetime(data_frame.index)
        data_frame.index.name = ticker_index

        return data_frame

    def create_event_desciptor_field(self, name, event, field):
        if event is None:
            return name + "." + field
        else:
            return name + "-" + event + "." + field

    def get_all_economic_events_date_time(self):
        event_names = self.get_all_economic_events()
        columns = ['event-name', 'release-date-time-full']

        data_frame = pandas.DataFrame(data=numpy.zeros((0,len(columns))), columns=columns)

        for event in event_names:
            event_times = self.get_economic_event_date_time(event)

            for time in event_times:
                data_frame.append({'event-name':event, 'release-date-time-full':time}, ignore_index=True)

        return data_frame

    def get_all_economic_events(self):
        field_names = LightEventsFactory._econ_data_frame.columns.values

        event_names = [x.split('.')[0] for x in field_names if '.Date' in x]

        event_names_filtered = [x for x in event_names if len(x) > 4]

        # sort list alphabetically (and remove any duplicates)
        return list(set(event_names_filtered))

    def get_economic_event_date(self, name, event = None):
        return LightEventsFactory._econ_data_frame[
            self.create_event_desciptor_field(name, event, ".release-dt")]

    def get_economic_event_ret_over_custom_event_day(self, data_frame_in, name, event, start, end, lagged = False,
                                              NYC_cutoff = 10):


        # get the times of events
        event_dates = self.get_economic_event_date_time(name, event)

        return super(LightEventsFactory, self).get_economic_event_ret_over_custom_event_day(data_frame_in, event_dates, name, event, start, end,
                                                                                            lagged = lagged, NYC_cutoff = NYC_cutoff)

    def get_economic_event_vol_over_event_day(self, vol_in, name, event, start, end, realised = False):

        return self.get_economic_event_ret_over_custom_event_day(vol_in, name, event, start, end,
            lagged = realised)

        # return super(EventsFactory, self).get_economic_event_ret_over_event_day(vol_in, name, event, start, end, lagged = realised)

    def get_daily_moves_over_event(self):
        # TODO
        pass

    # return only US events etc. by dates
    def get_intraday_moves_over_event(self, data_frame_rets, cross, event_fx, event_name, start, end, vol, mins = 3 * 60,
                                      min_offset = 0, create_index = False, resample = False, freq = 'minutes'):
        tsf = TimeSeriesFilter()

        ef_time_frame = self.get_economic_event_date_time_dataframe(event_fx, event_name)
        ef_time_frame = tsf.filter_time_series_by_date(start, end, ef_time_frame)

        return self.get_intraday_moves_over_custom_event(data_frame_rets, ef_time_frame,
                                                         vol, mins = mins, min_offset = min_offset,
                                                         create_index = create_index, resample = resample, freq = freq)#, start, end)

    def get_surprise_against_intraday_moves_over_event(self, data_frame_cross_orig, cross, event_fx, event_name, start, end,
                                                       offset_list = [1, 5, 30, 60], add_surprise = False,
                                                       surprise_field = 'survey-average'):

        tsf = TimeSeriesFilter()
        fields = ['actual-release', 'survey-median', 'survey-average', 'survey-high', 'survey-low']

        ef_time_frame = self.get_economic_event_date_time_fields(fields, event_fx, event_name)
        ef_time_frame = tsf.filter_time_series_by_date(start, end, ef_time_frame)

        return self.get_surprise_against_intraday_moves_over_custom_event(data_frame_cross_orig, ef_time_frame, cross, event_fx, event_name, start, end,
                                                       offset_list = offset_list, add_surprise = add_surprise,
                                                       surprise_field = surprise_field)

if __name__ == '__main__':
    pass
    # see examples