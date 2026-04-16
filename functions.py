import requests
import pandas as pd
from prophet import Prophet
from datetime import date, timedelta
import streamlit as st

REGRESSORS = ["temp_max", "rain_sum", "snowfall_sum", "precipitation_sum"]

def geocode_location(city_name):
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city_name, "count": 1, "language": "en", "format": "json"}
    data = requests.get(url, params=params).json()
    if not data.get("results"):
        return None, None
    result = data["results"][0]
    return result["latitude"], result["longitude"]

@st.cache_data
def get_weather_forecast(lat, lon, days=16):
    """Future weather — Open-Meteo forecast API, up to 16 days ahead."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ["temperature_2m_max", "rain_sum", "snowfall_sum", "precipitation_sum"],
        "forecast_days": days,
        "timezone": "auto"
    }
    df = pd.DataFrame(requests.get(url, params=params).json()["daily"])
    df["ds"] = pd.to_datetime(df["time"])
    return df.rename(columns={"temperature_2m_max": "temp_max"}).drop(columns=["time"])

@st.cache_data
def get_weather_historical(lat, lon, df):
    """Historical weather from Open-Meteo archive API, for days overlapping with sales data given"""
    start = df["ds"].min().date()
    end = df["ds"].max().date()
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ["temperature_2m_max", "rain_sum", "snowfall_sum", "precipitation_sum"],
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "timezone": "auto"
    }
    df = pd.DataFrame(requests.get(url, params=params).json()["daily"])
    df["ds"] = pd.to_datetime(df["time"])
    return df.rename(columns={"temperature_2m_max": "temp_max"}).drop(columns=["time"])


def forecast_product(product_df, weather_hist, weather_future, periods=30):
    """Takes sales rows for ONE product, returns (model, forecast_df)."""

    # trim sales to dates we actually have weather for
    valid_dates = weather_hist["ds"]
    product_df = product_df[product_df["ds"].isin(valid_dates)]

    if len(product_df) < 2:
        return None, None

    m = Prophet(weekly_seasonality=True, yearly_seasonality=False, daily_seasonality=False)
    for col in REGRESSORS:
        m.add_regressor(col)

    df = product_df.merge(weather_hist[["ds"] + REGRESSORS], on="ds", how="inner")
    if len(df) < 2:
        return None, None
    m.fit(df)

    # future weather data is used for future dates
    future = m.make_future_dataframe(periods=periods, freq="D")
    future = future.merge(weather_future[["ds"] + REGRESSORS], on="ds", how="left")
    for col in REGRESSORS:
        future[col] = future[col].fillna(df[col].mean())

    # Build a future dataframe starting from TODAY, not from end of training data
    today = pd.Timestamp.today().normalize()
    future_dates = pd.DataFrame({"ds": pd.date_range(start=today, periods=periods, freq="D")})
    future_dates = future_dates.merge(weather_future[["ds"] + REGRESSORS], on="ds", how="left")
    for col in REGRESSORS:
        future_dates[col] = future_dates[col].fillna(df[col].mean())

    fc = m.predict(future_dates)
    return m, fc

def days_until_stockout(forecast_df, current_stock):
    if current_stock <= 0:
        return 0
    future = forecast_df.copy()
    future["cumulative"] = future["yhat"].clip(lower=0).cumsum()
    hit = future[future["cumulative"] >= current_stock]
    if hit.empty:
        return None
    days = int((hit["ds"].iloc[0] - future["ds"].iloc[0]).days)
    return days