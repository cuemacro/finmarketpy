_author__ = 'saeedamen'

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
CreateDataIndexTemplate

Template for construction of custom indices.

"""

import abc

from pythalesians.util.configmanager import ConfigManager
from pythalesians.util.loggermanager import LoggerManager
from pythalesians.timeseries.calcs.timeseriesfilter import TimeSeriesFilter

class CreateDataIndexTemplate:

    def __init__(self):
        self.config = ConfigManager()
        self.logger = LoggerManager().getLogger(__name__)
        return

    @abc.abstractmethod
    def create_indicator(self):
        return

    @abc.abstractmethod
    def aggregate_news_data(self, raw_database):
        return

    @abc.abstractmethod
    def get_cached_aggregate(self):
        return

    def grab_indicator(self):
        return self.indicator

    def grab_econ_indicator(self):
        return self.indicator_econ

    def grab_final_indicator(self):
        return self.indicator_final

    def truncate_indicator(self, daily_ind, match):
        cols = daily_ind.columns.values

        to_include = []

        for i in range(0, len(cols)):
            if match in cols[i]:
                to_include.append(i)

        return daily_ind[daily_ind.columns[to_include]]

    def dump_indicators(self):
        tsf = TimeSeriesFilter()
        self.logger.info("About to write all indicators to CSV")
        self.indicator.to_csv(self._csv_indicator_dump, date_format='%d/%m/%Y')

        if (self._csv_econ_indicator_dump is not None):
            self.logger.info("About to write economy based indicators to CSV")
            self.indicator_econ.to_csv(self._csv_econ_indicator_dump, date_format='%d/%m/%Y')

        self.logger.info("About to write final indicators to CSV")

        # remove weekends and remove start of series
        if (self._csv_final_indicator_dump is not None):
            indicator_final_copy = tsf.filter_time_series_by_holidays(self.indicator_final, cal = 'WEEKDAY')
            indicator_final_copy = tsf.filter_time_series_by_date(
                start_date="01 Jan 2000", finish_date = None, data_frame=indicator_final_copy)

            indicator_final_copy.to_csv(self._csv_final_indicator_dump, date_format='%d/%m/%Y')




