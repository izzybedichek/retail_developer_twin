# https://pypi.org/project/prophet/
import pandas as pd
from prophet import Prophet

### Goal: "Days until stock-out" prediction per item. ###

# reading in all data
weather = pd.read_csv("data/palo_alto_weather.csv")
inventory = pd.read_csv("data/inventory.csv")

# double-checking for missingness
print(weather.isna().sum())
print(inventory.isna().sum())

# making sure both date columns are date type and named appropraitely
inventory["record_date"] = pd.to_datetime(inventory["record_date"])
weather["time"] = pd.to_datetime(weather["time"])
inventory.rename(columns={"record_date": "ds"}, inplace=True)
weather.rename(columns={"time": "ds"}, inplace=True)

df = inventory.merge(weather, on="ds", how="left")

df.rename(columns={"quantity": "y"}, inplace=True)

# ref https://facebook.github.io/prophet/docs/seasonality,_holiday_effects,_and_regressors.html#coefficients-of-additional-regressors
# ref https://nbviewer.org/github/nicolasfauchereau/Auckland_Cycling/blob/master/notebooks/Auckland_cycling_and_weather.ipynb
# Claude prompted as well

# Prophet requires columns named exactly "ds" and "y"
prophet_df = df.reset_index()[["ds", "y"]]
print(prophet_df)

# --- add weather as regressors ---
for col in ["temp_max", "rain_sum", "snowfall_sum", "precipitation_sum"]:
    prophet_df[col] = df[col].values

print(prophet_df.columns.tolist())

m = Prophet(
    yearly_seasonality=False,
    weekly_seasonality=True,
    daily_seasonality=False, # apparently you need "very granular data" for this ref https://medium.com/@pysquad/prophet-for-predictive-analytics-a-comprehensive-guide-using-python-1d2297df7e85
)

# adding regressors
m.add_regressor("temp_max")
m.add_regressor("precipitation_sum")
m.add_regressor("rain_sum")
m.add_regressor("snowfall_sum")

# fitting model
m.fit(prophet_df)

# predicting
future = m.make_future_dataframe(periods = 30, freq='1D')

print(future)