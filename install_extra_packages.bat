REM this will install all of the dependencies used by chartpy, findatapy and finmarketpy (other than the actual libraries themselves)
pip install numpy, pandas, pytz, request, multiprocess, pandas_datareader, quandl, redis, openpxyl, blosc, bokeh, plotly, cufflinks, matplotlib, git+https://github.com/manahl/arctic.git
pip install git+https://github.com/cuemacro/chartpy.git
pip install git+https://github.com/cuemacro/findatapy.git
pip install git+https://github.com/cuemacro/finmarketpy.git