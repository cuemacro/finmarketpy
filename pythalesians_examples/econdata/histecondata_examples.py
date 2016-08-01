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
histecondata_examples

Shows how to get historical economic data and also plot.

The files below, contain default tickers and country groups. However, you can add whichever tickers you'd like
conf/all_econ_tickers.csv
conf/econ_country_codes.csv
conf/econ_country_groups.csv

These can be automatically generated via conf/econ_tickers.xlsm

For some of the plot examples to work, you need to have plotly & cufflinks setup (however, you will still be able to
download the data).

"""

import datetime

from pythalesians.economics.events.histecondatafactory import HistEconDataFactory
from pythalesians.economics.events.popular.commonecondatafactory import CommonEconDataFactory
from pythalesians.util.loggermanager import LoggerManager

# just change "False" to "True" to run any of the below examples

#### Plot US economic data by state using a choropleth Plotly plot
####
if False:
    logger = LoggerManager.getLogger(__name__)

    hist = HistEconDataFactory()
    start_date = '01 Jan 1990'
    finish_date = datetime.datetime.utcnow()
    country_group = 'usa-states'
    yoy_ret = False

    # select as appropriate
    # data_type = 'Total Nonfarm'; title = 'Change in non-farm payrolls (YoY)'; freq = 12
    # data_type = 'Real GDP'; title = 'Real GDP'; freq = 1
    # data_type = 'Economic Activity Index'; title = 'Economic Activity Index (YoY change %)'; yoy_ret = True; freq = 12
    # data_type = 'Total Construction Employees'; title = Total Construction Employees'; freq = 12
    data_type = 'Unemployment Rate'; title = 'Unemployment Rate'; freq = 12
    # data_type = 'Total Personal Income'; title = 'Total Personal Income'; freq = 12
    # data_type = 'House Price Index'; title = 'House Price Index (YoY change %)';  yoy_ret = True; freq = 12;

    source = 'fred'

    df = hist.get_economic_data_history(start_date, finish_date, country_group, data_type, source=source)
    df = df.fillna(method='pad')

    if yoy_ret is True: df = 100 * (df / df.shift(freq) - 1)

    df = hist.grasp_coded_entry(df, -1)

    from chartesians.graphs import PlotFactory
    from chartesians.graphs.graphproperties import GraphProperties

    gp = GraphProperties()
    pf = PlotFactory()

    gp.plotly_location_mode = 'USA-states'
    gp.plotly_choropleth_field = 'Val'
    gp.plotly_scope = 'usa'
    gp.plotly_projection = 'albers usa'
    gp.plotly_url = country_group + data_type.replace(' ', '-')
    gp.plotly_world_readable = False
    gp.title = title
    gp.units = 'Value'

    # do a map plot by US state
    pf.plot_generic_graph(df, type = 'choropleth', adapter = 'cufflinks', gp = gp)

#### uses CommonEconDataFactory to get more common forms of economic data and plot
####
if True:
    logger = LoggerManager.getLogger(__name__)

    cedf = CommonEconDataFactory()
    start_date = '01 Jan 2014'
    finish_date = datetime.datetime.utcnow()

    # select as appropriate!
    # cedf.g10_plot_gdp_cpi_une(start_date, finish_date)
    # cedf.usa_plot_une(start_date, finish_date)
    # cedf.world_plot_une(start_date, finish_date)
    # cedf.world_plot_cpi(start_date, finish_date)
    # cedf.europe_plot_une(start_date, finish_date)
    # cedf.g10_line_plot_cpi(start_date, finish_date)
    cedf.g10_line_plot_une(start_date, finish_date)
