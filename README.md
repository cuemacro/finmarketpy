# finmarketpy

finmarketpy is a Python based library that enables you to analyze market data and also to backtest trading strategies using
a simple to use API, which has prebuilt templates for you to define backtest. Included in the library

* Prebuilt templates for backtesting trading strategies
* Display historical returns for trading strategies
* Investigate seasonality of trading strategies
* Conduct market event studies around data events
* In built calculator for risk weighting using volatility targeting
* Written in object orientated way to make code more reusable

I had previously written the open source PyThalesians financial library. This new finmarketpy library has similar functionality to the 
trading part of that library. However, I've totally rewritten the API to make it much cleaner and easier to use, as well as having many 
new features. It requires the libraries, which I've written chartpy (for charts) and findatapy (for loading market data) to function.

* Using findatapy, you can download market data easily from Bloomberg, Quandl, Yahoo etc
* Using chartpy, you can choose to have results displayed in matplotlib, plotly or bokeh by changing single keyword!

Points to note:
* Please bear in mind at present finmarketpy is currently a highly experimental alpha project and isn't yet fully 
documented
* Uses Apache 2.0 licence

# Gallery

Calculate the cumulative returns of a trading strategy historically (see examples/tradingmodelfxtrend_example.py)

<img src="https://github.com/cuemacro/finmarketpy/blob/master/finmarketpy/examples/gallery/fx-trend-cumulative.png?raw=true" width="750"/>

Plot the leverage of the strategy over time

<img src="https://github.com/cuemacro/finmarketpy/blob/master/finmarketpy/examples/gallery/fx-trend-leverage.png?raw=true" width="750"/>

Plot the individual trade returns

<img src="https://github.com/cuemacro/finmarketpy/blob/master/finmarketpy/examples/gallery/fx-trend-trade-returns.png?raw=true" width="750"/>

Calculate seasonality of any asset: here we show gold and FX volatility seasonality (see examples/seasonality_examples.py)

<img src="https://github.com/cuemacro/finmarketpy/blob/master/finmarketpy/examples/gallery/gold-seasonality.png?raw=true" width="750"/>

<img src="https://github.com/cuemacro/finmarketpy/blob/master/finmarketpy/examples/gallery/fx-vol-seasonality.png?raw=true" width="750"/>

Calculate event study around events for asset (see examples/events_examples.py)

<img src="https://github.com/cuemacro/finmarketpy/blob/master/finmarketpy/examples/gallery/usdjpy-nfp.png?raw=true" width="750"/>


# Requirements

Major requirements
* Required: Python 3.4, 3.5
* Required: pandas 0.18, numpy etc.
* Required: findatapy for downloading market data (https://github.com/cuemacro/findatapy)
* Required: chartpy for funky interactive plots (https://github.com/cuemacro/chartpy)
* Recommended: multiprocessor_on_dill because standard multiprocessing library pickle causes issues 
(from https://github.com/sixty-north/multiprocessing_on_dill)

# Installation

You can install the library using the below. After installation:
* Make sure you edit the MarketConstants file

```
pip install git+https://github.com/cuemacro/finmarketpy.git
```

But beforehand please make sure you have already installed both chartpy, findatapy and any other dependencies

```
pip install git+https://github.com/cuemacro/chartpy.git
pip install git+https://github.com/cuemacro/findatapy.git
```

# finmarketpy examples

In finmarketpy/examples you will find several examples, including some simple trading models

# Release Notes

* No formal releases yet

# Coding log

* 12 Sep 2016 - Fixed issue with TradeAnalysis (method names)
* 02 Sep 2016 - Fixed issue with external dataframe eco events, added event study example
* 01 Sep 2016 - Added seasonality example for FX vol
* 22 Aug 2016 - Fixed boot issue and added credentials
* 17 Aug 2016 - Uploaded first code

End of note
