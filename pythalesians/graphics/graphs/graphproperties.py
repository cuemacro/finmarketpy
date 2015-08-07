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


"""
GraphProperties

Properties for graphs plotted in the PlotFactory. Defined properties for every field.

"""

from pythalesians.util.loggermanager import LoggerManager
from pythalesians.util.constants import Constants

import datetime

class GraphProperties:

    # TODO explicitly add fields (and do error checking)
    def __init__(self,
        # captions
        title = '',
	    x_title = '',
	    y_title = '',

        # colors
        color = [],
        color_2 = [],
        color_2_series = [],
        exclude_from_color = [],

        # display sizes
        scale_factor = Constants().plotfactory_scale_factor,
        dpi = Constants().plotfactory_dpi,
        width = Constants().plotfactory_width,
        height = Constants().plotfactory_height,
        resample = None,

        # lines and multiple y-axis
        y_axis_2_series = [],
        linewidth_2_series = [],
        linewidth = None,
        linewidth_2 = None,
    	marker_size = 1,
        line_of_best_fit = False,

        # labelling of sources
        brand_label = Constants().plotfactory_brand_label,
        display_brand_label = Constants().plotfactory_display_brand_label,
        source = Constants().plotfactory_source,
        source_color = 'black',
        display_source_label =  Constants().plotfactory_display_source_label,
        display_legend = False,

        # display output
        silent_display = False,
        file_output = None,
        date_formatter = None,

        # output
        html_file_output = None,
        display_mpld3 = False,

        # plotly only
        plotly_url = None,
        plotly_as_image = False,
        plotly_username = Constants().plotly_default_username,
        plotly_api_key = None,
        plotly_world_readable = False,
        plotly_theme = None,

        # matplotlib only
        style_sheet = Constants().plotfactory_default_stylesheet,
        convert_matplotlib_to_plotly = False
                 ):

        self.logger = LoggerManager().getLogger(__name__)

        # captions
        self.title = title
        self.x_title = x_title
        self.y_title = y_title

        # colors
        self.color = color
        self.color_2 = color_2
        self.color_2_series = color_2_series
        self.exclude_from_color = exclude_from_color

        # display sizes
        self.scale_factor = scale_factor
        self.dpi = dpi
        self.width = width
        self.height = height
        self.resample = resample

        # lines and multiple y-axis
        self.y_axis_2_series = y_axis_2_series
        self.linewidth_2_series = linewidth_2_series
        self.linewidth = linewidth
        self.linewidth_2 = linewidth_2
        self.marker_size = marker_size
        self.line_of_best_fit = line_of_best_fit

        # labelling of sources
        self.brand_label = brand_label
        self.display_brand_label = display_brand_label
        self.source = source
        self.source_color = source_color
        self.display_source_label = display_source_label
        self.display_legend = display_legend

        # display output
        self.silent_display = silent_display
        self.file_output = file_output
        self.date_formatter = date_formatter

        # output
        self.html_file_output = html_file_output
        self.display_mpld3 = display_mpld3

        # plotly only
        if plotly_url is None:
            plotly_url = title + datetime.datetime.utcnow().strftime("%b-%d-%Y-%H-%M-%S")

        self.plotly_url = plotly_url
        self.plotly_as_image = plotly_as_image
        self.plotly_username = plotly_username

        # try to get API key from constants file
        try:
            if plotly_api_key is None: plotly_api_key = Constants().plotly_creds[plotly_username]
        except: pass

        self.plotly_api_key = plotly_api_key
        self.plotly_world_readable = plotly_world_readable
        self.plotly_theme = plotly_theme

        # matplotlib only
        self.style_sheet = style_sheet
        self.convert_matplotlib_to_plotly = convert_matplotlib_to_plotly

    def str_list(self, original):
        if isinstance(original, list):
            original = [str(x) for x in original]

        return original
    
    ##### general captions   
    @property
    def title(self): return self.__title
    @title.setter
    def title(self, title): self.__title = title
    
    @property
    def x_title(self): return self.__x_title
    @x_title.setter
    def x_title(self, x_title): self.__x_title = x_title
    
    @property
    def y_title(self): return self.__y_title
    @y_title.setter
    def y_title(self, y_title): self.__y_title = y_title 

    ###### colors
    @property
    def color(self): return self.__color
    @color.setter
    def color(self, color): self.__color = color

    @property
    def color_2(self): return self.__color_2
    @color_2.setter
    def color_2(self, color_2): self.__color_2 = color_2 
    
    @property
    def color_2_series(self): return self.__color_2_series
    @color_2_series.setter
    def color_2_series(self, color_2_series): self.__color_2_series = self.str_list(color_2_series)

    @property
    def exclude_from_color(self): return self.__exclude_from_color
    @exclude_from_color.setter
    def exclude_from_color(self, exclude_from_color): self.__exclude_from_color = self.str_list(exclude_from_color)
    
    ###### chart size
    @property
    def scale_factor(self): return self.__scale_factor
    @scale_factor.setter
    def scale_factor(self, scale_factor): self.__scale_factor = scale_factor 

    @property
    def dpi(self): return self.__dpi
    @dpi.setter
    def dpi(self, dpi): self.__dpi = dpi     
    
    @property
    def width(self): return self.__width
    @width.setter
    def width(self, width): self.__width = width 
    
    @property
    def height(self): return self.__height
    @height.setter
    def height(self, height): self.__height = height 
 
    ###### resample frequency
    @property
    def resample(self): return self.__resample
    @resample.setter
    def resample(self, resample): self.__resample = resample 
    
    ###### line properties and second y-axis
    @property
    def y_axis_2_series(self): return self.__y_axis_2_series
    @y_axis_2_series.setter
    def y_axis_2_series(self, y_axis_2_series): self.__y_axis_2_series = self.str_list(y_axis_2_series)

    @property
    def linewidth_2_series(self): return self.__linewidth_2_series
    @linewidth_2_series.setter
    def linewidth_2_series(self, linewidth_2_series): self.__linewidth_2_series = self.str_list(linewidth_2_series)
    
    @property
    def linewidth(self): return self.__linewidth
    @linewidth.setter
    def linewidth(self, linewidth): self.__linewidth = linewidth 
 
    @property
    def linewidth_2(self): return self.__linewidth_2
    @linewidth_2.setter
    def linewidth_2(self, linewidth_2): self.__linewidth_2 = linewidth_2

    @property
    def marker_size(self): return self.__marker_size
    @marker_size.setter
    def marker_size(self, marker_size): self.__marker_size = marker_size
    
    @property
    def line_of_best_fit(self): return self.__line_of_best_fit
    @line_of_best_fit.setter
    def line_of_best_fit(self, line_of_best_fit): self.__line_of_best_fit = line_of_best_fit

    ###### label properties
    @property
    def brand_label(self): return self.__brand_label
    @brand_label.setter
    def brand_label(self, brand_label): self.__brand_label = brand_label   
    
    @property
    def display_brand_label(self): return self.__display_brand_label
    @display_brand_label.setter
    def display_brand_label(self, display_brand_label): self.__display_brand_label = display_brand_label 
    
    @property
    def source(self): return self.__source
    @source.setter
    def source(self, source): self.__source = source

    @property
    def source(self): return self.__source_color
    @source.setter
    def source(self, source_color): self.__source_color = source_color
 
    @property
    def display_source_label(self): return self.__display_source_label
    @display_source_label.setter
    def display_source_label(self, display_source_label): self.__display_source_label = display_source_label 
    
    @property
    def display_legend(self): return self.__display_legend
    @display_legend.setter
    def display_legend(self, display_legend): self.__display_legend = display_legend   
    
    ###### display output settings
    @property
    def silent_display(self): return self.__silent_display
    @silent_display.setter
    def silent_display(self, silent_display): self.__silent_display = silent_display 
    
    @property
    def file_output(self): return self.__file_output
    @file_output.setter
    def file_output(self, file_output): self.__file_output = file_output 
 
    @property
    def date_formatter(self): return self.__date_formatter
    @date_formatter.setter
    def date_formatter(self, date_formatter): self.__date_formatter = date_formatter 
    
    ###### settings for MPLD3 and HTML output
    @property
    def html_file_output(self): return self.__html_file_output
    @html_file_output.setter
    def html_file_output(self, html_file_output): self.__html_file_output = html_file_output 
    
    @property
    def display_mpld3(self): return self.__display_mpld3
    @display_mpld3.setter
    def display_mpld3(self, display_mpld3): self.__display_mpld3 = display_mpld3 
    
    ###### Plotly specific settings
    @property
    def plotly_url(self): return self.__plotly_url
    @plotly_url.setter
    def plotly_url(self, plotly_url): self.__plotly_url = plotly_url 
    
    @property
    def plotly_as_image(self): return self.__plotly_as_image
    @plotly_as_image.setter
    def plotly_as_image(self, plotly_as_image): self.__plotly_as_image = plotly_as_image   
    
    @property
    def plotly_username(self): return self.__plotly_username
    @plotly_username.setter
    def plotly_username(self, plotly_username): self.__plotly_username = plotly_username 
    
    @property
    def plotly_api_key(self): return self.__plotly_api_key
    @plotly_api_key.setter
    def plotly_api_key(self, plotly_api_key): self.__plotly_api_key = plotly_api_key 
 
    @property
    def plotly_world_readable(self): return self.__plotly_world_readable
    @plotly_world_readable.setter
    def plotly_world_readable(self, plotly_world_readable): self.__plotly_world_readable = plotly_world_readable 
    
    @property
    def plotly_theme(self): return self.__plotly_theme
    @plotly_theme.setter
    def plotly_theme(self, plotly_theme): self.__plotly_theme = plotly_theme   

    ###### matplotlib specific settings
    @property
    def style_sheet(self): return self.__style_sheet
    @style_sheet.setter
    def style_sheet(self, style_sheet): self.__style_sheet = style_sheet

    @property
    def convert_matplotlib_to_plotly(self): return self.__convert_matplotlib_to_plotly
    @convert_matplotlib_to_plotly.setter
    def convert_matplotlib_to_plotly(self, convert_matplotlib_to_plotly):
        self.__convert_matplotlib_to_plotly = convert_matplotlib_to_plotly