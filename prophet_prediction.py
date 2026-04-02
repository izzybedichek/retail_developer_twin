# https://pypi.org/project/prophet/
import pandas as pd

from prophet import Prophet

### Goal: "Days until stock-out" prediction per item. ###

# reading in all data
weather = pd.read_csv("data/palo_alto_weather.csv")
inventory = pd.read_csv("data/inventory.csv")

# making sure both date columns are the same type
inventory["date"] = pd.to_datetime(inventory["record_date"])
weather["date"] = pd.to_datetime(weather["time"])

df = inventory.merge(weather, on="date", how='left')

print(df.head())
