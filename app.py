# ref https://facebook.github.io/prophet/docs/seasonality,_holiday_effects,_and_regressors.html#coefficients-of-additional-regressors
# ref https://nbviewer.org/github/nicolasfauchereau/Auckland_Cycling/blob/master/notebooks/Auckland_cycling_and_weather.ipynb
# Claude prompted as well, in Claude_artifacts document

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from functions import (geocode_location, get_weather_forecast,
                       get_weather_historical, forecast_product, days_until_stockout)
from forecast_inventory import load_data, get_connection

# ── Theme ─────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Retail Inventory Twin", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,400;0,600;1,400&display=swap');

/* Global */
html, body, [class*="css"] {
    font-family: 'Crimson Pro', Cambria, Georgia, serif !important;
    background-color: #E9D2C0 !important;
    color: #033860 !important;
}

/* Main app background */
.stApp {
    background-color: #E9D2C0 !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #5C9EAD !important;
}
[data-testid="stSidebar"] * {
    color: #E9D2C0 !important;
    font-family: 'Crimson Pro', Cambria, Georgia, serif !important;
}
[data-testid="stSidebar"] input {
    background-color: #4a8a99 !important;
    border: 1px solid #E9D2C0 !important;
    color: #E9D2C0 !important;
}

/* Buttons */
.stButton > button {
    background-color: #5D3A00 !important;
    color: #E9D2C0 !important;
    border: none !important;
    font-family: 'Crimson Pro', Cambria, Georgia, serif !important;
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
    padding: 0.5rem 1.8rem !important;
    transition: opacity 0.2s ease !important;
}
.stButton > button:hover {
    opacity: 0.85 !important;
}
.stButton > button:disabled {
    opacity: 0.4 !important;
}

/* Slider */
[data-testid="stSlider"] > div > div > div {
    background-color: #5D3A00 !important;
}
[data-testid="stSlider"] label {
    color: #033860 !important;
    font-family: 'Crimson Pro', Cambria, Georgia, serif !important;
}
.stSlider [data-baseweb="slider"] [data-testid="stTickBar"] {
    color: #033860 !important;
}

/* Selectbox - target the inner div and input */
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    background-color: #dfc3ae !important;
    border-color: #5D3A00 !important;
    color: #033860 !important;
    font-family: 'Crimson Pro', Cambria, Georgia, serif !important;
}

/* Selectbox dropdown menu */
[data-baseweb="popover"] * {
    background-color: #dfc3ae !important;
    color: #033860 !important;
    font-family: 'Crimson Pro', Cambria, Georgia, serif !important;
}

/* File uploader box */
[data-testid="stFileUploader"] section {
    background-color: #dfc3ae !important;
    border: 2px dashed #5D3A00 !important;
    color: #033860 !important;
    font-family: 'Crimson Pro', Cambria, Georgia, serif !important;
}

/* Text inputs (city field etc.) */
[data-baseweb="input"] input, [data-baseweb="input"] {
    background-color: #dfc3ae !important;
    color: #033860 !important;
    font-family: 'Crimson Pro', Cambria, Georgia, serif !important;
    border-color: #5D3A00 !important;
}

/* Headings */
h1, h2, h3, h4 {
    font-family: 'Crimson Pro', Cambria, Georgia, serif !important;
    color: #033860 !important;
}
h1 { font-size: 2.4rem !important; font-weight: 600 !important; }
h2 { font-size: 1.8rem !important; }

/* Step indicator */
.step-indicator {
    display: flex;
    gap: 0;
    margin-bottom: 2rem;
    border-radius: 8px;
    overflow: hidden;
    border: 1.5px solid #5D3A00;
}
.step {
    flex: 1;
    text-align: center;
    padding: 0.55rem 0.5rem;
    font-family: 'Crimson Pro', Cambria, Georgia, serif;
    font-size: 0.95rem;
    font-weight: 600;
    background-color: #dfc3ae;
    color: #5D3A00;
    border-right: 1px solid #5D3A00;
}
.step:last-child { border-right: none; }
.step.active {
    background-color: #5D3A00;
    color: #E9D2C0;
}
.step.done {
    background-color: #a0794a;
    color: #E9D2C0;
}

/* Metric cards */
[data-testid="stMetric"] {
    background-color: #dfc3ae !important;
    border: 1px solid #5D3A00 !important;
    border-radius: 8px !important;
    padding: 0.8rem !important;
}

