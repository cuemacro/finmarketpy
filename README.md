# PyThalesians

PyThalesians is a Python financial library developed by the Thalesians (http://www.thalesians.com). Whilst elements of 
the project will remain proprietary (such as our proprietary trading algorithms), we are keen to publish many of the 
more generic elements to the community, many of whom have encouraged me to publish my code.

At present the latest open source version of PyThalesians offers:
* Backtesting of systematic trading strategies for cash markets
* Sensitivity analysis for systematic trading strategies parameters
* Seamless historic data downloading from Bloomberg (requires licence), Yahoo, Quandl, Dukascopy and other market data sources
* Produces beautiful line plots with PyThalesians wrapper (via Matplotlib), Plotly (via cufflinks) and a simple wrapper for Bokeh
* Basic seasonality analysis of markets
* Calculates some technical indicators and gives trading signals based on these
* Helper functions built on top of Pandas
* Automatic tweeting of charts
* And much more!
* Please bear in mind at present PyThalesians is currently a highly experimental alpha project and isn't yet fully 
documented
* Uses Apache 2.0 licence

The proprietary version of PyThalesians also has:

* Comprehensive backtesting systematic trading strategies for cash markets
* Analysis of intraday price action around data events
* Comprehensive number crunching of FX volatility market around data events
* Backtesting systematic trading strategies in FX vanilla options
* Elegant caching framework for historical market data
* Proprietary trading algorithms used in my own personal trading - which will not be open sourced :-)

# Gallery

Below we give some examples of analysis which we've done using the full code of PyThalesians (which currently includes more features than the open source version).

*Using PyThalesians to create a simple FX trend following strategy (in open source version - you can run this 
backtest using cashbacktest_examples.py)*

<img src="https://raw.github.com/thalesians/pythalesians/master/pythalesians_examples/fx-trend-example.png" width="543"/>

*Using PyThalesians to plot & calculate USD/JPY intraday moves around non-farm payrolls over past 10 years*

<img src="https://raw.github.com/thalesians/pythalesians/master/pythalesians_examples/usdjpy-nfp-delta.png" width="543"/>

*Using PyThalesians to calculate intraday vol in major FX crosses by time of day*

<img src="https://raw.github.com/thalesians/pythalesians/master/pythalesians_examples/fx-intraday-vol.png" width="543"/>

*Using PyThalesians to create the Thalesians CTA index (trend following), which replicates Newedge CTA index benchmark 
(in closed source version)*

<img src="https://raw.github.com/thalesians/pythalesians/master/pythalesians_examples/replicating-cta.png" width="543"/>

*Using PyThalesians with Cufflinks (Plotly wrapper) to plot interactive Plotly chart (using plotly_examples.py) - click the below to get to the interactive chart*
<div>
    <a href="https://plot.ly/~thalesians/867/" target="_blank" title="S&amp;P500 vs Apple" style="display: block; text-align: center;"><img src="https://plot.ly/~thalesians/867.png" alt="S&amp;P500 vs Apple" style="max-width: 100%;width: 580px;"  width="580" onerror="this.onerror=null;this.src='https://plot.ly/404.png';" /></a>
    <script data-plotly="thalesians:867"  src="https://plot.ly/embed.js" async></script>
</div>

*Using PyThalesians to plot via Bokeh EUR/USD in the 3 hours following FOMC statements
(plotting in open source version, calculations in closed source version)*

<img src="https://raw.github.com/thalesians/pythalesians/master/pythalesians_examples/bokeh-complex-example.png" width="543"/>

*Using PyThalesians to plot combination of bar/line/scatter for recent equity returns
(in open source version - you can run this analysis using bokeh_examples.py)*

<img src="https://raw.github.com/thalesians/pythalesians/master/pythalesians_examples/bokeh-bar-example.png" width="543"/>

*Using PyThalesians and PyFolio to plot return statistics of FX CTA strategy
(in open source version - you can run this analysis using strategyfxcta_example.py)*

<img src="https://raw.github.com/thalesians/pythalesians/master/pythalesians_examples/tradeanalysis-stat.png" width="543"/>

