__author__ = "saeedamen"

#
# Copyright 2020 Cuemacro
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
Shows how to load up FX vol surfaces from Bloomberg and then plot an animation 
of them. Note, this does not do
any interpolation.
"""

from findatapy.market import Market, MarketDataRequest, MarketDataGenerator, FXVolFactory
from chartpy import Chart, Style

try:
    from finaddpy.market import CachedMarketDataGenerator as MarketDataGenerator
except:
    pass

def plot_animated_vol_market():
    market = Market(market_data_generator=MarketDataGenerator())

    cross = ["EURUSD"]; start_date = "01 Mar 2017"; finish_date = "21 Apr 2017"; sampling = "no"

    md_request = MarketDataRequest(start_date=start_date, finish_date=finish_date,
                                   data_source="bloomberg", cut="NYC", category="fx-implied-vol",
                                   tickers=cross, cache_algo="cache_algo_return")

    df = market.fetch_market(md_request)
    if sampling != "no": df = df.resample(sampling).mean()
    fxvf = FXVolFactory()
    df_vs = []

    # Grab the vol surface for each date and create a dataframe for each date (could have used a panel)
    for i in range(0, len(df.index)): df_vs.append(fxvf.extract_vol_surface_for_date(df, cross[0], i))

    # Do static plot for first day using Plotly
    style = Style(title="FX vol surface of " + cross[0], source="chartpy", color="Blues")

    Chart(df=df_vs[0], chart_type="surface", style=style).plot(engine="plotly")

    # Now do animation (TODO: need to fix animation in chartpy for matplotlib)
    style = Style(title="FX vol surface of " + cross[0], source="chartpy", color="Blues",
                    animate_figure=True, animate_titles=df.index,
                    animate_frame_ms=500, normalize_colormap=False)

    Chart(df=df_vs, chart_type="surface", style=style).plot(engine="plotly")

    # Chart object is initialised with the dataframe and our chart style
    Chart(df=df_vs, chart_type="surface", style=style).plot(engine="plotly")

if __name__ == "__main__":
    plot_animated_vol_market()