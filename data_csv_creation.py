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
records = []
tid = 1

for i, date in enumerate(dates):
    is_weekend = date.dayofweek >= 5
    weekend_bump = 1.3 if is_weekend else 1.0

    # Sales per product
    sales_rates = {
        1: 18 * weekend_bump,   # Coffee Beans
        2: 8 * weekend_bump,    # Green Tea
        3: 12 * weekend_bump,   # Hot Chocolate
    }

    for pid, rate in sales_rates.items():
        qty = max(1, int(np.random.poisson(rate)))
        records.append({
            'transaction_id': tid,
            'product_id': pid,
            'transaction_date': date.date(),
            'quantity': qty
        })
        tid += 1

sales = pd.DataFrame(records)

# --- INVENTORY ---
# Calculate current stock per product from transactions
inventory_records = []
for pid in [1, 2, 3]:
    prod_tx = sales[sales['product_id'] == pid]
    purchased = prod_tx[prod_tx['transaction_type'] == 'purchase']['quantity'].sum()
    sold = prod_tx[prod_tx['transaction_type'] == 'sale']['quantity'].sum()
    current_stock = purchased - sold
    supplier_id = 1 if pid == 1 else 2
    inventory_records.append({
        'inventory_id': pid,
        'product_id': pid,
        'quantity': max(0, current_stock),
        'supplier_id': supplier_id,
        'last_updated': dates[-1].date()
    })

inventory = pd.DataFrame(inventory_records)

# --- SAVE ---
products.to_csv('products.csv', index=False)
transactions.to_csv('sales.csv', index=False)
inventory.to_csv('inventory.csv', index=False)

print("CSVs saved.")
print("\nInventory snapshot:")
for _, row in inventory.iterrows():
    name = products[products['product_id'] == row['product_id']]['product_name'].values[0]
    print(f"  {name}: {row['quantity']} units remaining")

print(f"\nTransactions: {len(transactions)} rows")
print(f"Date range: {dates[0].date()} to {dates[-1].date()}")