import requests
import pandas as pd
from prophet import Prophet

def days_until_stockout(product_id, forecast_df, stock_df):
    current_stock = stock_df.loc[stock_df.product_id == product_id, "quantity"].values[0]
    future = forecast_df[forecast_df["ds"] > pd.Timestamp.today()].copy()
    future["cumulative"] = future["yhat"].clip(lower=0).cumsum()
    stockout_row = future[future["cumulative"] >= current_stock]
    if stockout_row.empty:
        return None  # won't stock out within forecast window
    return (stockout_row["ds"].iloc[0] - pd.Timestamp.today()).days

def forecast_product(product_df, weather_historical, weather_future, periods=30):
    """Takes sales rows for ONE product, returns forecast df."""
    m = Prophet(weekly_seasonality=True, yearly_seasonality=False, daily_seasonality=False)
    for col in ["temp_max", "rain_sum", "snowfall_sum", "precipitation_sum"]:
        m.add_regressor(col)

    df = product_df.merge(weather_historical, on="ds", how="inner")
    m.fit(df)

    future = m.make_future_dataframe(periods=periods, freq='D')
    future = future.merge(weather_future, on="ds", how="left")
    for col in ["temp_max", "rain_sum", "snowfall_sum", "precipitation_sum"]:
        future[col] = future[col].fillna(df[col].mean())

    return m.predict(future)

def get_weather_forecast(days=30):
    # Palo Alto coordinates
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 37.4419,
        "longitude": -122.1430,
        "daily": [
            "temperature_2m_max",
            "rain_sum",
            "snowfall_sum",
            "precipitation_sum"
        ],
        "forecast_days": 16,  # max is 16 days
        "timezone": "America/Los_Angeles"
    }
    response = requests.get(url, params=params)
    data = response.json()

    df = pd.DataFrame(data["daily"])
    df["ds"] = pd.to_datetime(df["time"])
    df = df.rename(columns={"temperature_2m_max": "temp_max"})
    df = df.drop(columns=["time"])
    return df

weather_forecast = get_weather_forecast()