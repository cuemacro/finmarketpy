__author__ = 'saeedamen'

#
# Copyright 2020 Cuemacro
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
Shows how to use QuickChart to quickly download data and plot it
"""

# Generate a chart of S&P 500 on LHS y-axis axis and S&P 500 net long spec positioning on RHS y-axis downloaded from Bloomberg
QuickChart(engine='plotly', data_source='bloomberg').plot_chart(tickers='SPX Index', tickers_rhs='IMM0ENCN Index',
                             title='S&P500 vs. net spec pos RHS (2008-2010)',
                             start_date='01 Jan 2007', finish_date='01 Jan 2010')