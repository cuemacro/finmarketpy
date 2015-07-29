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
LoaderBBGOpen

Calls the Bloomberg Open API to download market data: daily, intraday and reference data.

"""

import abc
import copy
import collections
import datetime
import re

import pandas
import blpapi   # Bloomberg Open API (adapted by Fil Mackay for Python 3.4 - https://github.com/filmackay/blpapi-py)

# Thalesians dependencies
from pythalesians.util.constants import Constants
from pythalesians.util.loggermanager import LoggerManager
from pythalesians.market.loaders.lowlevel.bbg.optionsbbg import OptionsBBG
from pythalesians.market.loaders.lowlevel.bbg.loaderbbg import LoaderBBG

from collections import defaultdict

class LoaderBBGOpen(LoaderBBG):
    def __init__(self):
        super(LoaderBBGOpen, self).__init__()
        self.logger = LoggerManager().getLogger(__name__)

    def download_intraday(self, time_series_request):
        # Bloomberg OpenAPI implementation
        low_level_loader = BBGLowLevelIntraday()

        # by default we download all available fields!
        data_frame = low_level_loader.load_time_series(time_series_request)

        # self.kill_session() # need to forcibly kill_session since can't always reopen

        return data_frame

    def download_daily(self, time_series_request):
        # Bloomberg Open API implementation
        low_level_loader = BBGLowLevelDaily()

        # by default we download all available fields!
        data_frame = low_level_loader.load_time_series(time_series_request)

        # self.kill_session() # need to forcibly kill_session since can't always reopen

        return data_frame

    def download_ref(self, time_series_request):

         # Bloomberg Open API implementation
        low_level_loader = BBGLowLevelRef()

        time_series_request_vendor_selective = copy.copy(time_series_request)
        time_series_request_vendor_selective.fields = ['ECO_FUTURE_RELEASE_DATE_LIST']

        data_frame =  low_level_loader.load_time_series(time_series_request_vendor_selective)

        # self.kill_session() # need to forcibly kill_session since can't always reopen

        return data_frame

    def kill_session(self):
        BBGLowLevelDaily().kill_session()
        BBGLowLevelRef().kill_session()
        BBGLowLevelIntraday().kill_session()

########################################################################################################################
#### Lower level code to interact with Bloomberg Open API

class BBGLowLevelTemplate:

    _session = None

    def __init__(self):
        self._data_frame = None

        self.RESPONSE_ERROR = blpapi.Name("responseError")
        self.SESSION_TERMINATED = blpapi.Name("SessionTerminated")
        self.CATEGORY = blpapi.Name("category")
        self.MESSAGE = blpapi.Name("message")

        return

    def load_time_series(self, time_series_request):

        options = self.fill_options(time_series_request)

        if(BBGLowLevelTemplate._session is None):
            session = self.start_bloomberg_session()
        else:
            session = BBGLowLevelTemplate._session

        try:
            # if can't open the session, kill existing one
            # then try reopen (up to 5 times...)
            i = 0

            while i < 5:
                if session is not None:
                    if not session.openService("//blp/refdata"):
                        self.logger.info("Try reopening Bloomberg session... try " + str(i))
                        self.kill_session() # need to forcibly kill_session since can't always reopen
                        session = self.start_bloomberg_session()

                        if session is not None:
                            if session.openService("//blp/refdata"): i = 6
                else:
                    self.logger.info("Try opening Bloomberg session... try " + str(i))
                    session = self.start_bloomberg_session()

                i = i + 1

            # give error if still doesn't work after several tries..
            if not session.openService("//blp/refdata"):
                self.logger.error("Failed to open //blp/refdata")

                return

            self.logger.info("Creating request...")
            eventQueue = None # blpapi.EventQueue()

            # create a request
            self.send_bar_request(session, eventQueue)
            self.logger.info("Waiting for data to be returned...")

            # wait for events from session and collect the data
            self.event_loop(session, eventQueue)

        finally:
            # stop the session (will fail if NoneType)
            try:
                session.stop()
            except: pass

        return self._data_frame

    def event_loop(self, session, eventQueue):
        not_done = True

        data_frame = pandas.DataFrame()
        data_frame_slice = None

        while not_done:
            # nextEvent() method can be called with timeout to let
            # the program catch Ctrl-C between arrivals of new events
            event = session.nextEvent() # removed time out

            # Bloomberg will send us responses in chunks
            if event.eventType() == blpapi.Event.PARTIAL_RESPONSE:
                # self.logger.info("Processing Bloomberg Partial Response")
                data_frame_slice = self.process_response_event(event)
            elif event.eventType() == blpapi.Event.RESPONSE:
                # self.logger.info("Processing Bloomberg Full Response")
                data_frame_slice = self.process_response_event(event)
                not_done = False
            else:
                for msg in event:
                    if event.eventType() == blpapi.Event.SESSION_STATUS:
                        if msg.messageType() == self.SESSION_TERMINATED:
                            not_done = False

            # append DataFrame only if not empty
            if data_frame_slice is not None:
                if (data_frame.empty):
                    data_frame = data_frame_slice
                else:
                    # make sure we do not reattach a message we've already read
                    # sometimes Bloomberg can give us back the same message several times
                    # CAREFUL with this!
                    # compares the ticker names, and make sure they don't already exist in the time series
                    data_frame = self.combine_slices(data_frame, data_frame_slice)

        # make sure we do not have any duplicates in the time series
        if data_frame is not None:
            if data_frame.empty == False:
                data_frame.drop_duplicates(take_last = True)

        self._data_frame = data_frame

    # process raw message returned by Bloomberg
    def process_response_event(self, event):
        data_frame = pandas.DataFrame()

        for msg in event:
            # generates a lot of output - so don't use unless for debugging purposes
            # self.logger.info(msg)

            if msg.hasElement(self.RESPONSE_ERROR):
                self.logger.error("REQUEST FAILED: ", msg.getElement(self.RESPONSE_ERROR))
                continue

            data_frame_slice = self.process_message(msg)

            if (data_frame_slice is not None):
                if (data_frame.empty):
                    data_frame = data_frame_slice
                else:
                    data_frame = data_frame.append(data_frame_slice)
            else:
                data_frame = data_frame_slice

        return data_frame

    def get_previous_trading_date(self):
        tradedOn = datetime.date.today()

        while True:
            try:
                tradedOn -= datetime.timedelta(days=1)
            except OverflowError:
                return None

            if tradedOn.weekday() not in [5, 6]:
                return tradedOn

    # create a session for Bloomberg with appropriate server & port
    def start_bloomberg_session(self):

        # fill SessionOptions
        sessionOptions = blpapi.SessionOptions()
        sessionOptions.setServerHost(Constants().bbg_server)
        sessionOptions.setServerPort(Constants().bbg_server_port)

        self.logger.info("Starting Bloomberg session...")

        # create a Session
        session = blpapi.Session(sessionOptions)

        # start a Session
        if not session.start():
            self.logger.error("Failed to start session.")
            return

        self.logger.info("Returning session...")

        BBGLowLevelTemplate._session = session

        return session

    def add_override(self, request, field, value):
        overrides = request.getElement("overrides")
        override1 = overrides.appendElement()
        override1.setElement("fieldId", field)
        override1.setElement("value", value)

    @abc.abstractmethod
    def process_message(self, msg):
        # to be implemented by subclass
        return

    # create request for data
    @abc.abstractmethod
    def send_bar_request(self, session, eventQueue):
        # to be implemented by subclass
        return

    # create request for data
    @abc.abstractmethod
    def combine_slices(self, data_frame, data_frame_slice):
        # to be implemented by subclass
        return

    def kill_session(self):
        if (BBGLowLevelTemplate._session is not None):
            try:
                BBGLowLevelTemplate._session.stop()

                self.logger.info("Stopping session...")
            finally:
                self.logger.info("Finally stopping session...")

            BBGLowLevelTemplate._session = None

class BBGLowLevelDaily(BBGLowLevelTemplate):

    def __init__(self):
        super(BBGLowLevelDaily, self).__init__()

        self.logger = LoggerManager().getLogger(__name__)
        self._options = []

    def combine_slices(self, data_frame, data_frame_slice):
        if (data_frame_slice.columns.get_level_values(1).values[0]
            not in data_frame.columns.get_level_values(1).values):

            return data_frame.join(data_frame_slice, how="outer")

        return data_frame

    # populate options for Bloomberg request for asset daily request
    def fill_options(self, time_series_request):
        self._options = OptionsBBG()

        self._options.security = time_series_request.tickers
        self._options.startDateTime = time_series_request.start_date
        self._options.endDateTime = time_series_request.finish_date
        self._options.fields = time_series_request.fields

        return self._options

    def process_message(self, msg):
        # Process received events
        ticker = msg.getElement('securityData').getElement('security').getValue()
        fieldData = msg.getElement('securityData').getElement('fieldData')

        # SLOW loop (careful, not all the fields will be returned every time
        # hence need to include the field name in the tuple)
        data = defaultdict(dict)

        for i in range(fieldData.numValues()):
            for j in range(1, fieldData.getValue(i).numElements()):
                data[(str(fieldData.getValue(i).getElement(j).name()), ticker)][fieldData.getValue(i).getElement(0).getValue()] \
                    = fieldData.getValue(i).getElement(j).getValue()

        data_frame = pandas.DataFrame(data)

        # if obsolete ticker could return no values
        if (not(data_frame.empty)):
            # data_frame.columns = pandas.MultiIndex.from_tuples(data, names=['field', 'ticker'])
            data_frame.index = pandas.to_datetime(data_frame.index)
            self.logger.info("Read: " + ticker + ' ' + str(data_frame.index[0]) + ' - ' + str(data_frame.index[-1]))
        else:
            return None

        return data_frame

    # create request for data
    def send_bar_request(self, session, eventQueue):
        refDataService = session.getService("//blp/refdata")
        request = refDataService.createRequest("HistoricalDataRequest")

        request.set("startDate", self._options.startDateTime.strftime('%Y%m%d'))
        request.set("endDate", self._options.endDateTime.strftime('%Y%m%d'))

        # # only one security/eventType per request
        for field in self._options.fields:
            request.getElement("fields").appendValue(field)

        for security in self._options.security:
            request.getElement("securities").appendValue(security)

        self.logger.info("Sending Bloomberg Daily Request:" + str(request))
        session.sendRequest(request)

class BBGLowLevelRef(BBGLowLevelTemplate):

    def __init__(self):
        super(BBGLowLevelRef, self).__init__()

        self.logger = LoggerManager().getLogger(__name__)
        self._options = []

    # populate options for Bloomberg request for asset intraday request
    def fill_options(self, time_series_request):
        self._options = OptionsBBG()

        self._options.security = time_series_request.tickers
        self._options.startDateTime = time_series_request.start_date
        self._options.endDateTime = time_series_request.finish_date
        self._options.fields = time_series_request.fields

        return self._options

    def process_message(self, msg):
        data = collections.defaultdict(dict)

        # process received events
        securityDataArray = msg.getElement('securityData')

        index = 0

        for securityData in list(securityDataArray.values()):
            ticker = securityData.getElementAsString("security")
            fieldData = securityData.getElement("fieldData")

            for field in fieldData.elements():
                if not field.isValid():
                    field_name = "%s" % field.name()

                    self.logger.error(field_name + " is NULL")
                elif field.isArray():
                    # iterate over complex data returns.
                    field_name = "%s" % field.name()

                    for i, row in enumerate(field.values()):
                        data[(field_name, ticker)][index] = re.findall(r'"(.*?)"', "%s" % row)[0]

                        index = index + 1
                # else:
                    # vals.append(re.findall(r'"(.*?)"', "%s" % row)[0])
                    # print("%s = %s" % (field.name(), field.getValueAsString()))

            fieldExceptionArray = securityData.getElement("fieldExceptions")

            for fieldException in list(fieldExceptionArray.values()):
                errorInfo = fieldException.getElement("errorInfo")
                print(errorInfo.getElementAsString("category"), ":", \
                    fieldException.getElementAsString("fieldId"))

        data_frame = pandas.DataFrame(data)

        # if obsolete ticker could return no values
        if (not(data_frame.empty)):
            data_frame.columns = pandas.MultiIndex.from_tuples(data, names=['field', 'ticker'])
            self.logger.info("Reading: " + ticker + ' ' + str(data_frame.index[0]) + ' - ' + str(data_frame.index[-1]))
        else:
            return None

        return data_frame

    def combine_slices(self, data_frame, data_frame_slice):
        if (data_frame_slice.columns.get_level_values(1).values[0]
            not in data_frame.columns.get_level_values(1).values):

            return data_frame.join(data_frame_slice, how="outer")

        return data_frame

    # create request for data
    def send_bar_request(self, session, eventQueue):
        refDataService = session.getService("//blp/refdata")
        request = refDataService.createRequest('ReferenceDataRequest')

        self.add_override(request, 'TIME_ZONE_OVERRIDE', 23)    # force GMT time
        self.add_override(request, 'START_DT', self._options.startDateTime.strftime('%Y%m%d'))
        self.add_override(request, 'END_DT', self._options.endDateTime.strftime('%Y%m%d'))

        # only one security/eventType per request
        for field in self._options.fields:
            request.getElement("fields").appendValue(field)

        for security in self._options.security:
            request.getElement("securities").appendValue(security)

        self.logger.info("Sending Bloomberg Ref Request:" + str(request))
        session.sendRequest(request)

from operator import itemgetter

class BBGLowLevelIntraday(BBGLowLevelTemplate):

    def __init__(self):
        super(BBGLowLevelIntraday, self).__init__()

        self.logger = LoggerManager().getLogger(__name__)

        # constants
        self.BAR_DATA = blpapi.Name("barData")
        self.BAR_TICK_DATA = blpapi.Name("barTickData")
        self.OPEN = blpapi.Name("open")
        self.HIGH = blpapi.Name("high")
        self.LOW = blpapi.Name("low")
        self.CLOSE = blpapi.Name("close")
        self.VOLUME = blpapi.Name("volume")
        self.NUM_EVENTS = blpapi.Name("numEvents")
        self.TIME = blpapi.Name("time")

    def combine_slices(self, data_frame, data_frame_slice):
        return data_frame.append(data_frame_slice)

    # populate options for Bloomberg request for asset intraday request
    def fill_options(self, time_series_request):
        self._options = OptionsBBG()

        self._options.security = time_series_request.tickers[0]    # get 1st ticker only!
        self._options.event = "TRADE"
        self._options.barInterval = time_series_request.freq_mult
        self._options.startDateTime = time_series_request.start_date
        self._options.endDateTime = time_series_request.finish_date
        self._options.gapFillInitialBar = False

        if hasattr(self._options.startDateTime, 'microsecond'):
            self._options.startDateTime = self._options.startDateTime.replace(microsecond=0)

        if hasattr(self._options.endDateTime, 'microsecond'):
            self._options.endDateTime = self._options.endDateTime.replace(microsecond=0)

        return self._options

    # iterate through Bloomberg output creating a DataFrame output
    # implements abstract method
    def process_message(self, msg):
        data = msg.getElement(self.BAR_DATA).getElement(self.BAR_TICK_DATA)

        self.logger.info("Processing intraday data for " + str(self._options.security))

        data_vals = list(data.values())

        # data_matrix = numpy.zeros([len(data_vals), 6])
        # data_matrix.fill(numpy.nan)
        #
        # date_index = [None] * len(data_vals)
        #
        # for i in range(0, len(data_vals)):
        #     data_matrix[i][0] = data_vals[i].getElementAsFloat(self.OPEN)
        #     data_matrix[i][1] = data_vals[i].getElementAsFloat(self.HIGH)
        #     data_matrix[i][2] = data_vals[i].getElementAsFloat(self.LOW)
        #     data_matrix[i][3] = data_vals[i].getElementAsFloat(self.CLOSE)
        #     data_matrix[i][4] = data_vals[i].getElementAsInteger(self.VOLUME)
        #     data_matrix[i][5] = data_vals[i].getElementAsInteger(self.NUM_EVENTS)
        #
        #     date_index[i] = data_vals[i].getElementAsDatetime(self.TIME)
        #
        # self.logger.info("Dates between " + str(date_index[0]) + " - " + str(date_index[-1]))
        #
        # # create pandas dataframe with the Bloomberg output
        # return pandas.DataFrame(data = data_matrix, index = date_index,
        #                columns=['open', 'high', 'low', 'close', 'volume', 'events'])

        ## for loop method is touch slower
        # time_list = []
        # data_table = []

        # for bar in data_vals:
        #     data_table.append([bar.getElementAsFloat(self.OPEN),
        #                  bar.getElementAsFloat(self.HIGH),
        #                  bar.getElementAsFloat(self.LOW),
        #                  bar.getElementAsFloat(self.CLOSE),
        #                  bar.getElementAsInteger(self.VOLUME),
        #                  bar.getElementAsInteger(self.NUM_EVENTS)])
        #
        #     time_list.append(bar.getElementAsDatetime(self.TIME))

        # each price time point has multiple fields - marginally quicker
        tuple = [([bar.getElementAsFloat(self.OPEN),
                        bar.getElementAsFloat(self.HIGH),
                        bar.getElementAsFloat(self.LOW),
                        bar.getElementAsFloat(self.CLOSE),
                        bar.getElementAsInteger(self.VOLUME),
                        bar.getElementAsInteger(self.NUM_EVENTS)],
                        bar.getElementAsDatetime(self.TIME)) for bar in data_vals]

        data_table = list(map(itemgetter(0), tuple))
        time_list = list(map(itemgetter(1), tuple))

        try:
            self.logger.info("Dates between " + str(time_list[0]) + " - " + str(time_list[-1]))
        except:
            self.logger.info("No dates retrieved")
            return None

        # create pandas dataframe with the Bloomberg output
        return pandas.DataFrame(data = data_table, index = time_list,
                      columns=['open', 'high', 'low', 'close', 'volume', 'events'])

    # implement abstract method: create request for data
    def send_bar_request(self, session, eventQueue):
        refDataService = session.getService("//blp/refdata")
        request = refDataService.createRequest("IntradayBarRequest")

        # only one security/eventType per request
        request.set("security", self._options.security)
        request.set("eventType", self._options.event)
        request.set("interval", self._options.barInterval)

        # self.add_override(request, 'TIME_ZONE_OVERRIDE', 'GMT')

        if self._options.startDateTime and self._options.endDateTime:
            request.set("startDateTime", self._options.startDateTime)
            request.set("endDateTime", self._options.endDateTime)

        if self._options.gapFillInitialBar:
            request.append("gapFillInitialBar", True)

        self.logger.info("Sending Intraday Bloomberg Request...")

        session.sendRequest(request)

if __name__ == '__main__':
    pass

    # TODO methods to test higher level code
    # TODO methods to test lower level code