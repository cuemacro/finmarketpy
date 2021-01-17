__author__ = 'saeedamen'  # Saeed Amen

#
# Copyright 2016-2020 Cuemacro - https://www.cuemacro.com / @cuemacro
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the
# License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the License for the specific language governing permissions and limitations under the License.
#

import abc

import numpy as np

ABC = abc.ABCMeta('ABC', (object,), {'__slots__': ()})

from financepy.finutils.FinDate import FinDate

class AbstractVolSurface(ABC):
    """Holds data for an asset class vol surface

    """

    @abc.abstractmethod
    def build_vol_surface(self):
        return

    @abc.abstractmethod
    def extract_vol_surface(self):
        return

    def _extremes(self, min, max, data):
        if min is None:
            min = np.min(data)
        else:
            new_min = np.min(data)

            if new_min < min:
                min = new_min

        if max is None:
            max = np.max(data)
        else:
            new_max = np.max(data)

            if new_max > max:
                max = new_max

        return min, max

    def extract_vol_surface_across_dates(self, dates,
                                         num_strike_intervals=60, vol_surface_type='vol_surface_strike_space',
                                         reverse_plot=True):

        vol_surface_dict = {}

        min_x = None
        max_x = None
        min_z = None
        max_z = None

        for i in range(0, len(dates)):

            self.build_vol_surface(dates[i])

            # Note for unstable vol surface dates (eg. over Brexit date) you may need to increase tolerance
            # in FinancePy
            # in FinFXVolSurface.buildVolSurface method
            df_vol_surface = self.extract_vol_surface(num_strike_intervals=num_strike_intervals)[vol_surface_type]

            if reverse_plot:
                # Reverse order of tenors to match the way BBG plots it
                vol_surface_dict[dates[i]] = df_vol_surface.iloc[:, ::-1]
            else:
                vol_surface_dict[dates[i]] = df_vol_surface

            # x_axis = strike - index
            # y_axis = tenor - columns
            # z_axis = implied_vol vol - values
            min_x, max_x = self._extremes(min_x, max_x, df_vol_surface.index.values)
            min_z, max_z = self._extremes(min_z, max_z, df_vol_surface.values)

        extremes_dict = {'min_x': min_x, 'max_x': max_x, 'min_z': min_z, 'max_z': max_z}

        return vol_surface_dict, extremes_dict

    def _get_tenor_index(self, tenor):
        return self._tenors.index(tenor)

    def _findate(self, date):
        return FinDate(date.day, date.month, date.year)