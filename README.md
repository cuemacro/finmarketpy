<img src="finmarketpy_logo.png?raw=true" width="300"/>

# [finmarketpy (formerly pythalesians)](https://github.com/cuemacro/finmarketpy)

finmarketpy is a Python based library that enables you to analyze market data and also to backtest trading strategies using
a simple to use API, which has prebuilt templates for you to define backtest. Included in the library

* Prebuilt templates for backtesting trading strategies
* Display historical returns for trading strategies
* Investigate seasonality of trading strategies
* Conduct market event studies around data events
* In built calculator for risk weighting using volatility targeting
* Written in object oriented way to make code more reusable

*Contributors for the project are very much welcome, see below!*

# Merging with pythalesians
I had previously written the open source PyThalesians financial library (which has been merged with this - so can focus on maintaining
one set of libraries). This new finmarketpy library has 
* Similar functionality to the trading part of pythalesians
* Rewritten the API to make it much cleaner and easier to use, as well as having many 
new features. 
* finmarketpy requires the libraries, which I've written chartpy (for charts) and findatapy (for loading market data) to function
* By splitting up into smaller more specialised libraries, it should make it easier for contributors
* Using findatapy, you can download market data easily from Bloomberg, Quandl, Yahoo etc
* Using chartpy, you can choose to have results displayed in matplotlib, plotly or bokeh by changing single keyword!

Points to note:
* Please bear in mind at present finmarketpy is under continual development. The API is heavily documented, but we are
looking to add more general documentation.
* Uses Apache 2.0 licence

# Gallery

Calculate the cumulative returns of a trading strategy historically (see finmarketpy_examples/tradingmodelfxtrend_example.py)

<img src="finmarketpy_examples/gallery/fx-trend-cumulative.png?raw=true" width="750"/>

Plot the leverage of the strategy over time

<img src="finmarketpy_examples/gallery/fx-trend-leverage.png?raw=true" width="750"/>

Plot the individual trade returns

<img src="finmarketpy_examples/gallery/fx-trend-trade-returns.png?raw=true" width="750"/>

Calculate seasonality of any asset: here we show gold and FX volatility seasonality (see examples/seasonality_examples.py)

<img src="finmarketpy_examples/gallery/gold-seasonality.png?raw=true" width="750"/>

<img src="finmarketpy_examples/gallery/fx-vol-seasonality.png?raw=true" width="750"/>

Calculate event study around events for asset (see examples/events_examples.py)

<img src="finmarketpy_examples/gallery/usdjpy-nfp.png?raw=true" width="750"/>


# Requirements

