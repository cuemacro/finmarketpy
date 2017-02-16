from setuptools import setup, find_packages

setup(name='finmarketpy',
      version='0.11',
      description='Trading Backtest library',
      author='Saeed Amen',
      author_email='saeed@cuemacro.com',
      license='Apache 2.0',
      keywords = ['trading', 'markets', 'currencies', 'pandas', 'data', 'Bloomberg', 'tick', 'stocks', 'equities'],
      url = 'https://github.com/cuemacro/finmarketpy',
      packages = find_packages(),
      include_package_data = True,
      install_requires = ['pandas',
                          'twython',
                          'pytz',
                          'requests',
                          'numpy',
                          'multiprocess'],
	  zip_safe=False)