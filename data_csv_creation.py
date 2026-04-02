import pandas as pd
import numpy as np

### THE FOLLOWING CODE IS BY CLAUDE TO GENERATE RANDOM 3 MONTHS OF DATA ###
np.random.seed(42)

# --- DATE RANGE ---
dates = pd.date_range(end=pd.Timestamp.today(), periods=90, freq='D')

# --- PRODUCTS ---
products = pd.DataFrame({
    'product_id': [1, 2, 3],
    'product_name': ['Coffee Beans', 'Green Tea', 'Hot Chocolate Mix'],
    'price': [14.99, 9.99, 7.99],
    'category': ['Coffee', 'Tea', 'Chocolate']
})

# --- Sales ---
# Base daily sales per product, with weekend bump
sales_records = []
tid = 1

for date in dates:
    for pid in [1, 2, 3]:
        qty = np.random.randint(1, 30)
        sales_records.append({
            'transaction_id':   tid,
            'product_id':       pid,
            'transaction_date': date.date(),
            'quantity':         qty
        })
        tid += 1

sales = pd.DataFrame(sales_records)

# --- INVENTORY ---
# Calculate current stock per product from transactions
# seed each product with a starting stock, subtract daily sales
starting_stock = {1: 2000, 2: 2000, 3: 2000}

inventory_records = []
rid = 1

for pid in [1, 2, 3]:
    stock = starting_stock[pid]
    prod_sales = sales[sales['product_id'] == pid].set_index('transaction_date')

    for date in dates:
        sold  = prod_sales.loc[date.date(), 'quantity'] if date.date() in prod_sales.index else 0
        stock = max(0, stock - sold)
        inventory_records.append({
            'record_id':   rid,
            'product_id':  pid,
            'record_date': date.date(),
            'quantity':    stock,
        })
        rid += 1

inventory = pd.DataFrame(inventory_records)

# --- SAVE ---
products.to_csv('products.csv', index=False)
sales.to_csv('sales.csv', index=False)
inventory.to_csv('inventory.csv', index=False)


print("\nInventory snapshot:")
for _, row in inventory.iterrows():
    name = products[products['product_id'] == row['product_id']]['product_name'].values[0]
    print(f"  {name}: {row['quantity']} units remaining")

