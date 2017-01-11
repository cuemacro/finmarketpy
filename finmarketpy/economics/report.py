__author__ = 'saeedamen' # Saeed Amen

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

import pandas

from chartpy import Chart, Style
from findatapy.timeseries.calculations import Calculations
from findatapy.util.dataconstants import DataConstants

calculations = Calculations()

class Report(object):
    """Creates simple statistical reports (via plots) on time series, outputting results

    """

    def report_single_var_regression(self, y, x, y_variable_names, x_variable_names, statistic,
                                          pretty_index = None):


        if not(isinstance(statistic, list)): statistic = [statistic]

        # conduct the regression
        stats = Calculations.linear_regression_single_vars(y, x, y_variable_names, x_variable_names)

        if pretty_index is None: pretty_index = x_variable_names

        # strip out the field(s) from the regression output which we want
        stats_df = Calculations.strip_linear_regression_output(pretty_index, stats, statistic)
        # stats_df = stats_df.sort_index()

        return stats_df


    def plot_single_var_regression(self, y, x, y_variable_names, x_variable_names, statistic,
                                   tag = 'stats',
                                   title = None,
                                   pretty_index = None, output_path = None,
                                   scale_factor = None,
                                   silent_plot = False,
                                   shift=[0]):

        if not(isinstance(statistic, list)):
            statistic = [statistic]

        # TODO optimise loop so that we are calculating each regression *once* at present calculating it
        # for each statistic, which is redundant
        for st in statistic:
            stats_df = []

            for sh in shift:
                x_sh = x.shift(sh)
                stats_temp = self.report_single_var_regression(y, x_sh, y_variable_names, x_variable_names, st,
                                                             pretty_index)

                stats_temp.columns = [ x + "_" + str(sh) for x in stats_temp.columns]

                stats_df.append(stats_temp)

            stats_df = pandas.concat(stats_df, axis=1)
            stats_df = stats_df.dropna(how='all')

            if silent_plot: return stats_df

            chart = Chart()
            style = Style()

            if title is None: title = statistic

            style.title = title
            style.display_legend = True
            style.scale_factor = scale_factor
            # style.color = ['red', 'blue', 'purple', 'gray', 'yellow', 'green', 'pink']

            if output_path is not None:
                style.file_output = output_path + ' (' + tag + ' ' + st + ').png'

            chart.plot(stats_df, style=style)

        return stats_df