*Using PyThalesians to plot with Plotly map of USA unemployment rate by state (using FRED data)
(in open source version - you can run this analysis using histecondata_examples.py)*

<img src="https://raw.github.com/thalesians/pythalesians/master/pythalesians_examples/usa-states-unemployment-rate.png" width="543"/>

*Using PyThalesians to plot G10 CPI YoY rates (using FRED data)
(in open source version - you can run this analysis using histecondata_examples.py)*

<img src="https://raw.github.com/thalesians/pythalesians/master/pythalesians_examples/g10-cpi.png" width="543"/>

*Using PyThalesians to plot rolling correlatons in FX (using Bloomberg data)
(in open source version - you can run this analysis using correlation_examples.py)*

<img src="https://raw.github.com/thalesians/pythalesians/master/pythalesians_examples/rolling-correlations.png" width="543"/>

*Using PyThalesians to plot seconds data around last NFP (using Bloomberg data)
(in open source version - you can run this analysis using tick_examples.py)*

<img src="https://raw.github.com/thalesians/pythalesians/master/pythalesians_examples/second-download.png" width="543"/>

*Using PyThalesians to plot AUD/USD total returns from spot & deposit data (comparing with spot and Bloomberg
generated total return index) (in open source version - you can run this analysis using indicesfx_examples.py)*

<img src="https://raw.github.com/thalesians/pythalesians/master/pythalesians_examples/audusd-total-returns.png" width="543"/>

# Requirements

PyThalesians has been tested on Windows 8 & 10, running Bloomberg terminal software. Potentially, it could also work on the 
Bloomberg Server API (but I have not explicitly tested this).

Major requirements
* Required: Python 3.4+
* Required: pandas, matplotlib, numpy etc.
* Recommended: Bloomberg Python Open API
    * Use experimental Python 3.4 version from Bloomberg http://www.bloomberglabs.com/api/libraries/
    * Might need to tweak registry to avoid "Python 3.4 not found in registry error" (blppython.reg example)
    * Alternatively to access Bloomberg, the software also supports the old COM API (but this deprecated)
    * To use Bloomberg you will need to have a installed licence
