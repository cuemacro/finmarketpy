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
LoaderBBGCOM

Calls the Bloomberg COM API to download market data: daily, intraday and reference data.

"""

from pythalesians.util.loggermanager import LoggerManager
from pythalesians.market.loaders.lowlevel.bbg.loaderbbg import LoaderBBG

class LoaderBBGCOM(LoaderBBG):
    def __init__(self):
        super(LoaderBBGCOM, self).__init__()
        self.logger = LoggerManager().getLogger(__name__)

    def download_tick(self, time_series_request):
        # TODO not implemented
        return None

    def download_intraday(self, time_series_request):
        low_level_loader = IntradayBarRequest(time_series_request.tickers, interval=time_series_request.freq_mult,
                start = time_series_request.start_date, end = time_series_request.finish_date)

        low_level_loader.execute()

        return low_level_loader.response

    def download_daily(self, time_series_request):
        low_level_loader = HistoricalDataRequest(time_series_request.tickers, time_series_request.fields,
                start = time_series_request.start_date, end = time_series_request.finish_date,
                period = self.translate_to_vendor_freq(time_series_request.freq))

        low_level_loader.execute()
        data_frame = low_level_loader.response_as_single()

        # convert from vendor to Thalesians tickers/fields
        if data_frame is not None:
            returned_fields = data_frame.columns.get_level_values(0)
            returned_tickers = data_frame.columns.get_level_values(1)

        return [returned_fields, returned_tickers, data_frame]

    def download_ref(self, time_series_request):
        # TODO unstable
        ov = {'START_DT': time_series_request.start_date.strftime('%Y%m%d'), 'END_DT': time_series_request.finish_date.strftime('%Y%m%d')}

        low_level_loader_ref = ReferenceDataRequest(time_series_request.tickers, 'ECO_FUTURE_RELEASE_DATE_LIST', overrides=ov, response_type='map')
        return low_level_loader_ref.execute().response

    def kill_session(self):
        return


########################################################################################################################
#### Lower level code to interact with Bloomberg COM
########################################################################################################################


# Following methods are for using the bbg COM API v3 from Python.
# Heavily based on code written by Brian P. Smith (brian.p.smith@gmail.com), adapted for Python 3.4
# COM API v3 is left for backwards compatibility & easier to install on Windows. Recommend using BBG Open API.

from win32gui import PumpWaitingMessages
from win32com.client import DispatchWithEvents, constants, CastTo
from collections import defaultdict, namedtuple
from datetime import datetime, timedelta
from pandas import DataFrame, to_datetime, concat, Panel
import numpy as np

SecurityErrorAttrs = ['security', 'source', 'code', 'category', 'message', 'subcategory']
SecurityError = namedtuple('SecurityError', SecurityErrorAttrs)
FieldErrorAttrs = ['security', 'field', 'source', 'code', 'category', 'message', 'subcategory']
FieldError = namedtuple('FieldError', FieldErrorAttrs)

# poor mans debugging
DEBUG = False

class XmlHelper(object):

    @staticmethod
    def security_iter(nodearr):
        """ provide a security data iterator by returning a tuple of (Element, SecurityError) which are mutually exclusive """
        assert nodearr.Name == 'securityData' and nodearr.IsArray
        for i in range(nodearr.NumValues):
            node = nodearr.GetValue(i)
            err = XmlHelper.get_security_error(node)
            result = (None, err) if err else (node, None)
            yield result

    @staticmethod
    def message_iter(evt):
        """ provide a message iterator which checks for a response error prior to returning """
        iter = evt.CreateMessageIterator()
        while iter.Next():
            msg = iter.Message
            if DEBUG:
                print(msg.Print)
            if msg.AsElement.HasElement('responseError'):
                raise Exception(msg.AsElement.GetValue('message'))
            yield msg

    @staticmethod
    def get_sequence_value(node):
        """Convert an element with DataType Sequence to a DataFrame.
        Note this may be a naive implementation as I assume that bulk data is always a table
        """
        assert node.Datatype == 15
        data = defaultdict(list)
        cols = []
        for i in range(node.NumValues):
            row = node.GetValue(i)
            if i == 0:  # Get the ordered cols and assume they are constant
                cols = [str(row.GetElement(_).Name) for _ in range(row.NumElements)]

            for cidx in range(row.NumElements):
                col = row.GetElement(cidx)
                data[str(col.Name)].append(XmlHelper.as_value(col))
        return DataFrame(data, columns=cols)

    @staticmethod
    def as_value(ele):
        """ convert the specified element as a python value """
        dtype = ele.Datatype
        #print '%s = %s' % (ele.Name, dtype)
        if dtype in (1, 2, 3, 4, 5, 6, 7, 9, 12):
            # BOOL, CHAR, BYTE, INT32, INT64, FLOAT32, FLOAT64, BYTEARRAY, DECIMAL)
            return ele.Value
        elif dtype == 8:  # String
            return str(ele.Value)
        elif dtype == 10:  # Date
            v = ele.Value
            return datetime(year=v.year, month=v.month, day=v.day).date() if v else np.nan
        elif dtype == 11:  # Time
            v = ele.Value
            return datetime(hour=v.hour, minute=v.minute, second=v.second).time() if v else np.nan
        elif dtype == 13:  # Datetime
            v = ele.Value
            return datetime(year=v.year, month=v.month, day=v.day, hour=v.hour, minute=v.minute, second=v.second)
        elif dtype == 14:  # Enumeration
            raise NotImplementedError('ENUMERATION data type needs implemented')
        elif dtype == 16:  # Choice
            raise NotImplementedError('CHOICE data type needs implemented')
        elif dtype == 15:  # SEQUENCE
            return XmlHelper.get_sequence_value(ele)
        else:
            raise NotImplementedError('Unexpected data type %s. Check documentation' % dtype)

    @staticmethod
    def get_child_value(parent, name):
        """ return the value of the child element with name in the parent Element """
        return XmlHelper.as_value(parent.GetElement(name))

    @staticmethod
    def get_child_values(parent, names):
        """ return a list of values for the specified child fields. If field not in Element then replace with nan. """
        vals = []
        for name in names:
            if parent.HasElement(name):
                vals.append(XmlHelper.as_value(parent.GetElement(name)))
            else:
                vals.append(np.nan)
        return vals

    @staticmethod
    def as_security_error(node, secid):
        """ convert the securityError element to a SecurityError """
        assert node.Name == 'securityError'
        src = XmlHelper.get_child_value(node, 'source')
        code = XmlHelper.get_child_value(node, 'code')
        cat = XmlHelper.get_child_value(node, 'category')
        msg = XmlHelper.get_child_value(node, 'message')
        subcat = XmlHelper.get_child_value(node, 'subcategory')
        return SecurityError(security=secid, source=src, code=code, category=cat, message=msg, subcategory=subcat)

    @staticmethod
    def as_field_error(node, secid):
        """ convert a fieldExceptions element to a FieldError or FieldError array """
        assert node.Name == 'fieldExceptions'
        if node.IsArray:
            return [XmlHelper.as_field_error(node.GetValue(_), secid) for _ in range(node.NumValues)]
        else:
            fld = XmlHelper.get_child_value(node, 'fieldId')
            info = node.GetElement('errorInfo')
            src = XmlHelper.get_child_value(info, 'source')
            code = XmlHelper.get_child_value(info, 'code')
            cat = XmlHelper.get_child_value(info, 'category')
            msg = XmlHelper.get_child_value(info, 'message')
            subcat = XmlHelper.get_child_value(info, 'subcategory')

            return FieldError(security=secid, field=fld, source=src, code=code, category=cat, message=msg, subcategory=subcat)

    @staticmethod
    def get_security_error(node):
        """ return a SecurityError if the specified securityData element has one, else return None """
        assert node.Name == 'securityData' and not node.IsArray
        if node.HasElement('securityError'):
            secid = XmlHelper.get_child_value(node, 'security')
            err = XmlHelper.as_security_error(node.GetElement('securityError'), secid)
            return err
        else:
            return None

    @staticmethod
    def get_field_errors(node):
        """ return a list of FieldErrors if the specified securityData element has field errors """
        assert node.Name == 'securityData' and not node.IsArray
        nodearr = node.GetElement('fieldExceptions')
        if nodearr.NumValues > 0:
            secid = XmlHelper.get_child_value(node, 'security')
            errors = XmlHelper.as_field_error(nodearr, secid)
            return errors
        else:
            return None


def debug_event(evt):
    print('unhandled event: %s' % evt.EventType)
    if evt.EventType in [constants.RESPONSE, constants.PARTIAL_RESPONSE]:
        print('messages:')
        for msg in XmlHelper.message_iter(evt):
            print(msg.Print)

class ResponseHandler(object):

    def do_init(self, handler):
        """ will be called prior to waiting for the message """
        self.waiting = True
        self.exc_info = None
        self.handler = handler

    def set_evt_handler(self, handler):
        self.handler = handler

    def OnProcessEvent(self, evt):
        try:
            evt = CastTo(evt, 'Event')
            if not self.handler:
                debug_event(evt)

            if evt.EventType == constants.RESPONSE:
                self.handler.on_event(evt, is_final=True)
                self.waiting = False
            elif evt.EventType == constants.PARTIAL_RESPONSE:
                self.handler.on_event(evt, is_final=False)
            else:
                self.handler.on_admin_event(evt)
        except Exception:
            import sys
            self.waiting = False
            self.exc_info = sys.exc_info()

    @property
    def has_deferred_exception(self):
        return # self.exc_info is not None

    def raise_deferred_exception(self):
        return #raise self.exc_info[1], None, self.exc_info[2]

    def do_cleanup(self):
        self.waiting = False
        self.exc_info = None
        self.handler = None

class Request(object):

    def __init__(self, ignore_security_error=0, ignore_field_error=0):
        self.field_errors = []
        self.security_errors = []
        self.ignore_security_error = ignore_security_error
        self.ignore_field_error = ignore_field_error

    @property
    def has_exception(self):
        if not self.ignore_security_error and len(self.security_errors) > 0:
            return True
        if not self.ignore_field_error and len(self.field_errors) > 0:
            return True

    def raise_exception(self):
        if not self.ignore_security_error and len(self.security_errors) > 0:
            msgs = ['(%s, %s, %s)' % (s.security, s.category, s.message) for s in self.security_errors]
            raise Exception('SecurityError: %s' % ','.join(msgs))
        if not self.ignore_field_error and len(self.field_errors) > 0:
            msgs = ['(%s, %s, %s, %s)' % (s.security, s.field, s.category, s.message) for s in self.field_errors]
            raise Exception('FieldError: %s' % ','.join(msgs))
        raise Exception('Programmer Error: No exception to raise')

    def get_bbg_request(self, svc, session):
        raise NotImplementedError()

    def get_bbg_service_name(self):
        raise NotImplementedError()

    def on_event(self, evt, is_final):
        raise NotImplementedError()

    def on_admin_event(self, evt):
        pass

    def execute(self):
        Terminal.execute_request(self)
        return self

    @staticmethod
    def apply_overrides(request, omap):
        """ add the given overrides (omap) to bbg request """
        if omap:
            #for k, v in iter(omap.items()):
            #    o = request.GetElement('overrides').AppendElment()
            #    o.SetElement('fieldId', k)
            #    o.SetElement('value', v)

            for key in omap:
                o = request.GetElement('overrides').AppendElment()
                o.SetElement('fieldId', key)
                o.SetElement('value', omap[key])

class ReferenceDataRequest(Request):

    def __init__(self, symbols, fields, overrides=None, response_type='frame', ignore_security_error=0, ignore_field_error=0):
        """
        response_type: (frame, map) how to return the results
        """
        assert response_type in ('frame', 'map')
        Request.__init__(self, ignore_security_error=ignore_security_error, ignore_field_error=ignore_field_error)
        self.symbols = isinstance(symbols, str) and [symbols] or symbols
        self.fields = isinstance(fields, str) and [fields] or fields
        self.overrides = overrides
        # response related
        self.response = {} if response_type == 'map' else defaultdict(list)
        self.response_type = response_type

        self.logger = LoggerManager().getLogger(__name__)

    def get_bbg_service_name(self):
        return '//blp/refdata'

    def quick_override(self, request, fieldId, val):
        o = request.GetElement('overrides').AppendElment()
        o.SetElement('fieldId', fieldId)
        o.SetElement('value', val)

    def get_bbg_request(self, svc, session):
        # create the bbg request object
        request = svc.CreateRequest('ReferenceDataRequest')
        [request.GetElement('securities').AppendValue(sec) for sec in self.symbols]
        [request.GetElement('fields').AppendValue(fld) for fld in self.fields]

        #self.quick_override(request, 'START_DT', '19990101')
        #self.quick_override(request, 'END_DT', '20200101')

        self.quick_override(request, 'TIME_ZONE_OVERRIDE', 23)  # force GMT time

        Request.apply_overrides(request, self.overrides)
        return request

    def on_security_node(self, node):
        sid = XmlHelper.get_child_value(node, 'security')
        farr = node.GetElement('fieldData')
        fdata = XmlHelper.get_child_values(farr, self.fields)

        self.logger.debug("Returning reference data...")

        assert len(fdata) == len(self.fields), 'field length must match data length'

        if self.response_type == 'map':
            self.response[sid] = fdata
        else:
            self.response['security'].append(sid)
            [self.response[f].append(d) for f, d in zip(self.fields, fdata)]

        # Add any field errors if
        ferrors = XmlHelper.get_field_errors(node)
        ferrors and self.field_errors.extend(ferrors)

    def on_event(self, evt, is_final):
        """ this is invoked from in response to COM PumpWaitingMessages - different thread """

        for msg in XmlHelper.message_iter(evt):
            for node, error in XmlHelper.security_iter(msg.GetElement('securityData')):
                if error:
                    self.security_errors.append(error)
                else:
                    self.on_security_node(node)

        if is_final and self.response_type == 'frame':
            index = self.response.pop('security')
            frame = DataFrame(self.response, columns=self.fields, index=index)
            frame.index.name = 'security'
            self.response = frame

class HistoricalDataRequest(Request):

    def __init__(self, symbols, fields, start=None, end=None, period='DAILY', addtl_sets=None, ignore_security_error=0, ignore_field_error=0):
        """ Historical data request for bbg.

        Parameters
        ----------
        symbols : string or list
        fields : string or list
        start : start date (if None then use 1 year ago)
        end : end date (if None then use today)
        period : ('DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'SEMI-ANNUAL', 'YEARLY')
        ignore_field_errors : bool
        ignore_security_errors : bool

        """

        Request.__init__(self, ignore_security_error=ignore_security_error, ignore_field_error=ignore_field_error)

        assert period in ('DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'SEMI-ANNUAL', 'YEARLY')
        self.symbols = isinstance(symbols, str) and [symbols] or symbols
        self.fields = isinstance(fields, str) and [fields] or fields

        if start is None:
            start = datetime.today() - timedelta(365)   # by default download the past year
        if end is None:
            end = datetime.today()

        self.start = to_datetime(start)
        self.end = to_datetime(end)
        self.period = period

        self.logger = LoggerManager().getLogger(__name__)

        # response related
        self.response = {}

    def get_bbg_service_name(self):
        return '//blp/refdata'

    def get_bbg_request(self, svc, session):
        # create the bbg request object
        request = svc.CreateRequest('HistoricalDataRequest')
        [request.GetElement('securities').AppendValue(sec) for sec in self.symbols]
        [request.GetElement('fields').AppendValue(fld) for fld in self.fields]
        request.Set('startDate', self.start.strftime('%Y%m%d'))
        request.Set('endDate', self.end.strftime('%Y%m%d'))
        request.Set('periodicitySelection', self.period)

        o = request.GetElement('overrides').AppendElment()
        o.SetElement('fieldId', 'TIME_ZONE_OVERRIDE')
        o.SetElement('value', 'GMT')

        return request

    def on_security_data_node(self, node):
        """ process a securityData node - FIXME: currently not handling relateDate node """
        sid = XmlHelper.get_child_value(node, 'security')
        farr = node.GetElement('fieldData')
        dmap = defaultdict(list)

        self.logger.info("Fetching ticker " + sid)

        for i in range(farr.NumValues):
            pt = farr.GetValue(i)
            [dmap[f].append(XmlHelper.get_child_value(pt, f)) for f in ['date'] + self.fields]

        self.logger.info("Returning ticker " + sid)

        idx = dmap.pop('date')
        frame = DataFrame(dmap, columns=self.fields, index=idx)
        frame.index.name = 'date'
        self.response[sid] = frame

    def on_event(self, evt, is_final):
        """
        on_event - This is invoked from in response to COM PumpWaitingMessages - different thread

        """

        for msg in XmlHelper.message_iter(evt):
            # Single security element in historical request
            node = msg.GetElement('securityData')
            if node.HasElement('securityError'):
                self.security_errors.append(XmlHelper.as_security_error(node.GetElement('securityError')))
            else:
                self.on_security_data_node(node)

    def response_as_single(self, copy=0):
        """
        response_as_single - convert the response map to a single data frame with Multi-Index columns

        """

        arr = []

        for sid, frame in self.response.items():
            if copy:
                frame = frame.copy()
            'security' not in frame and frame.insert(0, 'security', sid)
            arr.append(frame.reset_index().set_index(['date', 'security']))

        # time.sleep(1000)
        if (arr == []): return arr

        return concat(arr).unstack()

    def response_as_panel(self, swap=False):
        panel = Panel(self.response)
        if swap:
            panel = panel.swapaxes('items', 'minor')
        return panel

class IntradayBarRequest(Request):

    def __init__(self, symbol, interval, start=None, end=None, event='TRADE'):
        """
        Intraday bar request for bbg

        Parameters
        ----------
        symbols : string
        interval : number of minutes
        start : start date
        end : end date (if None then use today)
        event : (TRADE,BID,ASK,BEST_BID,BEST_ASK)

        """

        Request.__init__(self)

        self.logger = LoggerManager().getLogger(__name__)

        assert event in ('TRADE', 'BID', 'ASK', 'BEST_BID', 'BEST_ASK')
        assert isinstance(symbol, str)

        if start is None:
            start = datetime.today() - timedelta(30)

        if end is None:
            end = datetime.utcnow()

        self.symbol = symbol
        self.interval = interval
        self.start = to_datetime(start)
        self.end = to_datetime(end)
        self.event = event

        # response related
        self.response = defaultdict(list)

    def get_bbg_service_name(self):
        return '//blp/refdata'

    def get_bbg_request(self, svc, session):

        # create the bbg request object
        start, end = self.start, self.end
        request = svc.CreateRequest('IntradayBarRequest')
        request.Set('security', self.symbol)
        request.Set('interval', self.interval)
        request.Set('eventType', self.event)
        request.Set('startDateTime', session.CreateDatetime(start.year, start.month, start.day, start.hour, start.minute))
        request.Set('endDateTime', session.CreateDatetime(end.year, end.month, end.day, end.hour, end.minute))

        self.logger.info("Fetching intraday data for " + str(self.symbol) + " from "
                         + start.strftime('%d/%m/%Y') + " to " + end.strftime('%d/%m/%Y'))

        return request

    def on_event(self, evt, is_final):
        """
        on_event - This is invoked from in response to COM PumpWaitingMessages - different thread

        """

        response = self.response

        self.logger.debug("Receiving data from Bloomberg...")

        for msg in XmlHelper.message_iter(evt):
            bars = msg.GetElement('barData').GetElement('barTickData')

            self.logger.debug("Read message...")

            for i in range(bars.NumValues):
                bar = bars.GetValue(i)
                ts = bar.GetElement(0).Value

                dt = datetime(ts.year, ts.month, ts.day, ts.hour, ts.minute)

                response['time'].append(dt)
                response['open'].append(bar.GetElement(1).Value)
                response['high'].append(bar.GetElement(2).Value)
                response['low'].append(bar.GetElement(3).Value)
                response['close'].append(bar.GetElement(4).Value)
                response['volume'].append(bar.GetElement(5).Value)
                response['events'].append(bar.GetElement(6).Value)

                if (i % 20000 == 0):
                    dt_str = dt.strftime('%d/%m/%Y')
                    self.logger.debug("Processing " + dt_str)

        self.logger.debug("Finished processing for ticker.")

        if is_final:
            idx = response.pop('time')
            self.response = DataFrame(response, columns=['open', 'high', 'low', 'close', 'volume', 'events'],
                                      index=idx)
            self.response.index.name = 'Date'
            self.response = self.response.astype('float32')

class Terminal(object):

    @staticmethod
    def execute_request(request):
        session = DispatchWithEvents('blpapicom.ProviderSession.1', ResponseHandler)
        session.Start()

        try:
            svcname = request.get_bbg_service_name()

            if not session.OpenService(svcname):
                raise Exception('failed to open service %s' % svcname)

            svc = session.GetService(svcname)
            asbbg = request.get_bbg_request(svc, session)
            session.SendRequest(asbbg)
            session.do_init(request)

            while session.waiting:
                PumpWaitingMessages()

            session.has_deferred_exception and session.raise_deferred_exception()
            request.has_exception and request.raise_exception()
            return request

        finally:
            session.Stop()
            session.do_cleanup()

if __name__ == '__main__':
    #### methods to test higher level code


    #### methods to test lower level code
    # 5 days ago
    import pandas
    d = pandas.datetools.BDay(-10).apply(datetime.now())
    # d = parse("01 Jan 1998").date()
    # m = pandas.datetools.BMonthBegin(-2).apply(datetime.now())
    #
    def banner(msg):
         print(msg)

    # ov = {'START_DT':'19990101', 'END_DT':'20200101'}
    #
    # banner('ReferenceDataRequest: multi-security, multi-field')
    # req = ReferenceDataRequest(['NFP TCH Index'], ['ECO_FUTURE_RELEASE_DATE_LIST'], overrides=ov, response_type='map')
    # map = req.execute().response
    #
    # print(map)
    #
    # banner('ReferenceDataRequest: single security, single field, frame response')
    # req = ReferenceDataRequest('msft us equity', 'px_last', response_type='frame')
    # print(req.execute().response)
    #
    # banner('ReferenceDataRequest: single security, single field, frame response')
    # req = ReferenceDataRequest('msft us equity', 'px_last', response_type='frame')
    # print(req.execute().response)
    #
    # banner('ReferenceDataRequest: single security, single field, map response')
    # req = ReferenceDataRequest('msft us equity', 'px_last', response_type='map')
    # print(req.execute().response)
    #
    # banner('ReferenceDataRequest: single security, multi-field (with bulk), frame response')
    # req = ReferenceDataRequest('eurusd curncy', ['px_last', 'fwd_curve'])
    # req.execute()
    # print(req.response)
    # # DataFrame within a DataFrame
    # print(req.response.fwd_curve[0].tail())
    #
    # banner('ReferenceDataRequest: multi security, multi-field, bad field')
    # req = ReferenceDataRequest(['eurusd curncy', 'msft us equity'], ['px_last', 'fwd_curve'], ignore_field_error=1)
    # req.execute()
    # print(req.response)

    # list_tickers = ['ND1 Index', 'TY1 Comdty']
    #
    # for tick in list_tickers:
    #     banner('HistoricalDataRequest: multi security, multi-field, daily data')
    #     req = HistoricalDataRequest([tick], ['px_last'], start=d)
    #     req.execute()
    #     print(req.response)
    #     print('--------- AS SINGLE TABLE ----------')
    #     print(req.response_as_single())
    #
    # banner('HistoricalDataRequest: multi security, multi-field, daily data')
    # req = HistoricalDataRequest(['EURUSD Curncy', 'USDCAD Curncy'], ['px_last', 'px_open'], start=d)
    # req.execute()
    # print(req.response)
    # print('--------- AS SINGLE TABLE ----------')
    # print(req.response_as_single())
    #
    # banner('HistoricalDataRequest: multi security, multi-field, weekly data')
    # req = HistoricalDataRequest(['EURUSD Curncy', 'USDJPY Curncy'], ['px_last', 'px_open'], start=m, period='WEEKLY')
    # req.execute()
    # print(req.response)
    # print('--------- AS SINGLE TABLE ----------')
    # print(req.response_as_single())
    # print('--------- AS PANEL (id indexed) ----------')
    # print(req.response_as_panel())
    # print('--------- AS PANEL (field indexed) ----------')
    # print(req.response_as_panel(swap=1))

    banner('IntrdayBarRequest: every minute')
    req = IntradayBarRequest('GBPUSD Curncy', 1, start=d)
    req.execute()

    pandas = req.response
    print(req.response[10:])
    print(req.response[-10:])

    #
    # HOW TO
    #
    # - Retrieve an fx vol surface:  BbgReferenceDataRequest('eurusd curncy', 'DFLT_VOL_SURF_MID')
    # - Retrieve a fx forward curve:  BbgReferenceDataRequest('eurusd curncy', 'FWD_CURVE')
    # - Retrieve dividends:  BbgReferenceDataRequest('csco us equity', 'BDVD_PR_EX_DTS_DVD_AMTS_W_ANN')