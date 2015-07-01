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

from bokeh.plotting import figure, output_file, show

from pythalesians.graphics.graphs.lowleveladapters.adaptertemplate import AdapterTemplate
from pythalesians.util.constants import Constants

class AdapterBokeh(AdapterTemplate):

    def plot_2d_graph(self, data_frame, gp, type):
        if hasattr(gp, 'html_file_output'):
            output_file(gp.html_file_output)

        scale_factor = Constants().plotfactory_scale_factor

        if hasattr(gp, 'scale_factor'): scale_factor = gp.scale_factor

        p1 = figure(
            x_axis_type = "datetime",
            plot_width = Constants().plotfactory_width * scale_factor,
            plot_height = Constants().plotfactory_height * scale_factor,
            )

        p1.axis.major_label_text_font_size = str(10 * scale_factor) + "pt"
        p1.axis.major_label_text_font = Constants().plotfactory_bokeh_font
        p1.xaxis.axis_label_text_font_size = str(10 * scale_factor) + "pt"
        p1.xaxis.axis_label_text_font = Constants().plotfactory_bokeh_font
        p1.yaxis.axis_label_text_font_size = str(10 * scale_factor) + "pt"
        p1.yaxis.axis_label_text_font = Constants().plotfactory_bokeh_font
        p1.legend.label_text_font_size = str(10 * scale_factor) + "pt"
        p1.legend.label_text_font = Constants().plotfactory_bokeh_font

        p1.title_text_font_size = str(14 * scale_factor) + "pt"
        p1.title_text_font = Constants().plotfactory_bokeh_font

        if Constants().plotfactory_display_source:
            p1.text([30, 30], [0, 0], text = [Constants().plotfactory_brand_label],
                text_font_size = str(10 * scale_factor) + "pt", text_align = "left",
                text_font = Constants().plotfactory_bokeh_font)

        dates = data_frame.index

        for i in range(0, len(data_frame.columns)):
            if type == 'line':
                    p1.line(
                        dates,                                              # x coordinates
                        data_frame.ix[:,i],                                 # y coordinates
                        color = self.get_color_list(i),                     # set a color for the line
                        legend = data_frame.columns[i],                     # attach a legend label
                    )

        p1.legend.border_line_width = 0
        p1.legend.label_text_font = Constants().plotfactory_bokeh_font

        try:
            p1.title = gp.title
        except: pass

        p1.grid.grid_line_alpha = 0.3

        show(p1)  # open a browser

    def get_color_list(self, i):
        color_palette = Constants().plotfactory_bokeh_palette

        return color_palette[i % len(color_palette)]

    def generic_settings(self):
        return