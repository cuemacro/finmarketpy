# Planned features for finmarketpy, findatapy and chartpy

Whilst the finmarketpy, findatapy and chartpy projects have been going in various forms for a few years, we have a large
wishlist of features and improvements to add (in addition to general bug fixes). If you are looking to contribute to any
of these projects, any of these features would be a great place to start. I've tried to focus the new features on areas
which I would find useful in my market analysis, but of course I'm sure I've missed many potential features here.

## finmarketpy plans

* Speeding up BacktestEngine class (possibly via using multiprocessor_on_dill library, but also accelerating computation of returns,
return statistics, for example through using GPU accelerated code for cases when we multiply matrices etc.)
* Add more market analysis types in the economics folder including
    * Proper seasonality analysis (eg. decompose into seasonal and trend components)
* More statistics for trading result output (including ability to create fully encapsulated HTML files?)
* Adding tests based on pytest
* Add more examples to demonstrate API usage
* Use Sphinx to create HTML API files (readthedocs)
* Add basic event driven backtester on top (possibly) with a wrapper for Interactive Brokers - low priority at this stage

## findatapy plans

* Add data wrappers for other data providers:
    * Thomson Reuters
    * Alpha Vantage
    * Macrobond
    * And any others we can think of!
* Add subscription style data listening to data from:
    * Bloomberg
    * Thomson Reuters
    * And more
* Improve DataQuality class for evaluating data quality
* Adding tests based on pytest
* Add more examples
* Use Sphinx to create HTML API files (readthedocs)

## chartpy plans

* Add a wrapper for bqplot (Bloomberg's open source plotting library designed for Jupyter notebook)
* Add a wrapper for vispy, high performance GPU accelerated (partially done)
* Add more chart types across the various engines, in particular for plotly and matplotlib including FOMC style dotplot (aka beeswarm plot)
* Add more animated chart types (surface currently implemented for matplotlib, want to add for plotly)
* Adding tests based on pytest (although guess this is tricky, given output is graphical)
* Add more examples
* Use Sphinx to create HTML API files (readthedocs)
