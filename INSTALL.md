# Installation of Cuemacro Python libraries (finmarketpy, findatapy and chartpy)

In order to install the Cuemacro Python libraries, I would recommend following the instructions below. If you already have Python 3.5 installed,
you can skip most of these steps. The below instructions assume that you have not installed Python at all and are assuming you have Windows.

In general, I would go in the order suggested here. Some components are optional (such as Bloomberg software).

Before installation of any specific Python libraries, we need to set up the core Python distribution and other programming tools,
which will help you to write your own trading strategies and Python scripts for doing market analysis on top of the Cuemacro libraries.

* Programming Tools
    * Anaconda 4.20 64 bit Python - https://www.continuum.io/downloads
        * This is the most used Python distribution for data science.
    * As well as installing the core Python libraries, it also installs many useful libraries like the SciPy stack, which
    contains NumPy, pandas etc. and many other useful libraries like matplotlib which are dependencies for the various Cuemacro libraries
        * Microsoft Visual Studio 2015 Community Edition- https://www.visualstudio.com/downloads/
    * Makes sure to do a custom installation and tick Visual C++
        * Some Python libraries need a C++ compiler in order to build (such as blpapi and arctic)
    * Git - https://git-scm.com/downloads
        * Version control software
    * Makes it easier to maintain your own Python code
        * PyCharm Community Edition - https://www.jetbrains.com/pycharm/download/
    * PyCharm is a relatively easy to use IDE for coding Python
        * The Professional Edition also adds a few bells and whistles including a code profiler

* Data tools
    * MongoDB - https://www.mongodb.com/download-center
        * IOEngine class has a wrapper over arctic to use MongoDB (as well as HDF5 files if preferred)
        * Be sure to setup a database in MongoDB, if you wish to use it to store data later
    * Bloomberg Terminal software for Windows - https://www.bloomberg.com/professional/downloads/
        * Bloomberg provides a high quality data source
        * Note, you must be a subscriber for the software to function and to have a licence for the data
        * This also needs installation of your serial number

Open up the Anaconda Command Prompt (accessible via the Start Menu) to run the various "pip" commands to install the
various Python libraries. The Cuemacro libraries will install most Python dependencies, but some need to be installed separately.

* Python libraries (open source)
    * arctic - pip install git+https://github.com/manahl/arctic.git
        * Wrapper for MongoDB
        * Allows us to easily save and load pandas DataFrames in MongoDB
        * Also compresses data contents
    * blpapi - https://www.bloomberglabs.com/api/libraries/ (both C++ and Python libraries)
        * Interact with Bloomberg programmatically via Python to download historical and live data
        * Note that this requires a C++ compiler to build the Python library
        * Follow instructions at https://www.github.com/cuemacro/findatapy/BLOOMBERG.md for all the steps necessary to install blpapi

* Cuemacro Python libraries (open source)
    * chartpy - pip install git+https://github.com/cuemacro/chartpy.git
        * Check constants file configuration findatapy/findatapy/util/dataconstants.py for
            * Adding your own API keys for Plotly, Twitter etc
            * Changing the default size of plots
            * Changing the default chart engine (eg. Plotly, Bokeh or Matplotlib)
        * Alternatively you can create chartcred.py class in the same folder to put your own API keys
        * This has the benefit of not being overwritten each time you upgrade the project
    * findatapy - pip install git+https://github.com/cuemacro/findatapy.git
        * Check constants file configuration findatapy/findatapy/util/dataconstants.py for
            * adding your own API keys for Quandl etc.
            * changing path of your local data source (folder_time_series_data)
            * changing path of the config folder if necessary (config_root_folder) so you can create your own custom
            ticker library (otherwise it will get overwritten each time you upgrade findatapy)
            * changing the ticker library (placed in findatapy/findatapy/conf/*.CSV files)
                * time_series_categories_fields.csv - define the categories of tickers and what fields they have
                * time_series_fields_list.csv - define aliases for vendor fields
                * time_series_tickers_list.csv - defines aliases for vendor tickers
                * There are already setup with a few FX tickers to act as an example
                * In addition, you can add your own CSV files to accompany time_series_tickers_list.csv
                    * fx_vol_tickers.csv - samples of FX vol tickers
                    * fx_forward_tickers.csv - samples of FX forward tickers
            * changing logging.conf
                * For customising how the project dumps logs to disk
        * Alternatively you can create datacred.py class in the same folder to put your own API keys and file folder settings
        * This has the benefit of not being overwritten each time you upgrade the project
    * finmarketpy - pip install git+https://github.com/cuemacro/finmarketpy.git
        * Check constants file configuration
        * You can also create your own file marketcred.py (placed in the same folder)

You can then setup your own project in PyCharm to create your own trading strategies on top of it. I'd recommend creating
a private (or public) project on GitHub so you can use it for version control and backup. Bitbucket is an alternative online
site for hosting a Git server. It also possible to setup a Git server locally as well.