* Recommended: Plotly for funky interactive plots (https://github.com/plotly/python-api) and 
* Recommended: Cufflinks a nice Plotly
wrapper when using Pandas dataframes (Jorge Santos project now supports Python 3 
https://github.com/jorgesantos/cufflinks - so I recommend using that rather than my fork)
* Recommended: PyFolio for statistical analysis of trading strategy returns (https://github.com/quantopian/pyfolio/)
* Recommended: multiprocessor_on_dill because standard multiprocessing library pickle causes issues 
(from https://github.com/sixty-north/multiprocessing_on_dill)

# Installation

Once installed please make sure you edit pythalesians.util.constants file for the following variables:
* Change the root path variable - this will ensure that the logging (and a number of other features works correctly). 
Failure to do so will result in the project not starting
* Change the default Bloomberg settings (Which API to use? What server address to use?)
* Write in API keys for Quandl, Twitter, Plotly etc.
* Latest version can be installed using setup.py or pip (see below)

```
pip install git+https://github.com/thalesians/pythalesians.git
```

# Examples for PyThalesians

After installation, the easiest way to get started is by looking at the example scripts. I am hoping to add some Jupyter notebooks, illustrating how to use the library too. The example scripts show how to:

* Download market data from many different sources, Bloomberg, Yahoo, Quandl, Dukascopy etc
* Plot line charts, with different styles

# About the Thalesians

The Thalesians are a think tank of dedicated professionals with an interest in quantitative finance, economics, 
mathematics, physics and computer science, not necessarily in that order. We run quant finance events in London, New York,
Budapest, Prague and Frankfurt (join our Meetup.com group at http://events.thalesians.com). We also publish research
on systematic trading and also consult in the area. One of our clients is RavenPack, a major news analytics vendor.

# Major contributors to PyThalesians

* Saeed Amen - Saeed is managing director and co-founder of the Thalesians. He has a decade of experience creating and successfully running systematic trading models at Lehman Brothers and Nomura. Independently, he runs a systematic trading model with proprietary capital. He is the author of Trading Thalesians – What the ancient world can teach us about trading today (Palgrave Macmillan). He graduated with a first class honours master’s degree from Imperial College in Mathematics and Computer Science. He is also a co-founder of Argonautae.

# Supporting PyThalesians project

If you find PyThalesians useful (and in particular if you are commercial company) please consider supporting the project
through sponsorship or by using our consultancy/research services in systematic trading. If you would like to contribute to the project, also let me know.

For the UK election Plot.ly code - please visit https://github.com/plotly/IPython-plotly/tree/master/notebooks/ukelectionbbg

# Future Plans for PyThalesians

We plan to add the following features:
* Have a proper setup mechanism (eg. via pip), at present needs (partial) manual deployment
* Add Plotly & Seaborn wrappers for plotting (partially there)
* Improve support for Bokeh plotting (partially)
* Add more plots from Matlibplot
* Add Reuters as a historic data source
* Add ability to stream data from Bloomberg and Reuters
* Use event driven code to generate trading signals (to be used live and historically)
* Add more interesting trading analysis tools
* Add support for live trading via Interactive Brokers
* Integrate support for zipline as an alternative trading system
* Improve support for PyFolio
* Support Python 2.7+

More generally, we want to:
* Make existing code more robust
* Increase documentation and examples

# Release Notes

* 0.1a (highly experimental alpha version) - 01 Jul 2015
* Basic implementation of plotting for line charts
* Basic downloading of market data like Bloomberg/Yahoo etc. via generic wrapper

# Coding log

* 01 Feb 2016 - Added LightEventsFactory to make it easier to deal with econ data events (stored as HDF5 files)
* 20 Jan 2016 - Added kurtosis measure for trading strategy results, fixed Quandl issue
* 19 Jan 2016 - Changed examples folder name
* 15 Jan 2016 - Added risk on/off FX correlation example
* 05 Jan 2016 - Added total return (spot) indices construction for FX and example
* 26 Dec 2015 - Fixed problem with econ data downloaders
* 24 Dec 2015 - Added datafactory templates for creating custom indicators
* 19 Dec 2015 - Refactored Dukascopy downloader
* 10 Dec 2015 - Various bug fixes
* 22 Nov 2015 - Increased vol targeting features for doing backtesting
* 07 Nov 2015 - Added feature to download tick data from Bloomberg (with example)
* 05 Nov 2015 - Added intraday event study class (and example)
* 02 Nov 2015 - Added easy wrapper for doing rolling correlations (and example)
* 28 Oct 2015 - Added more sensitivity analysis for trading strategies
* 26 Oct 2015 - Various bug fixes for Bloomberg Open API downloader
* 14 Oct 2015 - Added capability to do parallel downloading of market data (thread/multiprocessing library), with an 
example for benhcmarking and bug fixes for Bloomberg downloader
* 25 Sep 2015 - Refactored examples into different folders / more seasonality examples
* 19 Sep 2015 - Added support for Plotly choropleth map plots & easy downloading of economic data via FRED/Bloomberg/Quandl
* 12 Sep 2015 - Added basic support for PyFolio for statistical analysis of strategies
* 04 Sep 2015 - Added StrategyTemplate for backtesting (with example) & bug fixes
* 21 Aug 2015 - Added stacked charts (with matplotlib & bokeh) & several bug fixes
* 15 Aug 2015 - Added bar charts (with matplotlib & bokeh) & added more time series filter functions
* 09 Aug 2015 - Improved Bokeh support
* 07 Aug 2015 - Added Plotly support (via Jorge Santos Cufflinks wrapper)
* 04 Aug 2015 - Added ability to download from FRED and example for downloading from FRED.
* 29 Jul 2015 - Added backtesting functions (including simple FX trend following strategy) and various bug fixes/comments.
* 24 Jul 2015 - Added functions for doing simple seasonality studies and added examples.
* 17 Jul 2015 - Created example to show how to use technical indicators.
* 13 Jul 2015 - Changed location of conf, renamed examples folder to pythalesians_examples. Can now be installed using setup.py.
* 10 Jul 2015 - Added ability to download Dukascopy FX tick data (data is free for personal use - check Dukascopy terms & conditions). Note that past month of data is generally not made available by Dukascopy

End of note
