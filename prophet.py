# https://pypi.org/project/prophet/
import pandas as pd

from data_csv_creation import transactions
from prophet import Prophet

### Goal: "Days until stock-out" prediction per item. ###

# reading in all data
weather = pd.read_csv("data/palo_alto_weather.csv")
inventory = pd.read_csv("data/inventory.csv")
transactions = pd.read_csv("data/transactions.csv")

# merging data
