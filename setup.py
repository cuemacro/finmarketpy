from setuptools import setup, find_packages

long_description = """finmarketpy is a Python based library that enables you to 
analyze market data and also to backtest trading strategies using a simple to 
use API, which has prebuilt templates for you to define backtest."""

setup(name="finmarketpy",
      version="0.11.14",
      description="finmarketpy is a Python based library for backtesting trading strategies",
      author="Saeed Amen",
      author_email="saeed@cuemacro.com",
      license="Apache 2.0",
      long_description=long_description,
      keywords=["trading", "markets", "currencies", "pandas", "data",
                "Bloomberg", "tick", "stocks", "equities"],
      url="https://github.com/cuemacro/finmarketpy",
      packages=find_packages(),
      include_package_data=True,
      install_requires=["pandas",
                        "twython",
                        "pytz",
                        "requests",
                        "numpy",
                        "multiprocess",
                        "seasonal",
                        "scikit-learn",
                        "matplotlib",
                        "numba",
                        "financepy==0.310"],
      zip_safe=False)
