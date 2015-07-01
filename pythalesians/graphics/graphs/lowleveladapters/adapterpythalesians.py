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
AdapterMatplotlib

Wrapper for matplotlib for charting, with an easier to use common interface. Currently supports simple line, bar and
scatter plots. Like Seaborne, this wrapper seeks to make "nicer" plots than the matplotlib defaults.

"""

# matplotlib based libraries
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.dates import YearLocator, MonthLocator, DayLocator, HourLocator, MinuteLocator
from matplotlib.ticker import MultipleLocator

# output matplotlib charts externally to D3 based libraries
import mpld3
import plotly.plotly as py
import plotly
import plotly.tools as tls

# for manipulating dates and maths
from datetime import timedelta
from math import log10, floor
import numpy as np

from pythalesians.graphics.graphs.lowleveladapters.adaptertemplate import AdapterTemplate

from pythalesians.util.constants import Constants

class AdapterPyThalesians(AdapterTemplate):

    def plot_2d_graph(self, data_frame, gp, type):
        matplotlib.rcdefaults()

        # set the matplotlib style sheet
        plt.style.use(Constants().plotfactory_pythalesians_style_sheet[Constants().plotfactory_default_stylesheet])

        if hasattr(gp, 'style_sheet'):
            plt.style.use(Constants().plotfactory_pythalesians_style_sheet[gp.style_sheet])

        scale_factor = Constants().plotfactory_scale_factor

        if hasattr(gp, 'scale_factor'): scale_factor = gp.scale_factor

        dpi = Constants().plotfactory_dpi

        if hasattr(gp, 'dpi'): dpi = gp.dpi

        width = Constants().plotfactory_width; height = Constants().plotfactory_height

        if hasattr(gp, 'width'): width = gp.width
        if hasattr(gp, 'height'): width = gp.height

        fig = plt.figure(figsize = ((width * scale_factor)/dpi, (height * scale_factor)/dpi), dpi = dpi)

        # add a subplot
        ax = fig.add_subplot(111)

        matplotlib.rcParams.update({'font.size': matplotlib.rcParams['font.size'] * scale_factor})

        # format Y axis
        y_formatter = matplotlib.ticker.ScalarFormatter(useOffset = False)
        ax.yaxis.set_major_formatter(y_formatter)

        # format X axis
        self.format_x_axis(ax, data_frame, gp)

        y_axis_2_series = []
        ax2 = []
        color_2_series = []
        linewidth_2_series = []

        # create a second y axis if necessary
        if hasattr(gp, 'y_axis_2_series'):
            if gp.y_axis_2_series == []:
                pass
            else:
                y_axis_2_series = gp.y_axis_2_series
                ax2 = ax.twinx()

                # matplotlib.rcParams.update({'figure.subplot.right': matplotlib.rcParams['figure.subplot.right'] - 0.05})

                # do not use a grid with multiple y axes
                ax.yaxis.grid(False)
                ax2.yaxis.grid(False)

        # is there a second palette?
        if hasattr(gp, 'color_2_series'):
            if hasattr(gp.color_2_series, 'values'):
                color_2_series = [str(x) for x in gp.color_2_series.values]
            else:
                color_2_series = [str(x) for x in gp.color_2_series]

        # is there a second linewidth series
        if hasattr(gp, 'linewidth_2_series'):
            if hasattr(gp.linewidth_2_series, 'values'):
                linewidth_2_series = [str(x) for x in gp.linewidth_2_series.values]
            else:
                linewidth_2_series = [str(x) for x in gp.linewidth_2_series]

        # plot the lines (using custom palettes as appropriate)
        try:
            color = []; color_2 = []
            linewidth_2 = matplotlib.rcParams['axes.linewidth']

            exclude_from_color = []

            if hasattr(gp, 'color'):
                if isinstance(gp.color, list):
                    color = gp.color
                else:
                    try:
                        color = self.create_colormap(
                            len(data_frame.columns.values) - len(color_2_series), gp.color)
                    except: pass

            if hasattr(gp, 'width'):
                if isinstance(gp.width, list):
                    color = gp.color
                else:
                    try:
                        color = self.create_colormap(
                            len(data_frame.columns.values) - len(color_2_series), gp.color)
                    except: pass

            if hasattr(gp, 'color_2'):
                if isinstance(gp.color_2, list):
                    color_2 = gp.color_2
                else:
                    try:
                        color_2 = self.create_colormap(len(color_2_series), gp.color_2)
                    except: pass

            if hasattr(gp, 'exclude_from_color'):
                if not(isinstance(gp.exclude_from_color, list)):
                    gp.exclude_from_color = [gp.exclude_from_color]

                exclude_from_color = [str(x) for x in gp.exclude_from_color]

            if hasattr(gp, 'linewidth_2'):
                linewidth_2 = gp.linewidth_2

            axis_1_color_index = 0
            axis_2_color_index = 0

            if type == 'bar':
                # bottom = np.cumsum(np.vstack((np.zeros(data_frame.values.shape[1]), data_frame.values)), axis=0)[:-1]
                # bottom = np.vstack((np.zeros((data_frame.values.shape[1],), dtype=data_frame.dtype),
                #                    np.cumsum(data_frame.values, axis=0)[:-1]))
                yoff = np.zeros(len(data_frame.index.values)) # the bottom values for stacked bar chart

            # some lines we should exclude from the color and use the default palette
            for i in range(0, len(data_frame.columns.values)):
                label = str(data_frame.columns[i])
                ax_temp = self.get_axis(ax, ax2, label, y_axis_2_series)

                color_spec, axis_1_color_index, axis_2_color_index = \
                    self.get_color(label, axis_1_color_index, axis_2_color_index, color, color_2,
                                        exclude_from_color, color_2_series)

                xd = data_frame.index; yd = data_frame.ix[:,i]

                if (type == 'line'):
                    linewidth = self.get_linewidth(label, linewidth_2, linewidth_2_series)
                    ax_temp.plot(xd, yd, label = label, color = color_spec,
                                 linewidth = linewidth)
                elif(type == 'bar'):
                    ax_temp.bar(xd, yd, label = label, color = color_spec, bottom = yoff)
                    yoff = yoff + yd

                elif(type == 'scatter'):
                    ax_temp.scatter(xd, yd, label = label, color = color_spec)

                    if hasattr(gp, 'line_of_best_fit'):
                        if gp.line_of_best_fit == True:
                            self.trendline(ax_temp, xd.values, yd.values, order=1, color= color_spec, alpha=1,
                                           scale_factor = scale_factor)
        except: pass

        try:
             fig.suptitle(gp.title, fontsize = 14 * scale_factor)
        except: pass

        try:
            source = Constants().plotfactory_source

            source_color = 'black'
            display_brand_label = False

            if hasattr(gp, 'source'):
                source = gp.source
                display_brand_label = True

            if hasattr(gp, 'source_color'):
                source_color = self.get_color_code(gp.source_color)

            if display_brand_label or Constants().plotfactory_display_brand_label:
                ax.annotate('Source: ' + source, xy = (1, 0), xycoords='axes fraction', fontsize=7 * scale_factor,
                        xytext=(-5 * scale_factor, 10 * scale_factor), textcoords='offset points',
                        ha='right', va='top', color = source_color)

        except: pass

        if hasattr(gp, 'display_brand_label'):
            if gp.display_brand_label is True:
                self.create_brand_label(ax, anno = Constants().plotfactory_brand_label, scale_factor = scale_factor)
        else:
            if Constants().plotfactory_display_brand_label is True:
                self.create_brand_label(ax, anno = Constants().plotfactory_brand_label, scale_factor = scale_factor)

        leg = []
        leg2 = []

        loc = 'best'

        # if we have two y-axis then make sure legends are in opposite corners
        if ax2 != []: loc = 2

        try:
            leg = ax.legend(loc = loc, prop={'size':10 * scale_factor})
            leg.get_frame().set_linewidth(0.0)
            leg.get_frame().set_alpha(0)

            if ax2 is not []:
                leg2 = ax2.legend(loc = 1, prop={'size':10 * scale_factor})
                leg2.get_frame().set_linewidth(0.0)
                leg2.get_frame().set_alpha(0)

        except: pass

        try:
            if gp.display_legend == False:
                if leg is not[]: leg.remove()
                if leg2 is not[]: leg.remove()

        except: pass

        try:
            plt.savefig(gp.file_output, transparent=False)
        except: pass

        try:
            if hasattr(gp, 'silent_display'):
                if gp.silent_display is False:
                    plt.show()
            else:
                plt.show()
        except:
            pass

        # convert to D3 format with mpld3
        try:
            if hasattr(gp, 'html_file_output'):
                mpld3.save_d3_html(fig, gp.html_file_output)

            if hasattr(gp, 'display_mpld3'):
                if gp.display_mpld3 == True: mpld3.show(fig)
        except: pass

        # convert to Plotly format (fragile!)
        # TODO better to create Plotly graphs from scratch rather than convert from matplotlib
        # TODO also dependent on matplotlib version for support
        try:
            if hasattr(gp, 'plotly_url'):
                plotly.tools.set_credentials_file(username = Constants().plotly_username,
                                                  api_key = Constants().plotly_api_key)

                py_fig = tls.mpl_to_plotly(fig, strip_style = True)
                plot_url = py.plot_mpl(py_fig, filename = gp.plotly_url)
        except:
            pass

    def format_x_axis(self, ax, data_frame, gp):
        # format X axis
        dates = data_frame.index

        # scaling for time series plots with hours and minutes only (and no dates)
        if hasattr(data_frame.index[0], 'hour') and not(hasattr(data_frame.index[0], 'month')):
            ax.xaxis.set_major_locator(MultipleLocator(86400./3.))
            ax.xaxis.set_minor_locator(MultipleLocator(86400./24.))
            ax.grid(b = True, which='minor', color='w', linewidth=0.5)

        # TODO have more refined way of formating time series x-axis!

        # scaling for time series plots with dates too
        else:
            # to handle dates
            try:
                dates = dates.to_pydatetime()
                diff = data_frame.index[-1] - data_frame.index[0]

                import matplotlib.dates as md

                if hasattr(gp, 'date_formatter'):
                    ax.xaxis.set_major_formatter(md.DateFormatter(gp.date_formatter))
                elif diff < timedelta(days = 2):
                    xfmt = md.DateFormatter('%H:%M')
                    ax.xaxis.set_major_formatter(xfmt)

                    if diff < timedelta(minutes=20):
                        ax.xaxis.set_major_locator(MinuteLocator(byminute=range(60), interval=2))
                        ax.xaxis.set_minor_locator(MinuteLocator(interval=1))
                    elif diff < timedelta(hours=1):
                        ax.xaxis.set_major_locator(MinuteLocator(byminute=range(60), interval=5))
                        ax.xaxis.set_minor_locator(MinuteLocator(interval=2))
                    elif diff < timedelta(hours=6):
                        locator = HourLocator(interval=1)
                        ax.xaxis.set_major_locator(locator)
                        ax.xaxis.set_minor_locator(MinuteLocator(interval=30))
                    elif diff < timedelta(days=2):
                        ax.xaxis.set_major_locator(HourLocator(interval=6))
                        ax.xaxis.set_minor_locator(HourLocator(interval=1))

                elif diff < timedelta(days=40):
                    locator = DayLocator(interval=10)
                    ax.xaxis.set_major_locator(locator)
                    ax.xaxis.set_major_formatter(md.DateFormatter('%d %b %y'))

                    day_locator = DayLocator(interval=1)
                    ax.xaxis.set_minor_locator(day_locator)

                elif diff < timedelta(days=365 * 0.5):
                    locator = MonthLocator(bymonthday=1, interval=2)
                    ax.xaxis.set_major_locator(locator)
                    ax.xaxis.set_major_formatter(md.DateFormatter('%b %y'))

                    months_locator = MonthLocator(interval=1)
                    ax.xaxis.set_minor_locator(months_locator)

                elif diff < timedelta(days=365 * 2):
                    locator = MonthLocator(bymonthday=1, interval=3)
                    ax.xaxis.set_major_locator(locator)
                    ax.xaxis.set_major_formatter(md.DateFormatter('%b %y'))

                    months_locator = MonthLocator(interval=1)
                    ax.xaxis.set_minor_locator(months_locator)

                elif diff < timedelta(days = 365 * 5):
                    locator = YearLocator()
                    ax.xaxis.set_major_locator(locator)
                    ax.xaxis.set_major_formatter(md.DateFormatter('%Y'))
            except:
                try:
                    # otherwise we have integers, rather than dates
                    max = dates.max()
                    min = dates.min()

                    big_step = self.round_to_1((max - min)/10)

                    small_step = big_step / 5

                    ax.xaxis.set_major_locator(MultipleLocator(big_step))
                    ax.xaxis.set_minor_locator(MultipleLocator(small_step))

                    plt.xlim(min, max)
                except: pass

    def round_to_1(self, x):
        return round(x, -int(floor(log10(x))))

    def get_axis(self, ax, ax2, label, y_axis_2_series):

        if label in y_axis_2_series:
            return ax2

        return ax

    def get_linewidth(self, label, linewidth_2, linewidth_2_series):
        if label in linewidth_2_series:
            return linewidth_2

        return matplotlib.rcParams['axes.linewidth']

    def get_color(self, label, axis_1_color_index, axis_2_color_index, color, color_2, exclude_from_color,
                  color_2_series):
        if label in exclude_from_color:
            return None, axis_1_color_index, axis_2_color_index

        if label in color_2_series:
            if color_2 != []:
                return self.get_color_code(color_2[axis_2_color_index]), axis_1_color_index, axis_2_color_index + 1
        else:
            if color != []:
                return self.get_color_code(color[axis_1_color_index]), axis_1_color_index + 1, axis_2_color_index

        return None, axis_1_color_index, axis_2_color_index

    def trendline(self, ax, xd, yd, order=1, color='red', alpha=1, Rval=False, scale_factor = 1):
        """Make a line of best fit"""

        # Calculate trendline
        xd[np.isnan(xd)] = 0
        yd[np.isnan(yd)] = 0

        coeffs = np.polyfit(xd, yd, order)

        intercept = coeffs[-1]
        slope = coeffs[-2]
        if order == 2: power = coeffs[0]
        else: power = 0

        minxd = np.min(xd)
        maxxd = np.max(xd)

        xl = np.array([minxd, maxxd])
        yl = power * xl ** 2 + slope * xl + intercept

        # plot trendline
        ax.plot(xl, yl, color = color, alpha = alpha)

        # calculate R squared
        p = np.poly1d(coeffs)

        ybar = np.sum(yd) / len(yd)
        ssreg = np.sum((p(xd) - ybar) ** 2)
        sstot = np.sum((yd - ybar) ** 2)
        Rsqr = ssreg / sstot

        if Rval == False:
            text = 'R^2 = %0.2f, m = %0.4f, c = %0.4f' %(Rsqr, slope, intercept)

            ax.annotate(text, xy=(1, 1), xycoords='axes fraction', fontsize=8 * scale_factor,
                    xytext=(-5 * scale_factor, 10 * scale_factor), textcoords='offset points',
                    ha='right', va='top')

            # Plot R^2 value
            # ax.text(0.65, 0.95, text, fontsize = 10 * scale_factor,
            #            ha= 'left',
            #            va = 'top', transform = ax.transAxes)
            pass
        else:
            # return the R^2 value:
            return Rsqr

    def get_color_code(self, code):
        # redefine color names
        dict = Constants().plotfactory_color_overwrites

        if code in dict: return dict[code]

        return code

    def create_brand_label(self, ax, anno = Constants().plotfactory_brand_label, scale_factor = 1):
        ax.annotate(anno, xy = (0, 1), xycoords = 'axes fraction',
                    fontsize = 10 * scale_factor, color = 'white',
                    xytext = (0 * scale_factor, 15 * scale_factor), textcoords = 'offset points',
                    va = "center", ha = "center",
                    bbox = dict(boxstyle = "round,pad=0.4", facecolor = Constants().plotfactory_brand_colour))

    def create_colormap(self, num_colors, map_name):
        ## matplotlib ref for colors: http://matplotlib.org/examples/color/colormaps_reference.html
        cm = matplotlib.cm.get_cmap(name = map_name)
        return [cm(1.*i/num_colors) for i in range(num_colors)]
