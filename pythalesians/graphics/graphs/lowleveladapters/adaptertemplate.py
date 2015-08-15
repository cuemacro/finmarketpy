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

import abc

from math import log10, floor
from pythalesians.util.constants import Constants

import matplotlib
import numpy

class AdapterTemplate:

    def init(self):
        return

    @abc.abstractmethod
    def plot_2d_graph(self, data_frame, gp, type):
        return


    def get_bar_indices(self, data_frame, gp, chart_type, bar_ind):
        has_bar = False
        xd = data_frame.index
        no_of_bars = len(data_frame.columns)

        if chart_type is not None:
            if gp.chart_type is not None:
                if isinstance(gp.chart_type, list):
                    if 'bar' in gp.chart_type:
                        xd = bar_ind
                        no_of_bars = gp.chart_type.count('bar')
                        has_bar = True
                elif 'bar' == gp.chart_type:
                    xd = bar_ind
                    has_bar = True

            if chart_type == 'bar':
                xd = bar_ind
                has_bar = True

        return xd, bar_ind, has_bar, no_of_bars

    def assign(self, structure, field, default):
        if hasattr(structure, field): default = getattr(structure, field)

        return default

    def assign_list(self, gp, field, list):
        if hasattr(gp, field):
            list = [str(x) for x in getattr(gp, field)]

        return list

    def get_linewidth(self, label, linewidth_1, linewidth_2, linewidth_2_series):
        if label in linewidth_2_series:
            return linewidth_2

        return linewidth_1

    def round_to_1(self, x):
        return round(x, -int(floor(log10(x))))

    def create_color_list(self, gp, data_frame):
        # get all the correct colors (and construct gradients if necessary eg. from 'blues')
        color = self.construct_color(gp, 'color', len(data_frame.columns.values) - len(gp.color_2_series))
        color_2 = self.construct_color(gp, 'color_2', len(gp.color_2_series))

        return self.assign_color(data_frame.columns, color, color_2,
                                 gp.exclude_from_color, gp.color_2_series)

    def construct_color(self, gp, color_field_name, no_of_entries):
        color = []

        if hasattr(gp, color_field_name):
            if isinstance(getattr(gp, color_field_name), list):
                color = getattr(gp, color_field_name, color)
            else:
                try:
                    color = self.create_colormap(no_of_entries, getattr(gp, color_field_name))
                except: pass

        return color

    def exclude_from_color(self, gp):
        if not(isinstance(gp.exclude_from_color, list)):
            gp.exclude_from_color = [gp.exclude_from_color]

        exclude_from_color = [str(x) for x in gp.exclude_from_color]

        return exclude_from_color

    def assign_color(self, labels, color, color_2, exclude_from_color,
                  color_2_series):

        color_list = []

        axis_1_color_index = 0; axis_2_color_index = 0

        # convert all the labels to strings
        labels = [str(x) for x in labels]

        # go through each label
        for label in labels:
            color_spec = None

            if label in exclude_from_color:
                color_spec = None

            elif label in color_2_series:
                if color_2 != []:
                    color_spec = self.get_color_code(color_2[axis_2_color_index])
                    axis_2_color_index = axis_2_color_index + 1

            else:
                if color != []:
                    color_spec = self.get_color_code(color[axis_1_color_index])
                    axis_1_color_index = axis_1_color_index + 1

            try:
                color_spec = matplotlib.colors.colorConverter.to_rgba(color_spec)
            except:
                pass

            color_list.append(color_spec)

        return color_list

    def get_color_code(self, code):
        # redefine color names
        dict = Constants().plotfactory_color_overwrites

        if code in dict: return dict[code]

        return code

    def create_colormap(self, num_colors, map_name):
        ## matplotlib ref for colors: http://matplotlib.org/examples/color/colormaps_reference.html
        cm = matplotlib.cm.get_cmap(name = map_name)

        return [cm(1.*i/num_colors) for i in range(num_colors)]