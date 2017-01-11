__author__ = 'saeedamen' # Saeed Amen / saeed@thalesians.com

#
# Copyright 2016 Cuemacro
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the
# License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the License for the specific language governing permissions and limitations under the License.
#


import math

from pandas.tseries.offsets import CustomBusinessDay

from findatapy.timeseries import Calculations, Timezone, Filter, Calendar

class EventStudy(object):
    """Provides functions for doing event studies on price action on an intraday basis and daily basis.

    """

    def __init__(self):
        self.logger = LoggerManager().getLogger(__name__)
        return

    def get_economic_event_ret_over_custom_event_day(self, data_frame_in, event_dates, name, event, start, end, lagged = False,
                                              NYC_cutoff = 10):

        filter = Filter()
        event_dates = filter.filter_time_series_by_date(start, end, event_dates)

        data_frame = data_frame_in.copy(deep=True) # because we change the dates!

        timezone = Timezone()
        calendar = Calendar()

        bday = CustomBusinessDay(weekmask='Mon Tue Wed Thu Fri')

        event_dates_nyc = timezone.convert_index_from_UTC_to_new_york_time(event_dates)
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

        filter = Filter()

        ef_time_frame = filter.filter_time_series_by_date(data_frame_rets.index[0], data_frame_rets.index[-1], ef_time_frame)
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

            # make sure time series is properly sampled at 1 min intervals
            data_frame_rets = data_frame_rets.resample('1min')
            data_frame_rets = data_frame_rets.fillna(value = 0)
            data_frame_rets = filter.remove_out_FX_out_of_hours(data_frame_rets)

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
            calculations = Calculations()
            data_frame.ix[-minute_start + min_offset,:] = numpy.nan
            data_frame = calculations.create_mult_index(data_frame)
        else:
            if vol is True:
                # annualise (if vol)
                data_frame = data_frame.rolling(center=False,window=5).std() * math.sqrt(ann_factor)
            else:
                data_frame = data_frame.cumsum()

        return data_frame

    def get_surprise_against_intraday_moves_over_custom_event(
            self, data_frame_cross_orig, ef_time_frame, cross, event_fx, event_name, start, end,
            offset_list = [1, 5, 30, 60], add_surprise = False, surprise_field = 'survey-average', freq = 'minutes'):

        ticker = event_fx + "-" + event_name + ".release-date-time-full"

        data_frame_agg = None
        data_frame_cross_orig = data_frame_cross_orig.resample('T').mean()  # resample to minute freq - in case there are missing values

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

########################################################################################################################

import datetime
from datetime import timedelta

import numpy

from finmarketpy.util.marketconstants import MarketConstants
from findatapy.market import IOEngine
from findatapy.util import ConfigManager

try:
    from numbapro import autojit
except: pass

class EventsFactory(EventStudy):
    """Provides methods to fetch data on economic data events and to perform basic event studies for market data around
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

    # _econ_data_frame = None

    # where your HDF5 file is stored with economic data
    # TODO integrate with on the fly downloading!
    _hdf5_file_econ_file = MarketConstants().hdf5_file_econ_file
    _arctic_database = MarketConstants().arctic_database_econ_file

    ### manual offset for certain events where Bloomberg displays the wrong date (usually because of time differences)
    _offset_events = {'AUD-Australia Labor Force Employment Change SA.release-dt' : 1}

    def __init__(self, df = None):
        super(EventStudy, self).__init__()

        self.config = ConfigManager()
        self.logger = LoggerManager().getLogger(__name__)
        self.filter = Filter()
        self.io_engine =IOEngine()

        if df is not None:
            self._econ_data_frame = df
        else:
            self.load_economic_events()

        return

    def load_economic_events(self):
        # self._econ_data_frame = self.io_engine.read_time_series_cache_from_disk(self._hdf5_file_econ_file)
        self._econ_data_frame = self.io_engine.read_time_series_cache_from_disk(self._arctic_database, engine='arctic',
                                                                                db_server=MarketConstants().arctic_server)

    def harvest_category(self, category_name):
        cat = self.config.get_categories_from_tickers_selective_filter(category_name)

        for k in cat:
            md_request = self.market_data_generator.populate_md_request(k)
            data_frame = self.market_data_generator.fetch_market_data(md_request)

            # TODO allow merge of multiple sources

        return data_frame

    def get_economic_events(self):
        return self._econ_data_frame

    def dump_economic_events_csv(self, path):
        self._econ_data_frame.to_csv(path)

    def get_economic_event_date_time(self, name, event = None, csv = None):
        ticker = self.create_event_desciptor_field(name, event, "release-date-time-full")

        if csv is None:
            data_frame = self._econ_data_frame[ticker]
            data_frame.index = self._econ_data_frame[ticker]
        else:
            dateparse = lambda x: datetime.datetime.strptime(x, '%d/%m/%Y %H:%M')

            data_frame = pandas.read_csv(csv, index_col=0, parse_dates = True, date_parser=dateparse)

        data_frame = data_frame[pandas.notnull(data_frame.index)]

        start_date = datetime.datetime.strptime("01-Jan-1971", "%d-%b-%Y")
        self.filter.filter_time_series_by_date(start_date, None, data_frame)

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
        data_frame = self._econ_data_frame[ticker]
        data_frame.index = self._econ_data_frame[ticker_index]

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
        field_names = self._econ_data_frame.columns.values

        event_names = [x.split('.')[0] for x in field_names if '.Date' in x]

        event_names_filtered = [x for x in event_names if len(x) > 4]

        # sort list alphabetically (and remove any duplicates)
        return list(set(event_names_filtered))

    def get_economic_event_date(self, name, event = None):
        return self._econ_data_frame[
            self.create_event_desciptor_field(name, event, ".release-dt")]

    def get_economic_event_ret_over_custom_event_day(self, data_frame_in, name, event, start, end, lagged = False,
                                              NYC_cutoff = 10):


        # get the times of events
        event_dates = self.get_economic_event_date_time(name, event)

        return super(EventsFactory, self).get_economic_event_ret_over_custom_event_day(data_frame_in, event_dates, name, event, start, end,
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

        ef_time_frame = self.get_economic_event_date_time_dataframe(event_fx, event_name)
        ef_time_frame = self.filter.filter_time_series_by_date(start, end, ef_time_frame)

        return self.get_intraday_moves_over_custom_event(data_frame_rets, ef_time_frame,
                                                         vol, mins = mins, min_offset = min_offset,
                                                         create_index = create_index, resample = resample, freq = freq)#, start, end)

    def get_surprise_against_intraday_moves_over_event(self, data_frame_cross_orig, cross, event_fx, event_name, start, end,
                                                       offset_list = [1, 5, 30, 60], add_surprise = False,
                                                       surprise_field = 'survey-average'):

        fields = ['actual-release', 'survey-median', 'survey-average', 'survey-high', 'survey-low']

        ef_time_frame = self.get_economic_event_date_time_fields(fields, event_fx, event_name)
        ef_time_frame = self.filter.filter_time_series_by_date(start, end, ef_time_frame)

        return self.get_surprise_against_intraday_moves_over_custom_event(data_frame_cross_orig, ef_time_frame, cross, event_fx, event_name, start, end,
                                                       offset_list = offset_list, add_surprise = add_surprise,
                                                       surprise_field = surprise_field)

########################################################################################################################

"""
HistEconDataFactory

