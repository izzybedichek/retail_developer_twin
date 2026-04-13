import streamlit as st
import sqlite3
import pandas as pd
from prophet_prediction import forecast

# UI
st.title("Retail Inventory Twin")
st.subheader("To examine your predicted stock as relating to the weather forecast, please submit 3 months of sales data below")

# sales upload via file
uploaded = st.file_uploader("Upload CSV of sales (at least 3 months)", type="csv")
if uploaded:
    df = pd.read_csv(uploaded)
    # expect columns: product_id, transaction_date, quantity
    conn = sqlite3.connect("data/inventory.db")
    df.to_sql("Sales", conn, if_exists="append", index=False)
    conn.close()
    st.success(f"Loaded {len(df)} rows")

# trigger forecast
if st.button("Trigger Forecast"):
    results = forecast   # returns dict of {product_id: forecast_df}
    st.session_state["results"] = results  # persist across reruns

    submitted = st.form_submit_button("Forecast Stock")
    if submitted:
        st.write(pd.Dataframe({results}))
