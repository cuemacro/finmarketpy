# Installation of Cuemacro Python libraries (finmarketpy, findatapy and chartpy)

In order to install the Cuemacro Python libraries, I would recommend following the instructions below. If you already have Python 3.5 installed,
you can skip most of these steps. The below instructions assume that you have not installed Python at all and are assuming you have Windows.

At the end I also have comments related to installing finmarketpy, findatapy and chartpy on Linux and OS X.

In general, I would go in the order suggested here. Some components are optional (such as Bloomberg software).

Before installation of any specific Python libraries, we need to set up the core Python distribution and other programming tools,
which will help you to write your own trading strategies and Python scripts for doing market analysis on top of the Cuemacro libraries.

* Programming Tools
    * Anaconda 64 bit Python - [download](https://www.continuum.io/downloads) - Windows/Linux/Mac OS X
      * This is the most used Python distribution for data science
      * As well as installing the core Python libraries, it also installs many useful libraries like the SciPy stack, which
    contains NumPy, pandas etc. and many other useful libraries like matplotlib which are dependencies for the various Cuemacro libraries
      * Recommend installing latest version of Python 3.7 (by running in command line `conda install python=3.7`) as some of the multiprocessing libraries have issues with Python 3.6 at present when I've tried it
      * findatapy, chartpy and finmarketpy should be compatible with the dependencies in Anaconda (eg. version of pandas, numpy etc.)
    * Microsoft Visual Studio 2017 Community Edition - [download](https://www.visualstudio.com/downloads/) or Visual C++ 2015 build tools - Windows
      * Makes sure to do a custom installation and tick Visual C++ in the Visual Studio 2017 installation
      * Alternatively, it is quicker to install [Visual C++ 2017 build tools](http://landinghub.visualstudio.com/visual-cpp-build-tools)
         * You may need to add the following (or similar) to your Windows path `C:\Program Files (x86)\Windows Kits\8.1\bin\x64`
         * This should prevent the following compilation error where 'rl.exe' is not found
      * Some Python libraries need a C++ compiler in order to build (such as blpapi and arctic)
      * Often it is easier to install Python libraries using conda
      * Alternatively, if you don't want to compile the libraries yourself, you can sometimes find pre-compiled
      Python wheels for your platform
    * Git - https://git-scm.com/downloads - Windows/Linux/Mac OS X
        * Version control software
        * Makes it easier to maintain your own Python code
    * PyCharm Community Edition - [download](https://www.jetbrains.com/pycharm/download/) - Windows/Linux/Mac OS X
        * PyCharm is a relatively easy to use IDE for coding Python, with tools such as autocompletion
        and syntax highlighting
        * The Professional Edition also adds a few bells and whistles including a code profiler
        * I recommend running the 64 bit version, as I've the 32 bit version can run out memory particularly when building
        indices
        * There are many other alternative IDEs (and text editors) for Python, I recommend you also check out a few to see which you like most
        (or you just use a simple text editor like Notepad!)
            * Atom - [hackable text editor, which also has addins for Python coding](https://atom.io/)
            * PyDev - [Python IDE written on top of Eclipse](http://www.pydev.org/)
            * Sublime - [text editor](http://www.sublimetext.com/3)

* Data tools
    * MongoDB - [download](https://www.mongodb.com/download-center) - Windows/Linux/Mac OS X
        * IOEngine class has a wrapper over arctic to use MongoDB (as well as HDF5 files if preferred)
        * Be sure to setup a database in MongoDB, if you wish to use it to store data later
    * Redis - [Download](https://redis.io/download) - Windows/Linux/Mac OS X
        * IOEngine class has a wrapper to use Redis, as a high level cache
        * Redis is an in-memory database designed for short term volatile storage
        * findatapy uses it as a high level cache to speed up access to repeatedly used datasets
    * Bloomberg Terminal - [download](https://www.bloomberg.com/professional/downloads/]) - Windows
        * Bloomberg provides a high quality data source
        * Note, you must be a subscriber for the software to function and to have a licence for the data
        * This also needs installation of your serial number
        * Bloomberg Terminal is only available for Windows
        * Bloomberg Server API is available for Windows/Linux/Mac OS X but runs under a different licence

* Fonts
    * Open Sans - chartpy uses the open source Open Sans family of fonts as default for matplotlib
    * You can download these for free from [Font Squirrel](https://www.fontsquirrel.com/fonts/open-sans)
    * Once downloaded you need to install them on your operating system
    * On Windows this involves copying the fonts to your Windows font folder (eg. C:\Windows\Fonts)
    * You need to delete matplotlib's font cache file, so it picks up the new font (eg. fontList.py3k.cache in
    C:\Users\User name\.matplotlib

Open up the Anaconda Command Prompt (accessible via the Start Menu) to run the various "conda" and "pip" commands to install the
various Python libraries. The Cuemacro libraries will install most Python dependencies, but some need to be installed separately.

* Install finmarketpy, findatapy and chartpy the easy way...
    * You can install some Python data science conda environments that I use for teaching
    which include finmarketpy, findatapy and chartpy
    * Instructions on how to install Anaconda and the py37class conda environment at 
    [https://github.com/cuemacro/teaching/blob/master/pythoncourse/installation/installing_anaconda_and_pycharm.ipynb](https://github.com/cuemacro/teaching/blob/master/pythoncourse/installation/installing_anaconda_and_pycharm.ipynb)

* Python libraries (open source)
    * arctic - `pip install arctic`
        * Wrapper for MongoDB (also installs pymongo)
        * Allows us to easily save and load pandas DataFrames in MongoDB
        * Also compresses data contents
    * blpapi - https://www.bloomberglabs.com/api/libraries/ (both C++ and Python libraries)
        * Interact with Bloomberg programmatically via Python to download historical and live data
        * Note that may need requires a C++ compiler to build the Python library 
        * Follow instructions at [https://github.com/cuemacro/findatapy/blob/master/BLOOMBERG.md](https://github.com/cuemacro/findatapy/blob/master/BLOOMBERG.md) for all the steps necessary to install blpapi
    * Whilst Anaconda has most of the dependencies below and pip will install all additional ones needed by the Cuemacro Python
    libraries it is possible to install them manually via pip, below is a list of the dependencies
        * all libraries
            * numpy - matrix algebra (Anaconda)
            * pandas - time series (Anaconda) - older versions of pandas could have issues due to deprecated methods - recommend 1.0.5
            * pytz - timezone management (Anaconda)
            * requests - accessing URLs (Anaconda)
            * mulitprocess - multitasking
            * multiprocessing_on_dill - multiprocessing on dill (similar to multiprocess, can select which library to use)
        * findatapy
            * pandas_datareader - accessing market data sources including Yahoo Finance (Anaconda)
            * quandl - accessing market data sources (Anaconda)
            * redis - Python wrapper to access Redis, in-memory database, like a hashtable (Anaconda Linux/Mac)
                * `brew reinstall redis` (Unix)
            * openpyxl - writing Excel spreadsheets to disk (Anaconda)
            * pyarrow - for caching 
            * keyring - for storing passwords
            * arctic - wrapper on MongoDB (see below for installation)
            * blpapi - Python API for Bloomberg (see below for installation)
            * xlsxwriter - writing Excel files from Python (and reading) (Anaconda)
        * chartpy
            * bokeh - visualisation (Anaconda)
            * cufflinks - wrapper on plotly
            * matplotlib - visualisation (Anaconda)
            * plotly - visualisation (Anaconda)
            * vispy - visualisation with GPU acceleration
            * twython - Twitter library for Python
        * You can install all of these, and also chartpy, findatapy and finmarketpy by running the install_packages.bat file on Windows

* Cuemacro Python libraries (open source)
    * Before we start, make sure we are familiar where your Anaconda site packages folder is (ie. where it will install your Python dependencies),
    as this will be where we need to edit the various configuration files described in this section.
        * Typically this is in folders like:
            * C:\Anaconda3\Lib\site-packages
            * C:\Program Files\Anaconda\Lib\site-packages
    * chartpy - `pip install chartpy`
        * Check constants file configuration [chartpy/chartpy/util/chartconstants.py](https://github.com/cuemacro/finmarketpy/blob/master/chartpy/util/chartconstants.py) for
            * Adding your own API keys for Plotly, Twitter etc
            * Changing the default size of plots
            * Changing the default chart engine (eg. Plotly, Bokeh or Matplotlib)
        * Alternatively you can create chartcred.py class in the same folder to put your own API keys
        * This has the benefit of not being overwritten each time you upgrade the project
    * findatapy - `pip install findatapy`
        * Check constants file configuration [findatapy/findatapy/util/dataconstants.py](https://github.com/cuemacro/finmarketpy/blob/master/findatatpy/util/dataconstants.py) for
            * adding your own API keys for Quandl etc.
            * changing path of your local data source (change `folder_time_series_data` attribute)
            * changing path of the config folder if necessary (change `config_root_folder` attribute) so you can create your own custom
            ticker library (otherwise it will get overwritten each time you upgrade findatapy)
            * changing the ticker library (placed in findatapy/findatapy/conf/*.CSV files)
                * time_series_categories_fields.csv - define the categories of tickers and what fields they have
                * time_series_fields_list.csv - define aliases for vendor fields
                * time_series_tickers_list.csv - defines aliases for vendor tickers
                * There are already setup with a few FX tickers to act as an example
                * In addition, you can add your own CSV files to accompany time_series_tickers_list.csv (add to time_series_tickers_list attribute)
                    * fx_vol_tickers.csv - samples of FX vol tickers
                    * fx_forward_tickers.csv - samples of FX forward tickers
            * changing logging.conf
                * For customising how the project dumps logs to disk
        * Alternatively you can create datacred.py class in the same folder to put your own API keys and file folder settings.
        * This has the benefit of not being overwritten each time you upgrade the project.
        * Below we have a sample datacred.py class file, to be placed in the "util" folder, any parameters set here, will overwrite
        those of dataconstants.py (note: for passwords if a datacred.py file is not created, it will use
        passwords stored in your keyring and will prompt you the very first time it is run):

        ```python
class DataCred(object):

    folder_historic_CSV = "E:/tickdata/historicCSV"
    folder_time_series_data = "C:/timeseriesdata"

    config_root_folder = "E:/Remote/yen/conf/"

    ###### FOR ALIAS TICKERS
    # config file for time series categories
    time_series_categories_fields = \
        config_root_folder + "conf/time_series_categories_fields.csv"

    # we can have multiple tickers files (separated by ";")
    time_series_tickers_list = config_root_folder + "conf/time_series_tickers_list.csv;" + \
                               config_root_folder + "conf/futures_contracts_tickers.csv"


    time_series_fields_list = config_root_folder + "conf/time_series_fields_list.csv"

    # config file for long term econ data
    all_econ_tickers = config_root_folder + "conf/all_econ_tickers.csv"
    econ_country_codes = config_root_folder + "conf/econ_country_codes.csv"
    econ_country_groups = config_root_folder + "conf/econ_country_groups.csv"

    default_market_data_generator = "marketdatagenerator"

    # Quandl settings
    quandl_api_key = "XYZ"

    # Twitter settings (you need to set these up on Twitter)
    TWITTER_APP_KEY = "XYZ"
    TWITTER_APP_SECRET = "XYZ"
    TWITTER_OAUTH_TOKEN = "XYZ"
    TWITTER_OAUTH_TOKEN_SECRET = "XYZ"

    # FRED API key
    fred_api_key = "XYZ"

    # database settings need to be filled in even if you aren't going to use one
    # main database settings
    db_server = '127.0.0.1'

    # cache database settings
    db_cache_server = '127.0.0.1'
    db_cache_port = '6379'
    write_cache_engine = 'redis'

    # Override multithreading for certain categories of downloads
    override_multi_threading_for_categories = []

    ```
    * finmarketpy - `pip install git+https://github.com/cuemacro/finmarketpy.git`
        * Check constants file configuration [finmarketpy/finmarketpy/util/marketconstants.py](https://github.com/cuemacro/finmarketpy/blob/master/finmarketpy/util/marketconstants.py)
        * You can also create your own file marketcred.py (placed in the same folder)

You can then setup your own separate project in PyCharm to create your own trading strategies on top of it. I'd recommend creating
a private (or public) project on GitHub so you can use it for version control and backup on the cloud. BitBucket is an alternative online
site for hosting a Git server. It also possible to setup a Git server locally as well.

# Installing on Linux and Mac OS X

I have been able to install both chartpy and finmarketpy both Linux and Mac OS X, using the Anaconda distribution
for both platforms.

However, with findatapy, I would note that following:
* Bloomberg Terminal software is only available for windows, so Bloomberg Desktop API (DAPI) is not available for either Linux or Mac OS X,
blpapi needs the Bloomberg Terminal software to communicate with
* However, it should be possible to install Bloomberg Server API (SAPI) which allows blpapi to communicate with it, but you need
a different Bloomberg server licence to run that
* To install arctic on Mac OS X, read [this useful thread](https://github.com/manahl/arctic/issues/14), which gives suggestions
on ways of solving issues when installing arctic on Mac OS X, in particular around the C compiler

* Even if you cannot install blpapi and arctic, findatapy will still install and largely function, but you won't be able
to make Bloomberg calls or calls via arctic to MongoDB

# Installation additional notes - conda environments (courtesy of Tahsin Alam)

*   To install findatapy into a conda environment separate from root, you will need to create that environment with pip (rather than create the environment and then install pip into it). So, do:
    ```
    conda create -n cuemacro python=3.6 pip
    INSTEAD OF
    conda create -n cuemacro python=3.6
    ```

    This will ensure that pip installs any packages in this environment's site-packages folder rather than in the global site-packages folder. (This currently appears to be a known issue with conda - see https://github.com/ContinuumIO/anaconda-issues/issues/1429).

*   You can now activate the new conda environment and run pip install on findatapy:

    ```
    activate cuemacro
    pip install git+https://github.com/cuemacro/findatapy.git
    ```

    This will install findatapy into the conda environment's site-packages folder.

*   Above works fine for environments where you are planning to use findatapy. But for an environment if you plan to work on findatapy code itself, you might prefer to set it up a bit differently.
This will keep code you are working on separate from the site-packages directory. So, instead of running pip install on findatapy, run conda install (or pip install since some of the packages don't appear to be available on conda) on each of the packages listed in findatapy's setup.py:

    ```
    conda create -n devcuemacro python=3.6 pip
    activate devcuemacro
    pip install pandas twython pytz requests numpy pandas_datareader quandl statsmodels multiprocess ...
    ```

    I then separately clone the findatapy repository and add its location to my PYTHONPATH

*   If we wish to install an conda instance in our environment (which will install lots of libraries like pandas) we can instead run

    ```
    conda create -n devcuemacro python=3.6 anaconda
    ```