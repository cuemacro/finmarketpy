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
from matplotlib.ticker import Formatter

# output matplotlib charts externally to D3 based libraries
import mpld3
import plotly.plotly as py
import plotly
import plotly.tools as tls

# for manipulating dates and maths
from datetime import timedelta
import numpy as np

from pythalesians.graphics.graphs.lowleveladapters.adaptertemplate import AdapterTemplate

from pythalesians.util.constants import Constants

class AdapterPyThalesians(AdapterTemplate):

    def plot_2d_graph(self, data_frame, gp, type):
        if gp.resample is not None: data_frame = data_frame.asfreq(gp.resample)

        # set the matplotlib style sheet & defaults
        matplotlib.rcdefaults()

        # first search PyThalesians styles, then try matplotlib
        try:
            plt.style.use(Constants().plotfactory_pythalesians_style_sheet[gp.style_sheet])
        except:
            plt.style.use(gp.style_sheet)

        matplotlib.rcParams.update({'font.size': matplotlib.rcParams['font.size'] * gp.scale_factor})

        # create figure & add a subplot
        fig = plt.figure(figsize = ((gp.width * gp.scale_factor)/gp.dpi,
                                    (gp.height * gp.scale_factor)/gp.dpi), dpi = gp.dpi)
        ax = fig.add_subplot(111)

        # format Y axis
        y_formatter = matplotlib.ticker.ScalarFormatter(useOffset = False)
        ax.yaxis.set_major_formatter(y_formatter)

        # create a second y axis if necessary
        ax2 = []

        if gp.y_axis_2_series != []:
            ax2 = ax.twinx()

            # do not use a grid with multiple y axes
            ax.yaxis.grid(False)
            ax2.yaxis.grid(False)

        # plot the lines (using custom palettes as appropriate)
        try:
            # get all the correct colors (and construct gradients if necessary eg. from 'blues')
            color_spec = self.create_color_list(gp, data_frame)

            if type == 'bar':
                # bottom = np.cumsum(np.vstack((np.zeros(data_frame.values.shape[1]), data_frame.values)), axis=0)[:-1]
                # bottom = np.vstack((np.zeros((data_frame.values.shape[1],), dtype=data_frame.dtype),
                #                    np.cumsum(data_frame.values, axis=0)[:-1]))
                yoff = np.zeros(len(data_frame.index.values)) # the bottom values for stacked bar chart

            # some lines we should exclude from the color and use the default palette
            for i in range(0, len(data_frame.columns.values)):
                label = str(data_frame.columns[i])

                ax_temp = self.get_axis(ax, ax2, label, gp.y_axis_2_series)

                xd = data_frame.index; yd = data_frame.ix[:,i]

                if (type == 'line'):
                    linewidth_t = self.get_linewidth(label,
                                                     gp.linewidth, gp.linewidth_2, gp.linewidth_2_series)

                    if linewidth_t is None: linewidth_t = matplotlib.rcParams['axes.linewidth']

                    ax_temp.plot(xd, yd, label = label, color = color_spec[i],
                                     linewidth = linewidth_t)
                elif(type == 'bar'):
                    ax_temp.bar(xd, yd, label = label, color = color_spec[i], bottom = yoff)
                    yoff = yoff + yd

                elif(type == 'scatter'):
                    ax_temp.scatter(xd, yd, label = label, color = color_spec[i])

                    if gp.line_of_best_fit is True:
                        self.trendline(ax_temp, xd.values, yd.values, order=1, color= color_spec[i], alpha=1,
                                           scale_factor = gp.scale_factor)
        except: pass

        # format X axis
        self.format_x_axis(ax, data_frame, gp)

        fig.suptitle(gp.title, fontsize = 14 * gp.scale_factor)

        if gp.display_source_label == True:
            ax.annotate('Source: ' + gp.source, xy = (1, 0), xycoords='axes fraction', fontsize=7 * gp.scale_factor,
                        xytext=(-5 * gp.scale_factor, 10 * gp.scale_factor), textcoords='offset points',
                        ha='right', va='top', color = gp.source_color)

        if gp.display_brand_label == True:
            self.create_brand_label(ax, anno = gp.brand_label, scale_factor = gp.scale_factor)

        leg = []
        leg2 = []

        loc = 'best'

        # if we have two y-axis then make sure legends are in opposite corners
        if ax2 != []: loc = 2

        try:
            leg = ax.legend(loc = loc, prop={'size':10 * gp.scale_factor})
            leg.get_frame().set_linewidth(0.0)
            leg.get_frame().set_alpha(0)

            if ax2 != []:
                leg2 = ax2.legend(loc = 1, prop={'size':10 * gp.scale_factor})
                leg2.get_frame().set_linewidth(0.0)
                leg2.get_frame().set_alpha(0)
        except: pass

        try:
            if gp.display_legend is False:
                if leg != []: leg.remove()
                if leg2 != []: leg.remove()
        except: pass

        try:
            plt.savefig(gp.file_output, transparent=False)
        except: pass

        try:
            if gp.silent_display == False: plt.show()
        except:
            pass

        # convert to D3 format with mpld3
        try:
            mpld3.save_d3_html(fig, gp.html_file_output)

            if gp.display_mpld3 == True: mpld3.show(fig)
        except: pass

        # FRAGILE! convert matplotlib chart to Plotly format
        # recommend using AdapterCufflinks instead to directly plot to Plotly
        try:
            if gp.convert_matplotlib_to_plotly:
                plotly.tools.set_credentials_file(username = gp.plotly_username,
                                                  api_key = gp.plotly_api_key)

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

                if gp.date_formatter is not None:
                    ax.xaxis.set_major_formatter(md.DateFormatter(gp.date_formatter))
                elif diff < timedelta(days = 4):

                    # class MyFormatter(Formatter):
                    #     def __init__(self, dates, fmt='%H:%M'):
                    #         self.dates = dates
                    #         self.fmt = fmt
                    #
                    #     def __call__(self, x, pos=0):
                    #         'Return the label for time x at position pos'
                    #         ind = int(round(x))
                    #         if ind >= len(self.dates) or ind < 0: return ''
                    #
                    #         return self.dates[ind].strftime(self.fmt)
                    #
                    # formatter = MyFormatter(dates)
                    # ax.xaxis.set_major_formatter(formatter)

                    date_formatter = '%H:%M'
                    xfmt = md.DateFormatter(date_formatter)
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
                    elif diff < timedelta(days=4):
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

    def get_axis(self, ax, ax2, label, y_axis_2_series):

        if label in y_axis_2_series: return ax2

        return ax


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

    def create_brand_label(self, ax, anno, scale_factor):
        ax.annotate(anno, xy = (0, 1), xycoords = 'axes fraction',
                    fontsize = 10 * scale_factor, color = 'white',
                    xytext = (0 * scale_factor, 15 * scale_factor), textcoords = 'offset points',
                    va = "center", ha = "center",
                    bbox = dict(boxstyle = "round,pad=0.4", facecolor = Constants().plotfactory_brand_colour))



