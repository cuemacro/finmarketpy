__author__ = 'mhockenberger'


import pandas as pd

from chartpy import Chart, Style
from finmarketpy.economics import TechIndicator, TechParams

from findatapy.util.loggermanager import LoggerManager


logger = LoggerManager().getLogger(__name__)

chart = Chart(engine='bokeh')

tech_ind = TechIndicator()
###### Simple example loading local data and using finmarketpy engine
# Load data from local file
df = pd.read_csv("/Volumes/Data/s&p500.csv", index_col=0, parse_dates=['Date'],
                 date_parser=lambda x: pd.datetime.strptime(x, '%Y-%m-%d'))

# Calculate Volume Weighted Average Price (VWAP)
tech_params = TechParams()
tech_ind.create_tech_ind(df, 'VWAP', tech_params)

df = tech_ind.get_techind()

print(df)

style = Style()
style.title = 'S&P500 VWAP'
style.scale_factor = 2

df = tech_ind.get_techind()

chart.plot(df, style=style)
