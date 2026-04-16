# ref https://facebook.github.io/prophet/docs/seasonality,_holiday_effects,_and_regressors.html#coefficients-of-additional-regressors
# ref https://nbviewer.org/github/nicolasfauchereau/Auckland_Cycling/blob/master/notebooks/Auckland_cycling_and_weather.ipynb
# Claude prompted as well

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from functions import (geocode_location, get_weather_forecast,
                       get_weather_historical, forecast_product, days_until_stockout)
from forecast_inventory import load_data, get_connection

# Headers
st.title("Retail Inventory Twin")
st.subheader("To examine your predicted stock as relating to the weather forecast, please submit 3 months of sales data below")

# Sidebar
st.sidebar.header("Input Location")
city = st.sidebar.text_input("Your city", value="Palo Alto")
lat, lon = None, None
if city:
    lat, lon = geocode_location(city)
    if lat:
        st.sidebar.caption(f"You are at {lat:.4f}, {lon:.4f}")
    else:
        st.sidebar.error("City not found, try a different name or find the city nearest to you with a valid Meteostat weather station")

# sales upload via file
st.header("Upload your sales data")
uploaded = st.file_uploader("CSV with at least 3 months of sales", type="csv")

if uploaded:
    raw = pd.read_csv(uploaded)
    st.write("Preview:", raw.head())
    cols = raw.columns.tolist()

    st.subheader("Map your columns")
    col_product  = st.selectbox("Product ID column",       cols)
    col_date     = st.selectbox("Date column",             cols)
    col_quantity = st.selectbox("Quantity sold column",    cols)

    if st.button("Load into database"):
        mapped = raw[[col_product, col_date, col_quantity]].copy()
        mapped.columns = ["product_id", "transaction_date", "quantity"]
        conn = get_connection()
        mapped.to_sql("Sales", conn, if_exists="append", index=False)
        load_data.clear()
        st.success(f"Loaded {len(mapped)} rows")

    if st.button("Reset sales data"):
        conn = get_connection()
        conn.execute("DELETE FROM Sales")
        conn.commit()
        load_data.clear()
        st.warning("Sales table cleared")

# trigger forecast
st.header("Then you are ready! Click here to forecast your sales")

if st.button("Forecast", disabled=(lat is None)):
    with st.spinner("Fetching weather & running Prophet..."):
        sales, stock, products = load_data()
        weather_hist   = get_weather_historical(lat, lon, sales)
        weather_future = get_weather_forecast(lat, lon)

        results = {}
        for pid, group in sales.groupby("product_id"):
            _, fc = forecast_product(group, weather_hist, weather_future)
            if fc is not None:
                cur_stock_rows = stock.loc[stock.product_id == pid, "quantity"]
                cur_stock = int(cur_stock_rows.values[0]) if len(cur_stock_rows) else 0
                results[pid] = {
                    "forecast": fc,
                    "days": days_until_stockout(fc, cur_stock),
                    "stock": cur_stock
                }
        st.session_state["results"]  = results
        st.session_state["products"] = products
    st.success("Success")

 # DASHBOARD
if "results" in st.session_state:
    st.header("3. Results")
    results  = st.session_state["results"]
    products = st.session_state["products"]

    if not results:
        st.warning("No products could be forecast. Adding debug info below:")
        sales, stock, products = load_data()
        st.write(f"Sales rows in DB: {len(sales)}")
        st.write(f"Stock rows in DB: {len(stock)}")
        if len(sales) > 0:
            st.write("Sales sample:", sales.head())
            weather_hist = get_weather_historical(lat, lon)
            st.write(f"Weather hist rows: {len(weather_hist)}, range: {weather_hist['ds'].min()} to {weather_hist['ds'].max()}")
            st.write(f"Sales date range: {sales['ds'].min()} to {sales['ds'].max()}")
    else:
        # Customizable threshold
        threshold = st.slider("Show products running out within (days)", min_value=1, max_value=90, value=14)

        # Filter to only products within threshold
        urgent = {pid: data for pid, data in results.items() if data["days"] and data["days"] <= threshold}

        if not urgent:
            st.success(f"No products running out within {threshold} days!")
        else:
            st.warning(f"{len(urgent)} product(s) need ordering within {threshold} days:")

            # Clean list of urgent products
            for pid, data in urgent.items():
                name_row = products.loc[products.product_id == pid, "product_name"]
                label = name_row.values[0] if len(name_row) else f"Product {pid}"
                st.write(f"**{label}** — {data['days']} days until stockout ({data['stock']} in stock)")

        # Detailed view for any product
        st.divider()
        st.subheader("Detailed forecast by product")
        pid_options = list(results.keys())
        selected = st.selectbox(
            "Select product",
            pid_options,
            format_func=lambda p: products.loc[
                products.product_id == p, "product_name"
            ].values[0] if p in products.product_id.values else str(p)
        )
        fc = results[selected]["forecast"]
        fig = px.line(fc, x="ds", y="yhat",
                      labels={"ds": "Date", "yhat": "Predicted units sold"},
                      title="30-day forecast")
        fig.add_scatter(x=fc["ds"], y=fc["yhat_upper"], mode="lines",
                        line=dict(dash="dot", color="lightblue"), name="Upper bound")
        fig.add_scatter(x=fc["ds"], y=fc["yhat_lower"], mode="lines",
                        line=dict(dash="dot", color="lightblue"), name="Lower bound")
        st.plotly_chart(fig, use_container_width=True)
