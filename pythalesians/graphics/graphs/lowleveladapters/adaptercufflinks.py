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

import plotly.plotly

from pythalesians.graphics.graphs.lowleveladapters.adaptertemplate import AdapterTemplate
from pythalesians.graphics.graphs.graphproperties import GraphProperties

class AdapterCufflinks(AdapterTemplate):

    def plot_2d_graph(self, data_frame, gp, chart_type):

        mode = 'line'

        if gp is None: gp = GraphProperties()

        if gp.chart_type is None:
            if chart_type is None: chart_type = 'line'
        else:
            chart_type = gp.chart_type

        marker_size = 1

        x = ''; y = ''; z = ''
        fig = None

        if chart_type == 'line':
            chart_type = 'scatter'
        elif chart_type == 'scatter':
            mode = 'markers'
            marker_size = 5
        elif chart_type == 'bubble':
            x = data_frame.columns[0]
            y = data_frame.columns[1]
            z = data_frame.columns[2]

        # special case for choropleth which has yet to be implemented in Cufflinks
        # will likely remove this in the future
        elif chart_type == 'choropleth':
            import plotly.plotly as py

            for col in data_frame.columns:
                try:
                    data_frame[col] = data_frame[col].astype(str)
                except:
                    pass

            if gp.color != []:
                color = gp.color
            else:
                color = [[0.0, 'rgb(242,240,247)'],[0.2, 'rgb(218,218,235)'],[0.4, 'rgb(188,189,220)'],\
                [0.6, 'rgb(158,154,200)'],[0.8, 'rgb(117,107,177)'],[1.0, 'rgb(84,39,143)']]

            text = ''

            if 'text' in data_frame.columns:
                text = data_frame['Text']

            data = [ dict(
                    type='choropleth',
                    colorscale = color,
                    autocolorscale = False,
                    locations = data_frame['Code'],
                    z = data_frame[gp.plotly_choropleth_field].astype(float),
                    locationmode = gp.plotly_location_mode,
                    text = text,
                    marker = dict(
                        line = dict (
                            color = 'rgb(255,255,255)',
                            width = 1
                        )
                    ),
                    colorbar = dict(
                        title = gp.units
                    )
                ) ]

            layout = dict(
                    title = gp.title,
                    geo = dict(
                        scope=gp.plotly_scope,
                        projection=dict( type=gp.plotly_projection ),
                        showlakes = True,
                        lakecolor = 'rgb(255, 255, 255)',
                    ),
                )

            fig = dict( data=data, layout=layout )

        # check other plots implemented by Cufflinks

        if fig is None:

            # special case for surface (given coloring)
            if chart_type == 'surface':
                # create figure
                fig = data_frame.iplot(kind=chart_type,
                    title=gp.title,
                    xTitle=gp.x_title,
                    yTitle=gp.y_title,
                    x=x, y=y, z=z,
                    mode=mode,
                    size=marker_size,
                    theme=gp.plotly_theme,
                    bestfit=gp.line_of_best_fit,
                    legend=gp.display_legend,
                    colorscale=gp.color,
                    dimensions=(gp.width * gp.scale_factor * 2/3, gp.height * gp.scale_factor * 2/3),
                    asFigure=True)
            else:
                # get all the correct colors (and construct gradients if necessary eg. from 'Blues')
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

                # create figure
                fig = data_frame.iplot(kind=chart_type,
                    title=gp.title,
                    xTitle=gp.x_title,
                    yTitle=gp.y_title,
                    x=x, y=y, z=z,
                    mode=mode,
                    size=marker_size,
                    theme=gp.plotly_theme,
                    bestfit=gp.line_of_best_fit,
                    legend=gp.display_legend,
                    color=color_spec,
                    dimensions=(gp.width * gp.scale_factor * 2/3, gp.height * gp.scale_factor * 2/3),
                    asFigure=True)

        self.publish_plot(fig, gp)

    def publish_plot(self, fig, gp):

        if gp.plotly_plot_mode == 'online':
            plotly.tools.set_credentials_file(username=gp.plotly_username, api_key=gp.plotly_api_key)

            plotly.plotly.plot(fig, filename=gp.plotly_url,
                    world_readable=gp.plotly_world_readable,
                    auto_open = not(gp.silent_display),
                    asImage=gp.plotly_as_image)

        elif gp.plotly_plot_mode == 'offline_html':
            if gp.html_file_output is not None:
                temp_html = gp.html_file_output
            else:
                temp_html = "temp.html"

            plotly.offline.plot(fig, filename=temp_html, auto_open = not(gp.silent_display))

        elif gp.plotly_plot_mode == 'offline_jupyter':

            # plot in IPython notebook
            plotly.offline.init_notebook_mode()
            plotly.offline.iplot(fig)

        # plotly.offline.plot(fig, filename=gp.file_output, format='png',
        #         width=gp.width * gp.scale_factor, height=gp.height * gp.scale_factor)
        try:
            plotly.plotly.image.save_as(fig, filename=gp.file_output, format='png',
                                width=gp.width * gp.scale_factor, height=gp.height * gp.scale_factor)
        except: pass
