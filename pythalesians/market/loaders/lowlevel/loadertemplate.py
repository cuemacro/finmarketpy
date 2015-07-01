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
LoaderTemplate

Abstract class for various data source loaders.

"""

import abc
import copy

from pythalesians.util.constants import Constants

class LoaderTemplate:
    def __init__(self):

        if Constants().default_time_series_factory == "cachedtimeseriesfactory":
            from pythalesians.util.configmanager import ConfigManager
            self.config = ConfigManager()

        return

    @abc.abstractmethod
    def load_ticker(self, time_series_request):
        """
        load_ticker - Retrieves market data from external data source

        Parameters
        ----------
        time_series_request : TimeSeriesRequest
            contains all the various parameters detailing time series start and finish, tickers etc

        Returns
        -------
        DataFrame
        """

        return

        # to be implemented by subclasses

    @abc.abstractmethod
    def kill_session(self):
        return

    def construct_vendor_time_series_request(self, time_series_request):
        """
        construct_vendor_time_series_request - creates a TimeSeriesRequest with the vendor tickers

        Parameters
        ----------
        time_series_request : TimeSeriesRequest
            contains all the various parameters detailing time series start and finish, tickers etc

        Returns
        -------
        TimeSeriesRequest
        """

        symbols_vendor = self.translate_to_vendor_ticker(time_series_request)
        fields_vendor = self.translate_to_vendor_field(time_series_request)

        time_series_request_vendor = copy.copy(time_series_request)

        time_series_request_vendor.tickers = symbols_vendor
        time_series_request_vendor.fields = fields_vendor

        return time_series_request_vendor

    def translate_to_vendor_field(self, time_series_request):
        """
        translate_to_vendor_field - Converts all the fields from Thalesians fields to vendor fields

        Parameters
        ----------
        time_series_request : TimeSeriesRequest
            contains all the various parameters detailing time series start and finish, tickers etc

        Returns
        -------
        List of Strings
        """

        if hasattr(time_series_request, 'vendor_fields'):
            return time_series_request.vendor_fields

        source = time_series_request.data_source
        fields_list = time_series_request.fields

        if isinstance(fields_list, str):
            fields_list = [fields_list]

        if self.config is None: return fields_list

        fields_converted = []

        for field in fields_list:
            fields_converted.append(self.config.convert_library_to_vendor_field(source, field))

        return fields_converted

    # translate Thalesians ticker to vendor ticker
    def translate_to_vendor_ticker(self, time_series_request):
        """
        translate_to_vendor_tickers - Converts all the tickers from Thalesians tickers to vendor tickers

        Parameters
        ----------
        time_series_request : TimeSeriesRequest
            contains all the various parameters detailing time series start and finish, tickers etc

        Returns
        -------
        List of Strings
        """

        if hasattr(time_series_request, 'vendor_tickers'):
            return time_series_request.vendor_tickers

        category = time_series_request.category
        source = time_series_request.data_source
        freq = time_series_request.freq
        cut = time_series_request.cut
        tickers_list = time_series_request.tickers

        if isinstance(tickers_list, str):
            tickers_list = [tickers_list]

        if self.config is None: return tickers_list

        tickers_list_converted = []

        for ticker in tickers_list:
            tickers_list_converted.append(
                self.config.convert_library_to_vendor_ticker(category, source, freq, cut, ticker))

        return tickers_list_converted

    def translate_from_vendor_field(self, vendor_fields_list, time_series_request):
        """
        translate_from_vendor_field - Converts all the fields from vendors fields to Thalesians fields

        Parameters
        ----------
        time_series_request : TimeSeriesRequest
            contains all the various parameters detailing time series start and finish, tickers etc

        Returns
        -------
        List of Strings
        """

        data_source = time_series_request.data_source

        if isinstance(vendor_fields_list, str):
            vendor_fields_list = [vendor_fields_list]

        # if self.config is None: return vendor_fields_list

        fields_converted = []

        # if we haven't set the configuration files for automatic configuration
        if hasattr(time_series_request, 'vendor_fields'):

            dictionary = dict(zip(time_series_request.vendor_fields, time_series_request.fields))

            for vendor_field in vendor_fields_list:
                try:
                    fields_converted.append(dictionary[vendor_field])
                except:
                    fields_converted.append(vendor_field)

        # otherwise used stored configuration files
        else:
            for vendor_field in vendor_fields_list:
                fields_converted.append(self.config.convert_vendor_to_library_field(data_source, vendor_field))

        return fields_converted

    # translate Thalesians ticker to vendor ticker
    def translate_from_vendor_ticker(self, vendor_tickers_list, time_series_request):
        """
        translate_from_vendor_ticker - Converts all the fields from vendor tickers to Thalesians tickers

        Parameters
        ----------
        time_series_request : TimeSeriesRequest
            contains all the various parameters detailing time series start and finish, tickers etc

        Returns
        -------
        List of Strings
        """

        if hasattr(time_series_request, 'vendor_tickers'):

            dictionary = dict(zip(time_series_request.vendor_tickers, time_series_request.tickers))

            tickers_stuff = []

            for vendor_ticker in vendor_tickers_list:
                tickers_stuff.append(dictionary[vendor_ticker])

            return tickers_stuff # [item for sublist in tickers_stuff for item in sublist]

        data_source = time_series_request.data_source
        # tickers_list = time_series_request.tickers

        if isinstance(vendor_tickers_list, str):
            vendor_tickers_list = [vendor_tickers_list]

        if self.config is None: return vendor_tickers_list

        tickers_converted = []

        for vendor_ticker in vendor_tickers_list:
            tickers_converted.append(
                self.config.convert_vendor_to_library_ticker(data_source, vendor_ticker))

        return tickers_converted