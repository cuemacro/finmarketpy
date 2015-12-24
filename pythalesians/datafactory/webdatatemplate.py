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
WebDataTemplate

Template for construction of indices from web data.

"""

from pythalesians.util.configmanager import ConfigManager
from pythalesians.util.loggermanager import LoggerManager
import abc

class WebDataTemplate:

    def __init__(self):
        self.config = ConfigManager()
        self.logger = LoggerManager().getLogger(__name__)
        return

    @abc.abstractmethod
    def download_raw_data(self):
        return

    @abc.abstractmethod
    def construct_indicator(self):
        return

    def dump_indicator(self):

        indicator_group = self.raw_indicator # self.raw_indicator.join(self.processed_indicator, how='outer')

        self.logger.info("About to write all web indicators")
        indicator_group.to_csv(self._csv_indicator_dump, date_format='%d/%m/%Y %H:%M:%S')