Major requirements
* Required: Python 3.6
* Required: pandas 0.24.2, numpy etc.
* Required: findatapy for downloading market data (https://github.com/cuemacro/findatapy)
* Required: chartpy for funky interactive plots (https://github.com/cuemacro/chartpy)

# Installation

For detailed installation instructions for finmarketpy and its associated Python libraries go to
https://github.com/cuemacro/finmarketpy/blob/master/INSTALL.md (which includes details on how to setup your entire Python environment).

Also take a look at https://github.com/cuemacro/teaching/blob/master/pythoncourse/installation/installing_anaconda_and_pycharm.ipynb
from my Python for finance workshop course, where I keep notes specifically about setting up your Anaconda environment 
for data science (including for findatapy/chartpy/finmarketpy), including YAML files etc.

You can install the library using the below (better to get the newest version from repo, as opposed to releases).

After installation:
* Make sure you edit the marketconstants.py file (or you can create a marketcred.py file to overwrite the settings)

```
pip install git+https://github.com/cuemacro/finmarketpy.git
```

But beforehand please make sure you have already installed both chartpy, findatapy and any other dependencies. 
In chartpy you will need to change the chartconstants.py file (to add Plotly API key) and 
for findatapy, you will also need to change the dataconstants.py file to add the Quandl API 
(and possibly change other configuration settings there or add a datacred.py file in the util folder, 
alternatively you will be prompted on your first run to input the API key which will be installed).

```
pip install git+https://github.com/cuemacro/chartpy.git
pip install git+https://github.com/cuemacro/findatapy.git
```

# Contributors

Contributors are always welcome for finmarketpy, findatapy and chartpy. If you'd like to contribute, have a look at
[Planned Features](PLANNED_FEATURES.md) for areas we're looking for help on. Or if you have any ideas for improvements
to the libriares please let us know too!

# finmarketpy examples

In finmarketpy/examples you will find several examples, including some simple trading models

# Release Notes

* 0.11.3 - finmarketpy (04 Dec 2019)
* 0.11.1 - finmarketpy (23 Oct 2019)
* 0.11 - finmarketpy
* First prerelease version 

# Coding log

# finmarketpy log

* 17 Dec 2019
    * Added link for Python for finance workshop installation notes for Anaconda
* 04 Dec 2019
    * Making blosc optional in BacktestEngine
* 14 Nov 2019
    * Added network plot
* 02 Nov 2019 
    * Fixed bug running on Mac
    * Updated installation instructions
    * Added tests for technical indicators
    * Added backtestcomparison.py
* 29 Mar 2019 - Added variable transaction costs
* 14 Nov 2018 - Fixed contract bug in backtest_example
* 18 Sep 2018 - Fixed bug on writing PnL CSV
* 17 Sep 2018 - Added rounding for trade size display (otherwise trades can be ungrounded because of rounding errors)
* 11 Jun 2018 - Fixed bug with single threaded TradeAnalysis
* 29 May 2018 - Added port
* 25 Apr 2018
    * Added (some) parallel features for backtesting and sensitivity analysis (works better in Linux)
    * Added different transaction costs by assets
    * Fixed backtesting examples so work with "run_in_parallel" keyword and can customise BacktestRequest more
* 18 Apr 2018 - Fix bug with trade notional sizes
* 06 Apr 2018 - Added function to measure freq of trade notional sizes
* 29 Mar 2018 - Fix bug when dumping CSV of P&L
* 15 Mar 2018 - Added caching for event data
* 26 Feb 2018 - Added solution for replacing parameters under tech_params (in tradeanalysis.py).
* 30 Jan 2018 - Fix bug on backtest.example.py
* 25 Jan 2018 - Fix bug on class
* 04 Jan 2018 - Bug fix for Cred override of constants
* 16 Sep 2017 - Adding to planned features list
* 10 Jul 2017 - Added install instructions for conda
* 03 Jul 2017 - Fixed dependency on seasonal library
* 26 Jun 2017 - BacktestEngine can now handle weighted sum style portfolios
* 23 Jun 2017 - Downloads observation date for economic data (EventStudy)
* 21 Jun 2017 - Added trend following example using Bloomberg total return data
* 07 Jun 2017 - Added output of IR/Rets in sensitivity analysis (TradeAnalysis)
* 22 May 2017 - Output returns of strategy (to CSV file)
* 03 May 2017 - Added more planned features
* 13 Apr 2017 - Changed finish date on FX trend following model
* 12 Mar 2017 - Added FX vol surface animation example
* 25 Feb 2017 - Added signal delay parameter
* 24 Feb 2017 - Refactored backtesting classes so have consistent naming
* 21 Feb 2017 - Refactored BacktestEngine to use SwimPool
* 20 Feb 2017 - Extra install instructions
* 14 Feb 2017 - Added Planned Features page
* 08 Feb 2017 - Added SHOW_CHARTS parameter for TradingModel and made SMA work with old pandas
* 05 Feb 2017 - Added more installation notes and fixed Excel output in TradeAnalysis if notional not specified
* 02 Feb 2017 - Further changes to constraints on max long/shorts (with refactoring)
* 01 Feb 2017 - Added constraints for max longs/shorts and plots in BacktestEngine
* 25 Jan 2017 - Additional work on stops/take profit with multiple assets & plotting bug fixes for TradeAnalysis
* 24 Jan 2017 - Fixing issues around stops/take profits and adding fields in TechParams
* 19 Jan 2017 - Change location of examples in project
* 16 Jan 2017 - Added method in BacktestEngine for debugging of P&L (dumps table with signals/assets/returns)
* 12 Jan 2017 - Added detailed installation notes
* 11 Jan 2017 - Rewrote large number of comments, added ATR calculation and basic stop loss/take profit functionality
* 07 Jan 2017 - Now outputs position sizes scaled by notional & by user defined contract sizes
* 06 Jan 2017 - Added user defined weightings for strategies & general bug fixes
* 04 Jan 2017 - Added a period shift parameter for calculating leverage (in RiskEngine)
* 30 Nov 2016 - Added seasonality example for NFP
* 24 Nov 2016 - Added seasonality example for gasoline
* 17 Nov 2016 - Changed source to ChartConstants default for TradingModel
* 14 Oct 2016 - Fixed arctic references in MarketConstants
* 13 Oct 2016 - Fixed IR plotting for BacktestEngine, added YoY metric plots
* 11 Oct 2016 - Added to TradeAnalysis another way to plot return statistics for a portfolio
* 10 Oct 2016 - Added returns_example to show how to use PyFolio via finmarketpy, added dataframe input for TradeAnalysis, fixed typo in readme
* 07 Oct 2016 - Add .idea to .gitignore
* 06 Oct 2016 - Split out plotting of no of trades and position proportion
* 22 Sep 2016 - Fixed sorting of columns when signal plotting
* 21 Sep 2016 - Allow plotting of multiple signal days
* 15 Sep 2016 - Merged finmarketpy and pythalesians fully, released version 0.11
* 12 Sep 2016 - Fixed issue with TradeAnalysis (method names)
* 02 Sep 2016 - Fixed issue with external dataframe eco events, added event study example
* 01 Sep 2016 - Added seasonality example for FX vol
* 22 Aug 2016 - Fixed boot issue and added credentials
* 17 Aug 2016 - Uploaded first code

# pythalesians log

* 03 Aug 2016 - Fixed missing conf files
* 02 Aug 2016 - Changed default Plotly background color and fixed constants issue with AdapterTemplate
* 01 Aug 2016 - Renamed pythalesians_graphics as chartesians (preparing eventual spinout)
* 29 Jul 2016 - Created Jupyter notebook plot_market_data for plotting with multiple libraries, also fixed Bokeh sizing issue,
refactored library, spinning out chart functionality into pythalesians_graphics
* 28 Jul 2016 - Fixed issue with multiple fields returned by Quandl, added Quandl downloading example
* 26 Jul 2016 - Added more support for Plotly charts, added surface vol Plotly example
* 21 Jul 2016 - Refactor StrategyTemplate graph plotting functions
* 20 Jul 2016 - Return of figure handle for AdapterPyThalesians
* 08 Jun 2016 - Fix kurtosis issue, refactored vol scaling in CashBasktest, added resample wrapper in TimeSeriesFilter
* 03 Jun 2016 - Speed up CashBacktest (construct_strategy method)  
* 02 Jun 2016 - Fixed missing StrategyTemplate file in installation, added auto-detection of path 
to simplify installation and added methods for converting between pandas and bcolz
* 31 May 2016 - Got rid of deprecated Pandas methods in TechIndicator
* 27 May 2016 - Added ability to plot strategy signal at point in time
* 19 May 2016 - Updated Quandl wrapper to use new Quandl API
* 02 May 2016 - Tidied up BacktestRequest, added SPX seasonality example
* 28 Apr 2016 - Updated cashbacktest (for Pandas 0.18)
* 21 Apr 2016 - Got rid of deprecated Pandas methods in EventStudy
* 18 Apr 2016 - Fixed some incompatibility issues with Pandas 0.18
* 06 Apr 2016 - Added more trade statistics output
* 01 Apr 2016 - Speeded up joining operations, noticeable when fetching high freq time series
* 21 Mar 2016 - Added IPython notebook to demonstrate how to backtest simple FX trend following trading strategy
* 19 Mar 2016 - Tested with Python 3.5 64 bit (Anaconda 2.5 on Windows 10)
* 17 Mar 2016 - Refactored some of graph/time series functions and StrategyTemplate
* 11 Mar 2016 - Fixed warnings in matplotlib 1.5
* 09 Mar 2016 - Added more TradeAnalysis features (for sensitivity analysis of trading strategies)
* 01 Mar 2016 - Added IPython notebook to demonstrate how to download market data and plot
* 27 Feb 2016 - Fixed total returns FX example
* 20 Feb 2016 - Added more parameters for StrategyTemplate
* 13 Feb 2016 - Edited time series filter methods
* 11 Feb 2016 - Added example to plot BoJ interventions against USDJPY spot
* 10 Feb 2016 - Updated project description
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
example for benchmarking and bug fixes for Bloomberg downloader
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
