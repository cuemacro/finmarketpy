__author__ = 'mhockenberger'

#
# Copyright 2016-2020 Cuemacro - https://www.cuemacro.com / @cuemacro
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
Shows how to calculate VWAP with finmarketpy
"""

import pandas as pd

from chartpy import Chart, Style
from finmarketpy.economics import TechIndicator, TechParams

from findatapy.util.loggermanager import LoggerManager

logger = LoggerManager().getLogger(__name__)

chart = Chart(engine='bokeh')

tech_ind = TechIndicator()

# Load data from local file
df = pd.read_csv("/Volumes/Data/s&p500.csv", index_col=0, parse_dates=['Date'],
                 date_parser=lambda x: pd.datetime.strptime(x, '%Y-%m-%d'))

# Calculate Volume Weighted Average Price (VWAP)
tech_params = TechParams()
tech_ind.create_tech_ind(df, 'VWAP', tech_params)

df = tech_ind.get_techind()

print(df)

style = Style()
style.title = 'S&P500 VWAP'
style.scale_factor = 2

df = tech_ind.get_techind()

chart.plot(df, style=style)
