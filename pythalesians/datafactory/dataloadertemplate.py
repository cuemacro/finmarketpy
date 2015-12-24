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
DataLoaderTemplate

Template for loading of datasets and pushing into HDF5 format.

"""

import os.path
import abc

from pythalesians.util.configmanager import ConfigManager
from pythalesians.util.loggermanager import LoggerManager
from pythalesians.timeseries.calcs.timeseriescalcs import TimeSeriesCalcs
from pythalesians.market.loaders.timeseriesio import TimeSeriesIO

class DataLoaderTemplate:

    def __init__(self):
        self.config = ConfigManager()
        self.logger = LoggerManager().getLogger(__name__)
        return

    def load_database(self, key = None):
        tsio = TimeSeriesIO()
        tsc = TimeSeriesCalcs()

        file = self._hdf5

        if key is not None:
            file = self._hdf5 + key + ".h5"

        # if cached file exists, use that, otherwise load CSV
        if os.path.isfile(file):
            self.logger.info("About to load market database from HDF5...")
            self.news_database = tsio.read_time_series_cache_from_disk(file)
            self.news_database = self.preprocess(self.news_database)
        else:
            self.logger.info("About to load market database from CSV...")
            self.news_database = self.load_csv()

        return self.news_database

    @abc.abstractmethod
    def load_csv(self):
        return

    def get_database(self, key):
        return self.news_database

    @abc.abstractmethod
    def preprocess(self, df):
        return
