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
AdapterSeaborn

Wrapper for Seaborn (matplotlib) for charting, with an easier to use common interface. Note, just a skeleton of code at
present.

"""

from pythalesians.graphics.graphs.lowleveladapters.adapterpythalesians import AdapterPyThalesians
from pythalesians.graphics.graphs.graphproperties import GraphProperties

import seaborn as sns

class AdapterSeaborn(AdapterPyThalesians):

    def plot_2d_graph(self, data_frame, gp, chart_type):
        sns.set()

        if gp is None: gp = GraphProperties()
        if gp.chart_type is None and chart_type is None: chart_type = 'line'

        if gp.resample is not None: data_frame = data_frame.asfreq(gp.resample)

        self.apply_style_sheet(gp)

        if chart_type == 'heatmap':
            # Draw a heatmap with the numeric values in each cell
            sns_plot = sns.heatmap(data_frame, annot=True, fmt="d", linewidths=.5)

            fig = sns_plot.fig

        # TODO
        pass