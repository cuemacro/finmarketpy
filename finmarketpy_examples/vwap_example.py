__author__ = 'mhockenberger'


import pandas as pd

from chartpy import Chart, Style
from finmarketpy.economics import TechIndicator, TechParams

from findatapy.util.loggermanager import LoggerManager


logger = LoggerManager().getLogger(__name__)

chart = Chart(engine='matplotlib')

tech_ind = TechIndicator()

# Load data from local file
df = pd.read_csv("/Volumes/Data/s&p500.csv", index_col=0, parse_dates=['Date'],
                 date_parser=lambda x: pd.datetime.strptime(x, '%Y-%m-%d'))

# Calculate Volume Weighted Average Price (VWAP)
tech_params = TechParams()
tech_ind.create_tech_ind(df, 'VWAP', tech_params)

df = tech_ind.get_techind()

print(df)
