__author__ = "saeedamen"  # Saeed Amen / saeed@thalesians.com

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

from chartpy import Chart, Style, ChartConstants
from findatapy.util.dataconstants import DataConstants
from findatapy.market import Market, MarketDataRequest, MarketDataGenerator
from findatapy.timeseries import Calculations

import datetime

from datetime import timedelta

dataconstants = DataConstants()


class QuickChart(object):
    """Displays charts from downloaded data, in a single line code call. Ideal for quickly generating charts from sources
    including Bloomberg, Quandl, ALFRED/FRED etc.

    """

    def __init__(
            self,
            engine="plotly",
            data_source="bloomberg",
            market_data_generator=MarketDataGenerator(),
    ):
        self._chart = Chart(engine=engine)
        self._market = Market(market_data_generator=market_data_generator)
        self._data_source = data_source

    def plot_chart(
        self,
        tickers=None,
        tickers_rhs=None,
        start_date=None,
        finish_date=None,
        chart_file=None,
        chart_type="line",
        title="",
        fields={"close": "PX_LAST"},
        freq="daily",
        source="Web",
        brand_label="Cuemacro",
        display_brand_label=True,
        reindex=False,
        yoy=False,
        plotly_plot_mode="offline_png",
        quandl_api_key=dataconstants.quandl_api_key,
        fred_api_key=dataconstants.fred_api_key,
        alpha_vantage_api_key=dataconstants.alpha_vantage_api_key,
        df=None,
    ):

        if start_date is None:
            start_date = datetime.datetime.utcnow().date() - timedelta(days=60)
        if finish_date is None:
            finish_date = datetime.datetime.utcnow()

        if isinstance(tickers, str):
            tickers = {tickers: tickers}
        elif isinstance(tickers, list):
            tickers_dict = {}

            for t in tickers:
                tickers_dict[t] = t

            tickers = tickers_dict

        if tickers_rhs is not None:
            if isinstance(tickers_rhs, str):
                tickers_rhs = {tickers_rhs: tickers_rhs}
            elif isinstance(tickers, list):
                tickers_rhs_dict = {}

                for t in tickers_rhs:
                    tickers_rhs_dict[t] = t

                tickers_rhs = tickers_rhs_dict

            tickers.update(tickers_rhs)
        else:
            tickers_rhs = {}

        if df is None:
            md_request = MarketDataRequest(
                start_date=start_date,
                finish_date=finish_date,
                freq=freq,
                data_source=self._data_source,
                tickers=list(tickers.keys()),
                vendor_tickers=list(tickers.values()),
                fields=list(fields.keys()),
                vendor_fields=list(fields.values()),
                quandl_api_key=quandl_api_key,
                fred_api_key=fred_api_key,
                alpha_vantage_api_key=alpha_vantage_api_key,
            )

            df = self._market.fetch_market(md_request=md_request)

        df = df.fillna(method="ffill")
        df.columns = [x.split(".")[0] for x in df.columns]

        style = Style(
            title=title,
            chart_type=chart_type,
            html_file_output=chart_file,
            scale_factor=-1,
            height=400,
            width=600,
            file_output=datetime.date.today().strftime("%Y%m%d") + " " + title +
            ".png",
            plotly_plot_mode=plotly_plot_mode,
            source=source,
            brand_label=brand_label,
            display_brand_label=display_brand_label,
        )

        if reindex:
            df = Calculations().create_mult_index_from_prices(df)

            style.y_title = "Reindexed from 100"

        if yoy:
            if freq == "daily":
                obs_in_year = 252
            elif freq == "intraday":
                obs_in_year = 1440

            df_rets = Calculations().calculate_returns(df)
            df = (Calculations().average_by_annualised_year(
                df_rets, obs_in_year=obs_in_year) * 100)

            style.y_title = "Annualized % YoY"

        if list(tickers_rhs.keys()) != []:
            style.y_axis_2_series = list(tickers_rhs.keys())
            style.y_axis_2_showgrid = False
            style.y_axis_showgrid = False

        return self._chart.plot(df, style=style), df
