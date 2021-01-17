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
Shows how to use finmarketpy to process FX vol surfaces which have been interpolated (uses FinancePy underneath).

Note, you will need to have a Bloomberg terminal (with blpapi Python library) to download the FX market data in order
to plot these vol surface (FX spot, FX forwards, FX implied_vol volatility quotes and deposits)
"""

# For plotting
from chartpy import Chart, Style

# For loading market data
from findatapy.market import Market, MarketDataGenerator, MarketDataRequest

from findatapy.util.loggermanager import LoggerManager

from finmarketpy.curve.volatility.fxvolsurface import FXVolSurface

logger = LoggerManager().getLogger(__name__)

chart = Chart(engine='plotly')
market = Market(market_data_generator=MarketDataGenerator())

# Choose run_example = 0 for everything
# run_example = 1 - plot GBPUSD 1W implied vol
# run_example = 2 - get GBPUSD vol surface for a date and plot interpolated vol surface and implied PDF
# run_example = 3 - do an animation of GBPUSD implied vol surface over this period
# run_example = 4 - get implied vol for a particular strike, interpolating the surface
# run_example = 5 - get USDJPY vol surface around US presidential election and plot

run_example = 3

###### Fetch market data for pricing GBPUSD FX options over Brexit vote (ie. FX spot, FX forwards, FX deposits and FX vol quotes)
###### Show how to plot ATM 1M implied_vol vol time series
if run_example == 1 or run_example == 0:

    # Download the whole all market data for GBPUSD for pricing options (vol surface)
    md_request = MarketDataRequest(start_date='01 May 2016', finish_date='01 Aug 2016',
                                   data_source='bloomberg', cut='LDN', category='fx-vol-market',
                                   tickers=['GBPUSD'],
                                   cache_algo='cache_algo_return')

    df = market.fetch_market(md_request)

    style = Style()

    style.title = 'GBPUSD 1M Implied Vol'
    style.scale_factor = 3
    style.source = 'Bloomberg'

    chart.plot(df['GBPUSDV1M.close'], style=style)

###### Fetch market data for pricing GBPUSD FX options over Brexit vote (ie. FX spot, FX forwards, FX deposits and FX vol quotes)
###### Construct volatility surface using FinancePy library underneath, using polynomial interpolation
if run_example == 2 or run_example == 0:

    horizon_date = '23 Jun 2016'

    # Download the whole all market data for GBPUSD for pricing options (vol surface)
    md_request = MarketDataRequest(start_date=horizon_date, finish_date=horizon_date,
                                   data_source='bloomberg', cut='LDN', category='fx-vol-market',
                                   tickers=['GBPUSD'],
                                   cache_algo='cache_algo_return')

    df = market.fetch_market(md_request)

    fx_vol_surface = FXVolSurface(market_df=df, vol_function_type='BBG', asset='GBPUSD')

    fx_vol_surface.build_vol_surface(horizon_date)

    # Note for unstable vol surface dates (eg. over Brexit date) you may need to increase tolerance in FinancePy
    # FinFXVolSurface.buildVolSurface method to get it to fill, or choose different vol_function_type (eg. 'CLARK5')
    df_vol_dict = fx_vol_surface.extract_vol_surface()

    # Print out the various vol surface and data produced
    print(df_vol_dict['vol_surface_implied_pdf'])
    print(df_vol_dict['vol_surface_strike_space'])
    print(df_vol_dict['vol_surface_delta_space'])
    print(df_vol_dict['vol_surface_delta_space_exc_ms'])
    print(df_vol_dict['deltas_vs_strikes'])
    print(df_vol_dict['vol_surface_quoted_points'])

    # Plot vol surface in strike space (all interpolated)
    # x_axis = strike - index
    # y_axis = tenor - columns
    # z_axis = implied vol - values
    chart.plot(df_vol_dict['vol_surface_strike_space'].iloc[:, ::-1], chart_type='surface',
               style=Style(title='Plotting volatility in strike space'))

    # Plot vol surface in delta space (exc market strangle strikes)
    chart.plot(df_vol_dict['vol_surface_delta_space_exc_ms'].iloc[:, ::-1],
               chart_type='surface', style=Style(title='Plotting in delta space'))

    # Plot implied PDF in strike space (all interpolated)
    # x_axis = strike - index
    # y_axis = tenor - columns
    # z_axis = implied PDF - values
    chart.plot(df_vol_dict['vol_surface_implied_pdf'], chart_type='surface',
               style=Style(title='Plotting implied PDF in strike space'))

    # Plot the implied PDF for ON only versus strikes
    chart.plot(df_vol_dict['vol_surface_implied_pdf']['ON'], chart_type='line',
               style=Style(title='Plotting implied PDF in strike space ON around Brexit', x_axis_range=[1.0,1.8]))


###### Fetch market data for pricing GBPUSD FX options over Brexit vote (ie. FX spot, FX forwards, FX deposits and FX vol quotes)
###### Do animation for vol surface
if run_example == 3 or run_example == 0:
    # Download the whole all market data for GBPUSD for pricing options (vol surface)
    # Using LDN close data (CMPL)
    md_request = MarketDataRequest(start_date='01 Jun 2016', finish_date='30 Jul 2016',
                                   data_source='bloomberg', cut='LDN', category='fx-vol-market',
                                   tickers=['GBPUSD'],
                                   cache_algo='cache_algo_return')
    # 01 Jun 2016, 30 Jun 2016
    # 20 Jun 2016, 24 Jun 2016

    df = market.fetch_market(md_request)

    fx_vol_surface = FXVolSurface(market_df=df, asset='GBPUSD')

    animate_titles = []

    # Note for unstable vol surface dates (eg. over Brexit date) you may need to increase tolerance in FinancePy
    # FinFXVolSurface.buildVolSurface method to get it to fill - or just change dates and currency pair

    # Note this does take a few minutes, given it's fitting the vol surface for every date
    # TODO explore speeding up using Numba or similar
    vol_surface_dict, extremes_dict = fx_vol_surface.extract_vol_surface_across_dates(df.index,
                                         vol_surface_type='vol_surface_strike_space')

    animate_titles = [x.strftime('%d %b %Y') for x in vol_surface_dict.keys()]

    print(extremes_dict)

    # Plot vol surface animation in strike space (all interpolated)
    # x_axis = strike - index
    # y_axis = tenor - columns
    # z_axis = implied_vol vol - values
    style = Style(title='Plotting in strike space', animate_figure=True, animate_titles=animate_titles)

    chart.plot(list(vol_surface_dict.values()), chart_type='surface', style=style)

###### Fetch market data for pricing GBPUSD FX options over Brexit vote (ie. FX spot, FX forwards, FX deposits and FX vol quotes)
###### Get implied_vol vol for specific strikes interpolating across surface
if run_example == 4 or run_example == 0:
    # Download the whole all market data for GBPUSD for pricing options (vol surface)
    md_request = MarketDataRequest(start_date='20 Jun 2016', finish_date='25 Jun 2016',
                                   data_source='bloomberg', cut='LDN', category='fx-vol-market',
                                   tickers=['GBPUSD'],
                                   cache_algo='cache_algo_return')

    df = market.fetch_market(md_request)

    fx_vol_surface = FXVolSurface(market_df=df, asset='GBPUSD')

    df_vol_surface_strike_space_list = []
    animate_titles = []

    fx_vol_surface.build_vol_surface('20 Jun 2016')

    # Get the implied_vol volatility for a specific strike (GBPUSD=1.4000 in the 1W tenor) for 20 Jun 2016
    vol_at_strike = fx_vol_surface.calculate_vol_for_strike_expiry(1.4000, tenor='1W')

    fx_vol_surface.build_vol_surface('23 Jun 2016')

    # Get the implied_vol volatility for a specific strike (GBPUSD=1.4000 in the 1W tenor) for 23 Jun 2016
    vol_at_strike = fx_vol_surface.calculate_vol_for_strike_expiry(1.4000, tenor='1W')

    print(vol_at_strike)

###### Fetch market data for pricing USDJPY FX options near 2020 US Presidential Election (03 Nov 2020)
###### (ie. FX spot, FX forwards, FX deposits and FX vol quotes)
###### Construct volatility surface using FinancePy library underneath, using polynomial interpolation
if run_example == 5 or run_example == 0:

    horizon_date = '03 Nov 2020'

    # Download the whole all market data for GBPUSD for pricing options (vol surface)
    md_request = MarketDataRequest(start_date=horizon_date, finish_date=horizon_date,
                                   data_source='bloomberg', cut='NYC', category='fx-vol-market',
                                   tickers=['USDJPY'],
                                   cache_algo='cache_algo_return')

    df = market.fetch_market(md_request)

    # Skip 3W/4M because this particular close (NYC) doesn't have that in USDJPY market data
    tenors = ["ON", "1W", "2W", "1M", "2M", "3M", "6M", "9M", "1Y", "2Y", "3Y"]
    fx_vol_surface = FXVolSurface(market_df=df, tenors=tenors, asset='USDJPY')

    fx_vol_surface.build_vol_surface(horizon_date)

    # Note for unstable vol surface dates (eg. over Brexit date) you may need to increase tolerance in FinancePy
    # FinFXVolSurface.buildVolSurface method to get it to fill
    df_vol_dict = fx_vol_surface.extract_vol_surface()

    # Plot vol surface in strike space (all interpolated)
    # x_axis = strike - index
    # y_axis = tenor - columns
    # z_axis = implied vol - values
    chart.plot(df_vol_dict['vol_surface_strike_space'].iloc[:, ::-1], chart_type='surface',
               style=Style(title='Plotting volatility in strike space'))

    # Plot vol surface in delta space (exc market strangle strikes)
    chart.plot(df_vol_dict['vol_surface_delta_space_exc_ms'].iloc[:, ::-1],
               chart_type='surface', style=Style(title='Plotting in delta space'))