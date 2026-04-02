# https://pypi.org/project/prophet/
import pandas as pd
from prophet import Prophet

### Goal: "Days until stock-out" prediction per item. ###

# reading in all data
weather = pd.read_csv("data/palo_alto_weather.csv")
inventory = pd.read_csv("data/inventory.csv")

# making sure both date columns are date type and named appropraitely
inventory["record_date"] = pd.to_datetime(inventory["record_date"])
weather["time"] = pd.to_datetime(weather["time"])
inventory.rename(columns={"record_date": "DS"}, inplace=True)
weather.rename(columns={"time": "DS"}, inplace=True)

df = inventory.merge(weather, on="DS", how="left")

df.rename(columns={"quantity": "Y"}, inplace=True)

print(df.head())

# ref https://facebook.github.io/prophet/docs/seasonality,_holiday_effects,_and_regressors.html#coefficients-of-additional-regressors
# ref https://nbviewer.org/github/nicolasfauchereau/Auckland_Cycling/blob/master/notebooks/Auckland_cycling_and_weather.ipynb
#m = Prophet(df, daily_seasonality= True)
