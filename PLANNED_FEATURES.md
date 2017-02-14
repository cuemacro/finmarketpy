# Planned features for finmarketpy, findatapy and chartpy

Whilst the finmarketpy, findatapy and chartpy projects have been going in various forms for a few years, we have a large
wishlist of features and improvements to add (in addition to general bug fixes). If you are looking to contribute to any
of these projects, any of these features would be a great place to start.

## finmarketpy plans

* Speeding up BacktestEngine class (possibly via using multiprocessor_on_dill library, but also accelerating computation of returns,
return statistics etc)
* Add more market analysis types in the economics folder including
    * Proper seasonality analysis (eg. decompose into seasonal and trend components)
* Add basic event driven backtester on top
* Adding tests based on pytest

## findatapy plans

* Add data wrappers for other data providers
    * Thomson Reuters
    * Macrobond
    * And any others we can think of!
* Add subscription style data downloading for
    * Bloomberg
    * Thomson Reuters
    * And more
* Improve DataQuality class
* Adding tests based on pytest

## chartpy plans

* Add a wrapper for bqplot (Bloomberg's open source plotting library designed for Jupyter notebook)
* Add a wrapper for vispy, high performance GPU accelerated
* Add more chart types across the various engines, in particular for matplotlib including FOMC style dotplot (aka beeswarm plot)
* Adding tests based on pytest (although guess this is tricky?)