/* Divider */
hr { border-color: #5D3A00 !important; opacity: 0.3; }

/* Success / warning / error */
[data-testid="stAlert"] {
    font-family: 'Crimson Pro', Cambria, Georgia, serif !important;
}
</style>
""", unsafe_allow_html=True)

# ── Session state defaults ────────────────────────────────────────────────────
if "step" not in st.session_state:
    st.session_state.step = 1
if "raw" not in st.session_state:
    st.session_state.raw = None
if "results" not in st.session_state:
    st.session_state.results = None
if "products" not in st.session_state:
    st.session_state.products = None

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.header("Location")
city = st.sidebar.text_input("Your city (do not include state)", value="Palo Alto")
lat, lon = None, None
if city:
    lat, lon = geocode_location(city)
    if lat:
        st.sidebar.caption(f"Location {lat:.4f}, {lon:.4f}")
    else:
        st.sidebar.error("City not found")

# UI
st.title("Retail Inventory Twin")

# ── Step indicator ────────────────────────────────────────────────────────────
step = st.session_state.step
labels = ["1 · Upload", "2 · Map Columns", "3 · Forecast"]

def step_class(i):
    if i + 1 < step:  return "step done"
    if i + 1 == step: return "step active"
    return "step"

indicator_html = '<div class="step-indicator">' + "".join(
    f'<div class="{step_class(i)}">{l}</div>' for i, l in enumerate(labels)
) + "</div>"
st.markdown(indicator_html, unsafe_allow_html=True)

# ── STEP 1: Upload ────────────────────────────────────────────────────────────
if step == 1:
    st.header("Upload your sales data")
    st.caption("Provide a CSV with at least 3 months of sales history.")
    uploaded = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded:
        st.session_state.raw = pd.read_csv(uploaded)
        st.write("**Preview:**", st.session_state.raw.head())

    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("Next", disabled=(st.session_state.raw is None)):
            st.session_state.step = 2
            st.rerun()

# Map columns
elif step == 2:
    st.header("Map your columns")
    st.caption("Tell us which columns contain the product type, date, and quantity sold.")
    raw = st.session_state.raw
    cols = raw.columns.tolist()

    col_product  = st.selectbox("Product Type column",    cols)
    col_date     = st.selectbox("Date column",          cols)
    col_quantity = st.selectbox("Quantity sold column", cols)

    col1, col2, col3 = st.columns([1, 5, 1])
    with col1:
        if st.button("Back"):
            st.session_state.step = 1
            st.rerun()
    with col3:
        if st.button("Next"):
            mapped = raw[[col_product, col_date, col_quantity]].copy()
            mapped.columns = ["product_id", "transaction_date", "quantity"]
            conn = get_connection()
            mapped.to_sql("Sales", conn, if_exists="append", index=False)
            load_data.clear()
            st.session_state.col_mapping = (col_product, col_date, col_quantity)
            st.session_state.loaded_rows = len(mapped)
            st.session_state.step = 3
            st.rerun()

    st.divider()
    if st.button("Reset sales database"):
        conn = get_connection()
        conn.execute("DELETE FROM Sales")
        conn.commit()
        load_data.clear()
        st.warning("Sales table cleared.")

elif step == 3:
    st.header("Forecast & Results")
    st.caption("Weather data will be fetched for your location and Prophet will model each product.")
    if "loaded_rows" in st.session_state:
        st.success(f"{st.session_state.loaded_rows} rows loaded into database.")

    col1, col2, col3 = st.columns([1, 5, 1])
    with col1:
        if st.button("Back"):
            st.session_state.results = None
            st.session_state.step = 2
            st.rerun()
    with col3:
        forecast_clicked = st.button("Run Forecast", disabled=(lat is None))

    if lat is None:
        st.info("Please enter a valid city in the sidebar before forecasting.")

    if forecast_clicked:
        with st.spinner("Fetching weather & running Prophet…"):
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
                        "stock": cur_stock,
                    }
            st.session_state.results  = results
            st.session_state.products = products

    # ── Results appear on the same page once forecast is run ──
    results  = st.session_state.results
    products = st.session_state.products

    if results is not None:
        if not results:
            st.warning("No products could be forecast.")
            sales, stock, _ = load_data()
            st.write(f"Sales rows in DB: {len(sales)}")
            st.write(f"Stock rows in DB: {len(stock)}")
            if len(sales) > 0:
                st.write("Sales sample:", sales.head())
                weather_hist = get_weather_historical(lat, lon, sales)
                st.write(f"Weather hist rows: {len(weather_hist)}, "
                         f"range: {weather_hist['ds'].min()} → {weather_hist['ds'].max()}")
                st.write(f"Sales date range: {sales['ds'].min()} → {sales['ds'].max()}")
        else:
            st.divider()
            st.subheader("Detailed forecast by product")
            pid_options = list(results.keys())
            selected = st.selectbox("Select product",
                                    pid_options,
                                    format_func=lambda p: products.loc[
                                        products.product_id == p, "product_name"].values[0] if p in products.product_id.values else str(p))
            current_stock = st.number_input(
                "Enter current stock on hand",
                min_value=0,
                value=results[selected]["stock"],
                step=1)

            days_out = days_until_stockout(results[selected]["forecast"], current_stock)

            if current_stock <= 0:
                st.error("You are already out of stock!")
            elif days_out is None:
                st.success("At current forecast levels, this stock will last beyond the forecast window (30+ days).")
            else:
                st.warning(
                    f"At **{current_stock}** units on hand, estimated stockout in **{days_out} days** "
                    f"({(pd.Timestamp.today() + pd.Timedelta(days=days_out)).strftime('%B %d, %Y')}).")

            fc = results[selected]["forecast"]

            # ── Average daily sales (historical) ──
            st.subheader("Average daily sales")
            sales_data, _, _ = load_data()
            product_sales = sales_data[sales_data["product_id"] == selected].copy()
            product_sales["ds"] = pd.to_datetime(product_sales["ds"])
            daily_avg = product_sales.groupby("ds")["y"].sum().reset_index()
            daily_avg.columns = ["Date", "Units Sold"]

            fig_daily = px.bar(daily_avg, x="Date", y="Units Sold",
                               title="Daily sales history",
                               color_discrete_sequence=["#033860"])
            fig_daily.update_layout(paper_bgcolor="#E9D2C0", plot_bgcolor="#E9D2C0",
                                    font=dict(family="Crimson Pro, Cambria, Georgia, serif", color="#033860"))
            fig_daily.update_yaxes(rangemode="nonnegative")
            st.plotly_chart(fig_daily, use_container_width=True)

            # ── Average monthly sales (historical) ──
            st.subheader("Average monthly sales")
            product_sales["month"] = product_sales["ds"].dt.to_period("M").dt.to_timestamp()
            monthly_avg = product_sales.groupby("month")["y"].sum().reset_index()
            monthly_avg.columns = ["Month", "Units Sold"]

            fig_monthly = px.bar(monthly_avg, x="Month", y="Units Sold",
                                 title="Monthly sales history",
                                 color_discrete_sequence=["#5C9EAD"])
            fig_monthly.update_layout(paper_bgcolor="#E9D2C0", plot_bgcolor="#E9D2C0",
                                      font=dict(family="Crimson Pro, Cambria, Georgia, serif", color="#033860"))
            fig_monthly.update_yaxes(rangemode="nonnegative")
            st.plotly_chart(fig_monthly, use_container_width=True)

            # ── 30-day forecast ──
            st.subheader("30-day forecast")
            fc_plot = fc.copy()
            fc_plot["yhat"] = fc_plot["yhat"].clip(lower=0)
            fc_plot["yhat_upper"] = fc_plot["yhat_upper"].clip(lower=0)
            fc_plot["yhat_lower"] = fc_plot["yhat_lower"].clip(lower=0)

            fig_fc = px.line(fc_plot, x="ds", y="yhat",
                             labels={"ds": "Date", "yhat": "Predicted units sold"},
                             title="Predicted units sold",
                             color_discrete_sequence=["#033860"])
            fig_fc.add_scatter(x=fc_plot["ds"], y=fc_plot["yhat_upper"], mode="lines",
                               line=dict(dash="dot", color="#5C9EAD"), name="Upper bound")
            fig_fc.add_scatter(x=fc_plot["ds"], y=fc_plot["yhat_lower"], mode="lines",
                               line=dict(dash="dot", color="#5C9EAD"), name="Lower bound")
            fig_fc.update_layout(paper_bgcolor="#E9D2C0", plot_bgcolor="#E9D2C0",
                                 font=dict(family="Crimson Pro, Cambria, Georgia, serif", color="#033860"))
            fig_fc.update_yaxes(rangemode="nonnegative")
            st.plotly_chart(fig_fc, use_container_width=True)