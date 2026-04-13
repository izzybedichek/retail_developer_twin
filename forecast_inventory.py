import sqlite3
import pandas as pd
from prophet import Prophet

# connecting to database
conn = sqlite3.connect("data/inventory.db")

# Aggregate sales per product per day; Prophet 'y'
sales = pd.read_sql("""
    SELECT 
        product_id,
        transaction_date AS ds,
        SUM(quantity)    AS y
    FROM Sales
    GROUP BY product_id, transaction_date
    ORDER BY product_id, transaction_date
""", conn)

# Current stock level per product (for stockout calculation)
stock = pd.read_sql("""
    SELECT product_id, quantity
    FROM Inventory
    WHERE record_date = (
        SELECT MAX(record_date) FROM Inventory i2 
        WHERE i2.product_id = Inventory.product_id
    )
""", conn)

products = pd.read_sql("SELECT * FROM Products", conn)
conn.close()
