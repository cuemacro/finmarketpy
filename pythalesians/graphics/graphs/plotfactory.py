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
PlotFactory

Provides common interface for various plotting libraries like PyThalesians (Matplotlib wrapper), Bokeh etc.

Planning to improve support for these libraries and to also add support for other plotting libraries/wrappers like
Plotly, Cufflinks (Plotly wrapper), Seaborne (Matplotlib wrapper)

"""

from pythalesians.graphics.graphs.lowleveladapters.adapterpythalesians import AdapterPyThalesians
from pythalesians.graphics.graphs.lowleveladapters.adapterbokeh import AdapterBokeh

from pythalesians.util.twitterpythalesians import TwitterPyThalesians

from pythalesians.market.loaders.timeseriesio import TimeSeriesIO

from pythalesians.util.constants import Constants

class PlotFactory:

    default_adapter = Constants().plotfactory_default_adapter
    
    def __init__(self):
        pass

    def plot_scatter_graph(self, data_frame, adapter = default_adapter, gp = None):
        return self.get_adapter(adapter).plot_2d_graph(data_frame, gp, 'scatter')

    def plot_line_graph(self, data_frame, adapter = default_adapter, gp = None):
        return self.get_adapter(adapter).plot_2d_graph(data_frame, gp, 'line')

    def plot_bar_graph(self, data_frame, adapter =  default_adapter, gp = None):
        return self.get_adapter(adapter).plot_2d_graph(data_frame, gp, 'bar')

    def tweet_line_graph(self, data_frame, adapter =  default_adapter, gp = None, twitter_msg = None, twitter_on = None):
        return self.tweet_generic_graph(data_frame, type = 'line', adapter = adapter, gp = gp,
                                        twitter_msg = twitter_msg, twitter_on = twitter_on)

    def tweet_bar_graph(self, data_frame, adapter =  default_adapter, gp = None, twitter_msg = None, twitter_on = None):
        return self.tweet_generic_graph(data_frame, type = 'bar', adapter = adapter, gp = gp,
                                        twitter_msg = twitter_msg, twitter_on = twitter_on)

    def tweet_generic_graph(self, data_frame, adapter =  default_adapter, type = 'line', gp = None, twitter_msg = None, twitter_on = None):
        self.plot_generic_graph(data_frame, type = type, adapter = adapter, gp = gp)

        twitter = TwitterPyThalesians()
        twitter.auto_set_key()

        if twitter_on: twitter.update_status(twitter_msg, picture = gp.file_output)

    def plot_generic_graph(self, data_frame, adapter =  default_adapter, type = 'line', gp = None, excel_file = None,
                           excel_sheet = None, freq = 'daily'):


        if (excel_file is not None):
            tio = TimeSeriesIO()

            data_frame = tio.read_excel_data_frame(excel_file, excel_sheet, freq)

        if type in ['line', 'bar', 'scatter']: return self.get_adapter(adapter).plot_2d_graph(data_frame, gp, type)

    def get_adapter(self, adapter):

        if adapter == 'pythalesians' or adapter == 'matplotlib':
            # use pythalesians wrapper for matplotlib
            return AdapterPyThalesians()

        elif adapter == 'bokeh':
            return AdapterBokeh()

        elif adapter == 'plotly':
            return self.logg

        return None

if __name__ == '__main__':
    # see examples/plotfactory_examples for practical examples on how to use this class
    pass