Provides functions for getting historical economic data. Uses aliases for tickers, to make it relatively easy to use,
rather than having to remember all the underlying vendor tickers. Can use Fred, Quandl or Bloomberg.

The files below, contain default tickers and country groups. However, you can add whichever tickers you'd like.
- conf/all_econ_tickers.csv
- conf/econ_country_codes.csv
- conf/econ_country_groups.csv

These can be automatically generated via conf/econ_tickers.xlsm

"""

import pandas

from findatapy.market import MarketDataGenerator, MarketDataRequest
from findatapy.util import DataConstants, LoggerManager

class HistEconDataFactory(object):

    def __init__(self, market_data_generator = None):
        self.logger = LoggerManager().getLogger(__name__)

        self._all_econ_tickers = pandas.read_csv(DataConstants().all_econ_tickers)
        self._econ_country_codes = pandas.read_csv(DataConstants().econ_country_codes)
        self._econ_country_groups = pandas.read_csv(DataConstants().econ_country_groups)

        if market_data_generator is None:
            self.market_data_generator = MarketDataGenerator()
        else:
            self.market_data_generator = market_data_generator

    def get_economic_data_history(self, start_date, finish_date, country_group, data_type,
        source = 'fred', cache_algo = "internet_load_return"):

        #vendor_country_codes = self.fred_country_codes[country_group]
        #vendor_pretty_country = self.fred_nice_country_codes[country_group]

        if isinstance(country_group, list):
            pretty_country_names = country_group
        else:
            # get all the country names in the country_group
            pretty_country_names = list(self._econ_country_groups[
                self._econ_country_groups["Country Group"] == country_group]['Country'])

        # construct the pretty tickers
        pretty_tickers = [x + '-' + data_type for x in pretty_country_names]

        # get vendor tickers
        vendor_tickers = []

        for pretty_ticker in pretty_tickers:
            vendor_ticker = list(self._all_econ_tickers[
                                         self._all_econ_tickers["Full Code"] == pretty_ticker][source].values)

            if vendor_ticker == []:
                vendor_ticker = None
                self.logger.error('Could not find match for ' + pretty_ticker)
            else:
                vendor_ticker = vendor_ticker[0]

            vendor_tickers.append(vendor_ticker)

        vendor_fields = ['close']

        if source == 'bloomberg': vendor_fields = ['PX_LAST']

        md_request = MarketDataRequest(
                start_date = start_date,                            # start date
                finish_date = finish_date,                          # finish date
                category = 'economic',
                freq = 'daily',                                     # intraday data
                data_source = source,                               # use Bloomberg as data source
                cut = 'LOC',
                tickers = pretty_tickers,
                fields = ['close'],                                 # which fields to download
                vendor_tickers = vendor_tickers,
                vendor_fields = vendor_fields,                      # which Bloomberg fields to download
                cache_algo = cache_algo)                            # how to return data

        return self.market_data_generator.fetch_market_data(md_request)

    def grasp_coded_entry(self, df, index):
        df = df.ix[index:].stack()
        df = df.reset_index()
        df.columns = ['Date', 'Name', 'Val']

        countries = df['Name']

        countries = [x.split('-', 1)[0] for x in countries]

        df['Code'] = sum(
            [list(self._econ_country_codes[self._econ_country_codes["Country"] == x]['Code']) for x in countries],
            [])

        return df