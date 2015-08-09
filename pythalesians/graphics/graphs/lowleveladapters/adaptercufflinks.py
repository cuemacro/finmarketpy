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
AdapterCufflinks

Wrapper for Jorge Santos' Cufflinks library for plotting a multitude of charts to Plotly, using the same interface
as for PyThalesians (Matplotlib) charts.

"""

import plotly
import datetime

from pythalesians.util.constants import Constants

cf = None

try:
    import cufflinks as cf
except: pass

from pythalesians.graphics.graphs.lowleveladapters.adaptertemplate import AdapterTemplate

class AdapterCufflinks(AdapterTemplate):

    def plot_2d_graph(self, data_frame, gp, type):
        plotly.tools.set_credentials_file(username=gp.plotly_username, api_key=gp.plotly_api_key)

        mode = 'line'

        marker_size = 1
        scale_factor = gp.scale_factor

        x = ''; y = ''; z = ''

        if type == 'line':
            type = 'scatter'
        elif type == 'scatter':
            mode = 'markers'
            marker_size = 5
        elif type == 'bubble':
            x = data_frame.columns[0]
            y = data_frame.columns[1]
            z = data_frame.columns[2]

        # check other plots implemented by Cufflinks

        # get all the correct colors (and construct gradients if necessary eg. from 'blues')
        # need to change to strings for cufflinks
        color_spec = []
        color_list = self.create_color_list(gp, data_frame)

        # if no colors are specified strip the list
        if color_list == [None] * len(color_list):
            color_spec = None

        else:
            # otherwise assume all the colors are rgba
            for color in color_list:
                color = 'rgba' + str(color)
                color_spec.append(color)

        data_frame.iplot(kind=type,
            filename=gp.plotly_url,
            title=gp.title,
            xTitle=gp.x_title,
            yTitle=gp.y_title,
            x=x, y=y, z=z,
            mode=mode,
            size=marker_size,
            theme=gp.plotly_theme,
            bestfit=gp.line_of_best_fit,
            world_readable=gp.plotly_world_readable,
            legend=gp.display_legend,
            color = color_spec,
            dimensions=(gp.width * scale_factor, gp.height * scale_factor),
            asPlot=not(gp.silent_display),
            asImage=gp.plotly_as_image)
