# https://pypi.org/project/prophet/
import pandas as pd
from prophet import Prophet
import matplotlib.pyplot as plt
from functions import weather_forecast
import sqlite3

### Goal: "Days until stock-out" prediction per item. ###

# reading in all data
weather = weather_forecast.copy()
conn = sqlite3.connect("data/inventory.db")
inventory = pd.read_sql("SELECT * FROM inventory", conn)

# double-checking for missingness
print(weather.isna().sum())
print(inventory.isna().sum())

# making sure both date columns are date type and named appropraitely
inventory["ds"] = pd.to_datetime(inventory["record_date"])
weather["ds"] = pd.to_datetime(weather["time"])

df = inventory.merge(weather, on="ds", how="inner")
print(df.isna().sum())

df.rename(columns={"quantity": "y"}, inplace=True)

# ref https://facebook.github.io/prophet/docs/seasonality,_holiday_effects,_and_regressors.html#coefficients-of-additional-regressors
# ref https://nbviewer.org/github/nicolasfauchereau/Auckland_Cycling/blob/master/notebooks/Auckland_cycling_and_weather.ipynb
# Claude prompted as well

# other regressors
regressors = ["temp_max", "rain_sum", "snowfall_sum", "precipitation_sum"]

# --- add weather as regressors ---
for col in ["temp_max", "rain_sum", "snowfall_sum", "precipitation_sum"]:
    df[col] = df[col].values

print(df.columns.tolist())

m = Prophet(
    yearly_seasonality=False,
    weekly_seasonality=True,
    daily_seasonality=False, # apparently you need "very granular data" for this ref https://medium.com/@pysquad/prophet-for-predictive-analytics-a-comprehensive-guide-using-python-1d2297df7e85
)

# adding regressors
m.add_regressor("temp_max")
m.add_regressor("rain_sum")
m.add_regressor("snowfall_sum")
m.add_regressor("precipitation_sum")

# fitting model
m.fit(df)

# predicting
future = m.make_future_dataframe(periods = 30, freq="D")

# Combine historical weather + forecast weather
all_weather = pd.concat([
    weather[["ds", "temp_max", "rain_sum", "snowfall_sum", "precipitation_sum"]],
    weather_forecast[["ds", "temp_max", "rain_sum", "snowfall_sum", "precipitation_sum"]]]).drop_duplicates(subset="ds")

future = future.merge(all_weather, on="ds", how="left")

# Only dates beyond the 16-day forecast window need imputation
for col in regressors:
    future[col] = future[col].fillna(df[col].mean())

forecast = m.predict(future)

print(forecast)