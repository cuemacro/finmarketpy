__author__ = 'saeedamen'  # Saeed Amen

#
# Copyright 2016-2020 Cuemacro - https://www.cuemacro.com / @cuemacro
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.
#

import abc

class AbstractCurve(object):
    """Abstract class for creating total return indices and curves, which is for example implemented by FXSpotCurve
    and could be implemented by other asset classes.

    """

    @abc.abstractmethod
    def generate_key(self):
        return

    @abc.abstractmethod
    def fetch_continuous_time_series(self, md_request, market_data_generator):
        return

    @abc.abstractmethod
    def construct_total_returns_index(self):
        return
