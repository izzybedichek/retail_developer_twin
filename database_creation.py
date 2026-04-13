import sqlite3
import os

# wipe existing database
if os.path.exists("data/inventory.db"):
    os.remove("data/inventory.db")

# ref https://sqldocs.org/sqlite-create-database/, https://docs.python.org/3/library/sqlite3.html
connection = sqlite3.connect("data/inventory.db")

# needed to execute queries
cur = connection.cursor()

cur.execute("PRAGMA foreign_keys = ON;")

cur.execute("CREATE TABLE Products ("
            "product_id   INT PRIMARY KEY,"
            "product_name VARCHAR(255) NOT NULL,"
            "price        DECIMAL(10, 2) NOT NULL,"
            "category     VARCHAR(100));")

cur.execute("CREATE TABLE Inventory ("
        "record_id   INT PRIMARY KEY,"
        "product_id  INT,"
        "record_date DATE NOT NULL DEFAULT (CURRENT_DATE),"
        "quantity    INT DEFAULT 0,"
        "FOREIGN KEY (product_id) REFERENCES Products(product_id));")

cur.execute("CREATE TABLE Sales ("
        "transaction_id INTEGER PRIMARY KEY,"
        "product_id INT,"
        "transaction_date DATE NOT NULL DEFAULT (CURRENT_DATE),"
        "quantity INT NOT NULL,"
        "FOREIGN KEY (product_id) REFERENCES Products(product_id));")

connection.commit()
connection.close()