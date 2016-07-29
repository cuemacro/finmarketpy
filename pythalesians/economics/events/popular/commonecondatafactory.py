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
CommonEconDataFactory

Has wrapper functions for HistEconDataFactory to download relatively common data releases (like CPI, GDP etc) for various
country groups.

"""

import datetime

from pythalesians.economics.events.histecondatafactory import HistEconDataFactory
from pythalesians.util.constants import Constants
from pythalesians.util.loggermanager import LoggerManager


class CommonEconDataFactory:

    def __init__(self):
        self.logger = LoggerManager().getLogger(__name__)
        self.hist_econ_data_factory = HistEconDataFactory()

    def get_econ_data_group(self, start_date, finish_date, country_group, data_type, source):
        df = self.hist_econ_data_factory.get_economic_data_history(start_date, finish_date,
                                       country_group, data_type, source = source)

        df = df.fillna(method='pad')

        return df

    def get_GDP_QoQ(self, start_date, finish_date, country_group, source = 'bloomberg'):
        return self.get_econ_data_group(start_date, finish_date, country_group, 'GDP QoQ (SAAR)', source = source)

    def get_GDP_QoQ(self, start_date, finish_date, country_group, source = 'bloomberg'):
        return self.get_econ_data_group(start_date, finish_date, country_group, 'GDP QoQ (SAAR)', source = source)

    def get_UNE(self, start_date, finish_date, country_group, source = 'bloomberg'):
        return self.get_econ_data_group(start_date, finish_date, country_group, 'Unemployment Rate', source = source)

    def get_CPI_YoY(self, start_date, finish_date, country_group, source = 'bloomberg'):
        return self.get_econ_data_group(start_date, finish_date, country_group, 'CPI YoY', source = source)

    def usa_plot_une(self, start_date, finish_date):
        country_group = 'usa-states'; source = 'bloomberg'

        une = self.get_UNE(start_date, finish_date, country_group, source = 'bloomberg')
        une = self.hist_econ_data_factory.grasp_coded_entry(une, -1)

        from pythalesians_graphics.graphs import PlotFactory
        from pythalesians_graphics.graphs.graphproperties import GraphProperties

        gp = GraphProperties()
        pf = PlotFactory()

        gp.plotly_location_mode = 'USA-states'
        gp.plotly_choropleth_field = 'Val'
        gp.plotly_scope = 'usa'
        gp.plotly_projection = 'albers usa'
        gp.plotly_world_readable = False
        gp.plotly_url = country_group + "-unemployment"

        gp.title = "USA Unemployment"
        gp.units = 'pc'

        pf.plot_generic_graph(une, type = 'choropleth', adapter = 'plotly', gp = gp)

    def g10_plot_gdp_cpi_une(self, start_date, finish_date, data_type = 'cpi'):
        country_group = 'g10'

        if data_type == 'cpi':
            df = self.get_CPI_YoY(start_date, finish_date, country_group)
        elif data_type == 'gdp':
            df = self.get_GDP_QoQ(start_date, finish_date, country_group)
        elif data_type == 'une':
            df = self.get_UNE(start_date, finish_date, country_group)

        df = self.hist_econ_data_factory.grasp_coded_entry(df, -1)

        from pythalesians_graphics.graphs import PlotFactory
        from pythalesians_graphics.graphs.graphproperties import GraphProperties

        gp = GraphProperties()
        pf = PlotFactory()

        gp.plotly_location_mode = 'world'
        gp.plotly_choropleth_field = 'Val'
        gp.plotly_scope = 'world'
        gp.plotly_projection = 'Mercator'

        gp.plotly_world_readable = False

        gp.plotly_url = country_group + "-" + data_type
        gp.title = "G10 " + data_type
        gp.units = '%'

        pf.plot_generic_graph(df, type = 'choropleth', adapter = 'plotly', gp = gp)

    def europe_plot_une(self, start_date, finish_date):
        country_group = 'all-europe'

        une = self.get_UNE(start_date, finish_date, country_group)
        une = self.hist_econ_data_factory.grasp_coded_entry(une, -1)

        from pythalesians_graphics.graphs import PlotFactory
        from pythalesians_graphics.graphs.graphproperties import GraphProperties

        gp = GraphProperties()
        pf = PlotFactory()

        gp.plotly_location_mode = 'europe'
        gp.plotly_choropleth_field = 'Val'
        gp.plotly_scope = 'europe'
        gp.plotly_projection = 'Mercator'

        gp.plotly_world_readable = False

        gp.plotly_url = country_group + "-unemployment"; gp.title = "Europe Unemployment"
        gp.units = '%'

        pf.plot_generic_graph(une, type = 'choropleth', adapter = 'plotly', gp = gp)

    def world_plot_cpi(self, start_date, finish_date):
        country_group = 'world-liquid'

        cpi = self.get_CPI_YoY(start_date, finish_date, country_group)
        cpi = self.hist_econ_data_factory.grasp_coded_entry(cpi, -1)

        from pythalesians_graphics.graphs import PlotFactory
        from pythalesians_graphics.graphs.graphproperties import GraphProperties

        gp = GraphProperties()
        pf = PlotFactory()

        gp.plotly_location_mode = 'world'
        gp.plotly_choropleth_field = 'Val'
        gp.plotly_scope = 'world'
        gp.plotly_projection = 'Mercator'

        gp.plotly_world_readable = False

        gp.plotly_url = str(country_group) + "-cpi"
        gp.title = "World Liquid CPI YoY"
        gp.units = '%'

        pf.plot_generic_graph(cpi, type = 'choropleth', adapter = 'plotly', gp = gp)

    def g10_line_plot_cpi(self, start_date, finish_date):
        today_root = datetime.date.today().strftime("%Y%m%d") + " "
        country_group = 'g10-ez'
        cpi = self.get_CPI_YoY(start_date, finish_date, country_group)

        from pythalesians_graphics.graphs import PlotFactory
        from pythalesians_graphics.graphs.graphproperties import GraphProperties

        gp = GraphProperties()
        pf = PlotFactory()

        gp.title = "G10 CPI YoY"
        gp.units = '%'
        gp.scale_factor = Constants.plotfactory_scale_factor
        gp.file_output = today_root + 'G10 CPI YoY ' + str(gp.scale_factor) + '.png'
        cpi.columns = [x.split('-')[0] for x in cpi.columns]
        gp.linewidth_2 = 3
        gp.linewidth_2_series = ['United States']

        pf.plot_generic_graph(cpi, type = 'line', adapter = 'pythalesians', gp = gp)

    def g10_line_plot_une(self, start_date, finish_date):
        today_root = datetime.date.today().strftime("%Y%m%d") + " "
        country_group = 'g10-ez'
        une = self.get_UNE(start_date, finish_date, country_group)

        from pythalesians_graphics.graphs import PlotFactory
        from pythalesians_graphics.graphs.graphproperties import GraphProperties

        gp = GraphProperties()
        pf = PlotFactory()

        gp.title = "G10 Unemployment Rate (%)"
        gp.units = '%'
        gp.scale_factor = Constants.plotfactory_scale_factor
        gp.file_output = today_root + 'G10 UNE ' + str(gp.scale_factor) + '.png'
        une.columns = [x.split('-')[0] for x in une.columns]
        gp.linewidth_2 = 3
        gp.linewidth_2_series = ['United States']

        pf.plot_generic_graph(une, type = 'line', adapter = 'pythalesians', gp = gp)

    def g10_line_plot_gdp(self, start_date, finish_date):
        today_root = datetime.date.today().strftime("%Y%m%d") + " "
        country_group = 'g10-ez'
        gdp = self.get_GDP_QoQ(start_date, finish_date, country_group)

        from pythalesians_graphics.graphs import PlotFactory
        from pythalesians_graphics.graphs.graphproperties import GraphProperties

        gp = GraphProperties()
        pf = PlotFactory()

        gp.title = "G10 GDP"
        gp.units = 'Rebased'
        gp.scale_factor = Constants.plotfactory_scale_factor
        gp.file_output = today_root + 'G10 UNE ' + str(gp.scale_factor) + '.png'
        gdp.columns = [x.split('-')[0] for x in gdp.columns]
        gp.linewidth_2 = 3
        gp.linewidth_2_series = ['United Kingdom']

        from pythalesians.timeseries.calcs.timeseriescalcs import TimeSeriesCalcs
        tsc = TimeSeriesCalcs()
        gdp = gdp / 100
        gdp = tsc.create_mult_index_from_prices(gdp)
        pf.plot_generic_graph(gdp, type = 'line', adapter = 'pythalesians', gp = gp)

if __name__ == '__main__':
    # pass

    start_date = '01 Jan 2009'
    finish_date = datetime.datetime.utcnow()
    cedf = CommonEconDataFactory()
    cedf.g10_line_plot_gdp(start_date=start_date, finish_date=finish_date)
    # see histecondata_examples