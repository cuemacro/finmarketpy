__author__ = 'saeedamen'  # Saeed Amen

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
Shows how to use QuickChart to quickly download data and plot it
"""

# Choose run_example = 0 for everything
# run_example = 1 - Plot S&P 500 charts with Matplotlib
# run_example = 1 - Plot FX chart with Plotly

run_example = 0

###### Plot with Matplotlib
if run_example == 1 or run_example == 0:
    from finmarketpy.economics import QuickChart

    # Plot with Matplotlib - S&P 500 on LHS y-axis and S&P 500 net long spec positioning on RHS y-axis
    QuickChart(engine='matplotlib', data_source='bloomberg').plot_chart(tickers={'S&P500' : 'SPX Index'},
        tickers_rhs={'Net long spec S&P 500 futures' : 'IMM0ENCN Index'},
        title='S&P500 vs. net spec pos RHS (2008-2010)',
                start_date='01 Jan 2007', finish_date='01 Jan 2010', source='Bloomberg')

    # Plot with Matplotlib - S&P 500 YoY returns
    QuickChart(engine='matplotlib', data_source='bloomberg').plot_chart(tickers={'S&P500' : 'SPX Index'},
                title='S&P 500 YoY', chart_type='bar',
                start_date='01 Jan 2007', yoy=True, source='Bloomberg')

###### Plot with Plotly and Matplotlib
if run_example == 2 or run_example == 0:
    from finmarketpy.economics import QuickChart

    # Plot with matplotlib - Major USD crosses reindexed from 100 in 2020
    QuickChart(engine='matplotlib', data_source='bloomberg').plot_chart(
        tickers=['EURUSD Curncy', 'GBPUSD Curncy', 'AUDUSD Curncy'],
        title='USD crosses in 2020',
        start_date='01 Jan 2020', reindex=True, source='Bloomberg')

    # Plot with Plotly - Major USD crosses reindexed from 100 in 2020
    QuickChart(engine='plotly', data_source='bloomberg').plot_chart(
        tickers=['EURUSD Curncy', 'GBPUSD Curncy', 'AUDUSD Curncy'],
        title='USD crosses in 2020 (Plotly)',
        start_date='01 Jan 2020', reindex=True, source='Bloomberg')