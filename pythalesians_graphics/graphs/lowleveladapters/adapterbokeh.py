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
AdapterBokeh

Wrapper for Bokeh to plot graph, with an easier to use common interface. Only provides very basic implementation of
simple line charts currently, as a proof of concept.

"""

import numpy
import pandas
from bokeh.plotting import figure, output_file, show

from pythalesians_graphics.graphs.lowleveladapters.adaptertemplate import AdapterTemplate
from pythalesians_graphics.graphs.graphproperties import GraphProperties
from pythalesians.util.constants import Constants


class AdapterBokeh(AdapterTemplate):

    def plot_2d_graph(self, data_frame, gp, chart_type):

        if gp is None: gp = GraphProperties()

        if gp.chart_type is None and chart_type is None: chart_type = 'line'

        scale_factor = gp.scale_factor

        try:
            if gp.bokeh_plot_mode == "offline_jupyter":
                from bokeh.io import output_notebook
                output_notebook()
        except:
            pass

        try:
            html = gp.html_file_output
            if (html is None):
                html = "bokeh.htm"

            output_file(html)
        except: pass

        bar_ind = numpy.arange(1, len(data_frame.index) + 1)

        xd, bar_ind, has_bar, no_of_bars = self.get_bar_indices(data_frame, gp, chart_type, bar_ind)

        if type(data_frame.index) == pandas.tslib.Timestamp:
            p1 = figure(
                x_axis_type = "datetime",
                plot_width = int(gp.width * scale_factor),
                plot_height = int(gp.height * scale_factor),
                x_range=(xd[0], xd[-1])
                )

        # if has a bar than categorical axis
        elif has_bar == True:
            p1 = figure(
                plot_width = int(gp.width * scale_factor),
                plot_height = int(gp.height * scale_factor),
                x_range=[str(x) for x in data_frame.index]
                )

            from math import pi
            p1.xaxis.major_label_orientation = pi/2

        # otherwise numerical axis
        else:
            p1 = figure(
                plot_width = int(gp.width * scale_factor),
                plot_height = int(gp.height * scale_factor),
                x_range=(xd[0], xd[-1])
                )

        # set the fonts
        p1.axis.major_label_text_font_size = str(10 * scale_factor) + "pt"
        p1.axis.major_label_text_font = Constants().bokeh_font
        p1.axis.major_label_text_font_style = Constants().bokeh_font_style

        p1.xaxis.axis_label_text_font_size = str(10 * scale_factor) + "pt"
        p1.xaxis.axis_label_text_font = Constants().bokeh_font
        p1.xaxis.axis_label_text_font_style = Constants().bokeh_font_style
        p1.xaxis.axis_label = gp.x_title

        p1.yaxis.axis_label_text_font_size = str(10 * scale_factor) + "pt"
        p1.yaxis.axis_label_text_font = Constants().bokeh_font
        p1.yaxis.axis_label_text_font_style = Constants().bokeh_font_style
        p1.yaxis.axis_label = gp.y_title

        p1.legend.label_text_font_size = str(10 * scale_factor) + "pt"
        p1.legend.label_text_font = Constants().bokeh_font
        p1.legend.label_text_font_style = Constants().bokeh_font_style
        p1.legend.fill_alpha = 0

        # set chart outline
        p1.outline_line_width = 0

        p1.title_text_font_size = str(14 * scale_factor) + "pt"
        p1.title_text_font = Constants().bokeh_font

        # TODO fix label
        # if gp.display_source_label:
        #     p1.text([30 * scale_factor, 30 * scale_factor], [0, 0], text = [gp.brand_label],
        #         text_font_size = str(10 * scale_factor) + "pt", text_align = "left",
        #         text_font = Constants().bokeh_font)

        color_spec = self.create_color_list(gp, data_frame)
        import matplotlib

        bar_space = 0.2
        bar_width = (1 - bar_space) / (no_of_bars)
        bar_index = 0

        has_bar = False

        # plot each series in the dataframe separately
        for i in range(0, len(data_frame.columns)):
            label = str(data_frame.columns[i])
            glyph_name = 'glpyh' + str(i)

            # set chart type which can differ for each time series
            if chart_type is not None:
                if gp.chart_type is not None:
                    if isinstance(gp.chart_type, list): chart_type = gp.chart_type[i]
                    else: chart_type = gp.chart_type

            # get the color
            if color_spec[i] is None:
                color_spec[i] = self.get_color_list(i)

            try:
                color_spec[i] = matplotlib.colors.rgb2hex(color_spec[i])
            except: pass

            yd = data_frame.ix[:,i]

            # plot each time series as appropriate line, scatter etc.
            if chart_type == 'line':
                linewidth_t = self.get_linewidth(label,
                    gp.linewidth, gp.linewidth_2, gp.linewidth_2_series)

                if linewidth_t is None: linewidth_t = 1

                if gp.display_legend:
                    p1.line(xd, yd, color = color_spec[i], line_width=linewidth_t, name = glyph_name,
                            legend = label,
                    )
                else:
                    p1.line(xd, data_frame.ix[:,i], color = color_spec[i], line_width=linewidth_t, name = glyph_name)

            elif(chart_type == 'bar'):
                bar_pos = [k - (1 - bar_space) / 2. + bar_index * bar_width for k in range(1,len(bar_ind) + 1)]
                bar_pos_right = [x + bar_width for x in bar_pos]

                if gp.display_legend:
                    p1.quad(top=yd, bottom=0 * yd, left=bar_pos, right=bar_pos_right, color=color_spec[i], legend=label)
                else:
                    p1.quad(top=yd, bottom=0 * yd, left=bar_pos, right=bar_pos_right, color=color_spec[i])

                bar_index = bar_index + 1
                bar_ind = bar_ind + bar_width

            elif chart_type == 'scatter':
                linewidth_t = self.get_linewidth(label,
                    gp.linewidth, gp.linewidth_2, gp.linewidth_2_series)

                if linewidth_t is None: linewidth_t = 1

                if gp.display_legend:
                    p1.circle(xd, yd, color = color_spec[i], line_width=linewidth_t, name = glyph_name,
                            legend = label,
                    )
                else:
                    p1.circle(xd, yd, color = color_spec[i], line_width=linewidth_t, name = glyph_name)

            # set common properties
            # glyph = p1.select(name=glyph_name)[0].glyph

        try:
            p1.title = gp.title
        except: pass

        p1.grid.grid_line_alpha = 0.3

        show(p1)  # open a browser

    def get_color_list(self, i):
        color_palette = Constants().bokeh_palette

        return color_palette[i % len(color_palette)]

    def generic_settings(self):
        return